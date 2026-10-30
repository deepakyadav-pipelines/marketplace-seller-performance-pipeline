
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

load_dotenv()

SILVER_DIR = Path("data/silver")
ORDERS_FILE = SILVER_DIR / "olist_orders.csv"

url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(url)


def load_orders():
    df = pd.read_csv(ORDERS_FILE)

    timestamp_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for col in timestamp_columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Load customer key mapping.
    with engine.connect() as conn:
        customers = pd.read_sql(
            text("""
                SELECT customer_id, customer_key
                FROM dim_customer
            """),
            conn,
        )

    df = df.merge(
        customers,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    unmatched = int(df["customer_key"].isna().sum())

    if unmatched:
        raise ValueError(
            f"{unmatched} orders have unmatched customers."
        )

    # Build distinct purchase dates.
    dates = (
        df["order_purchase_timestamp"]
        .dropna()
        .dt.normalize()
        .drop_duplicates()
    )

    date_records = []

    for date in dates:
        date_records.append({
            "date_key": int(date.strftime("%Y%m%d")),
            "full_date": date.date(),
            "year": date.year,
            "month": date.month,
            "day": date.day,
            "quarter": date.quarter,
            "day_of_week": date.dayofweek + 1,
            "is_weekend": date.dayofweek >= 5,
        })

    date_df = pd.DataFrame(date_records)

    # Insert dates without duplicating existing records.
    with engine.begin() as conn:
        for record in date_records:
            conn.execute(
                text("""
                    INSERT INTO dim_date (
                        date_key, full_date, year, month,
                        day, quarter, day_of_week, is_weekend
                    )
                    VALUES (
                        :date_key, :full_date, :year, :month,
                        :day, :quarter, :day_of_week, :is_weekend
                    )
                    ON DUPLICATE KEY UPDATE
                        full_date = VALUES(full_date)
                """),
                record,
            )

        # Load date key mapping.
        date_mapping = pd.read_sql(
            text("""
                SELECT full_date, date_key
                FROM dim_date
            """),
            conn,
        )

        df["purchase_date"] = (
            df["order_purchase_timestamp"].dt.date
        )

        df = df.merge(
            date_mapping,
            left_on="purchase_date",
            right_on="full_date",
            how="left",
            validate="many_to_one",
        )

        df["revenue_eligible"] = (
            df["order_status"].eq("delivered")
        )

        # Prepare fact table records.
        fact_df = df[[
            "order_id",
            "customer_key",
            "date_key",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "revenue_eligible",
        ]].copy()

        fact_df = fact_df.rename(columns={
            "date_key": "purchase_date_key",
            "order_purchase_timestamp": "purchase_timestamp",
            "order_approved_at": "approved_timestamp",
            "order_delivered_carrier_date": "delivered_carrier_timestamp",
            "order_delivered_customer_date": "delivered_customer_timestamp",
            "order_estimated_delivery_date": "estimated_delivery_timestamp",
        })

        fact_df = fact_df.where(
            pd.notna(fact_df),
            None,
        )

        # Insert using a transaction.
        fact_df.to_sql(
            "fact_order",
            con=conn,
            if_exists="append",
            index=False,
            chunksize=2000,
        )

    print("\nOrder loading completed!")
    print(f"Orders loaded: {len(fact_df):,}")
    print(f"Distinct purchase dates: {len(date_df):,}")
    print(f"Unmatched customers: {unmatched:,}")


if __name__ == "__main__":
    load_orders()
