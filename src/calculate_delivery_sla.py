
import os
from datetime import datetime

import numpy as np
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text


# --------------------------------------------------
# 1. DATABASE CONNECTION
# --------------------------------------------------

load_dotenv()

required_vars = [
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME"
]

missing_vars = [v for v in required_vars if os.getenv(v) is None]

if missing_vars:
    raise ValueError(f"Missing .env variables: {missing_vars}")

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# --------------------------------------------------
# 2. SQL QUERIES
# --------------------------------------------------

ORDER_QUERY = text("""
    SELECT
        o.order_id,
        o.order_status,
        o.purchase_timestamp,
        o.approved_timestamp,
        o.delivered_customer_timestamp,
        c.state
    FROM fact_order o
    LEFT JOIN dim_customer c
        ON o.customer_key = c.customer_key
    WHERE o.order_status = 'delivered'
""")

HOLIDAY_QUERY = text("""
    SELECT holiday_date, state
    FROM ref_holiday
""")

CREATE_RUN = text("""
    INSERT INTO pipeline_run
        (start_date, end_date, started_at, status, rows_processed)
    VALUES
        (:start_date, :end_date, NOW(), 'RUNNING', 0)
""")

UPDATE_RUN = text("""
    UPDATE pipeline_run
    SET
        completed_at = NOW(),
        status = :status,
        rows_processed = :rows_processed,
        error_message = :error_message
    WHERE run_id = :run_id
""")

UPDATE_ORDER = text("""
    UPDATE fact_order
    SET delivery_business_days = :business_days
    WHERE order_id = :order_id
""")

INSERT_DQ = text("""
    INSERT INTO data_quality_issue
    (
        rule_id,
        entity_type,
        entity_id,
        issue_type,
        details,
        run_id
    )
    SELECT
        :rule_id,
        'order',
        :entity_id,
        :issue_type,
        :details,
        :run_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM data_quality_issue
        WHERE rule_id = :rule_id
          AND entity_type = 'order'
          AND entity_id = :entity_id
          AND issue_type = :issue_type
          AND run_id = :run_id
    )
""")


# --------------------------------------------------
# 3. DATA QUALITY HELPER
# --------------------------------------------------

def add_issue(issues, run_id, rule_id, order_id, issue_type, details):
    issues.append({
        "rule_id": rule_id,
        "entity_id": str(order_id),
        "issue_type": issue_type,
        "details": details,
        "run_id": run_id
    })


# --------------------------------------------------
# 4. MAIN PIPELINE
# --------------------------------------------------

def main():

    run_id = None
    results = []
    issues = []

    try:
        # Read source data
        with engine.connect() as connection:
            orders = pd.read_sql(ORDER_QUERY, connection)
            holidays_df = pd.read_sql(HOLIDAY_QUERY, connection)

        print(f"Delivered orders fetched: {len(orders)}")

        if orders.empty:
            print("No delivered orders found.")
            return

        # Parse timestamps
        timestamp_columns = [
            "purchase_timestamp",
            "approved_timestamp",
            "delivered_customer_timestamp"
        ]

        for column in timestamp_columns:
            orders[column] = pd.to_datetime(
                orders[column],
                errors="coerce"
            )

        holidays_df["holiday_date"] = pd.to_datetime(
            holidays_df["holiday_date"],
            errors="coerce"
        )

        holidays_df = holidays_df.dropna(
            subset=["holiday_date", "state"]
        )

        # Create pipeline run
        valid_purchase_dates = orders["purchase_timestamp"].dropna()

        start_date = (
            valid_purchase_dates.min().date()
            if not valid_purchase_dates.empty else None
        )

        end_date = (
            valid_purchase_dates.max().date()
            if not valid_purchase_dates.empty else None
        )

        with engine.begin() as connection:
            result = connection.execute(
                CREATE_RUN,
                {
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            run_id = result.lastrowid

        print(f"Pipeline run started. Run ID: {run_id}")

        # --------------------------------------------------
        # 5. IDENTIFY DATA QUALITY ISSUES
        # --------------------------------------------------

        for row in orders.itertuples(index=False):

            order_id = row.order_id

            if pd.isna(row.approved_timestamp):
                add_issue(
                    issues, run_id, "R9", order_id,
                    "MISSING_APPROVAL_TIMESTAMP",
                    "Approval timestamp is missing; business days cannot be calculated."
                )

            if pd.isna(row.delivered_customer_timestamp):
                add_issue(
                    issues, run_id, "R3", order_id,
                    "MISSING_DELIVERY_TIMESTAMP",
                    "Delivered order has no customer delivery timestamp; excluded from SLA calculation."
                )

            if pd.isna(row.state):
                add_issue(
                    issues, run_id, "R9", order_id,
                    "MISSING_CUSTOMER_STATE",
                    "Customer state is missing; applicable regional holidays cannot be determined."
                )

            if (
                pd.notna(row.approved_timestamp)
                and pd.notna(row.delivered_customer_timestamp)
                and row.delivered_customer_timestamp < row.approved_timestamp
            ):
                add_issue(
                    issues, run_id, "R9", order_id,
                    "DELIVERY_BEFORE_APPROVAL",
                    "Customer delivery timestamp is earlier than approval timestamp."
                )

        # --------------------------------------------------
        # 6. PREPARE VALID ORDERS
        # --------------------------------------------------

        valid = orders[
            orders["approved_timestamp"].notna()
            & orders["delivered_customer_timestamp"].notna()
            & orders["state"].notna()
            & (
                orders["delivered_customer_timestamp"]
                >= orders["approved_timestamp"]
            )
        ].copy()

        valid["state"] = valid["state"].astype(str).str.strip().str.upper()

        valid["approval_date"] = (
            valid["approved_timestamp"].dt.normalize()
        )

        valid["delivery_date"] = (
            valid["delivered_customer_timestamp"].dt.normalize()
        )

        invalid_dates = valid[
            valid["delivery_date"] < valid["approval_date"]
        ]

        valid = valid[
            valid["delivery_date"] >= valid["approval_date"]
        ].copy()

        # --------------------------------------------------
        # 7. PREPARE HOLIDAY MAP
        # --------------------------------------------------

        holiday_map = {}

        for state in valid["state"].unique():

            applicable_holidays = holidays_df[
                holidays_df["state"].astype(str).str.upper().isin(
                    ["BR", state]
                )
            ]

            holiday_map[state] = (
                applicable_holidays["holiday_date"]
                .drop_duplicates()
                .values.astype("datetime64[D]")
            )

        # --------------------------------------------------
        # 8. CALCULATE BUSINESS DAYS
        # --------------------------------------------------

        for state, group in valid.groupby("state"):

            # Approval date excluded
            start_dates = (
                group["approval_date"].values.astype("datetime64[D]")
                + np.timedelta64(1, "D")
            )

            # Delivery date included
            end_dates = (
                group["delivery_date"].values.astype("datetime64[D]")
                + np.timedelta64(1, "D")
            )

            business_days = np.busday_count(
                start_dates,
                end_dates,
                weekmask="1111100",
                holidays=holiday_map[state]
            )

            for order_id, days in zip(
                group["order_id"],
                business_days
            ):
                results.append({
                    "order_id": order_id,
                    "business_days": int(days)
                })

        # --------------------------------------------------
        # 9. SAVE RESULTS AND DQ ISSUES
        # --------------------------------------------------

        batch_size = 2000

        with engine.begin() as connection:

            # Reset old calculated values for delivered orders.
            # This makes reruns safe.
            connection.execute(text("""
                UPDATE fact_order
                SET delivery_business_days = NULL
                WHERE order_status = 'delivered'
            """))

            # Insert DQ records
            if issues:
                connection.execute(INSERT_DQ, issues)

            # Batch update business days
            for start in range(0, len(results), batch_size):

                batch = results[start:start + batch_size]

                connection.execute(
                    UPDATE_ORDER,
                    batch
                )

                print(
                    f"Updated {min(start + batch_size, len(results))}"
                    f"/{len(results)} orders"
                )

        # --------------------------------------------------
        # 10. MARK PIPELINE SUCCESS
        # --------------------------------------------------

        with engine.begin() as connection:
            connection.execute(
                UPDATE_RUN,
                {
                    "run_id": run_id,
                    "status": "SUCCESS",
                    "rows_processed": len(results),
                    "error_message": None
                }
            )

        print("\nDelivery SLA calculation completed!")
        print(f"Run ID: {run_id}")
        print(f"Delivered orders: {len(orders)}")
        print(f"Valid calculations: {len(results)}")
        print(f"Invalid date sequences: {len(invalid_dates)}")
        print(f"DQ issues identified: {len(issues)}")
        print(f"Rows processed: {len(results)}")

    except Exception as error:

        if run_id is not None:
            with engine.begin() as connection:
                connection.execute(
                    UPDATE_RUN,
                    {
                        "run_id": run_id,
                        "status": "FAILED",
                        "rows_processed": 0,
                        "error_message": str(error)[:5000]
                    }
                )

        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
