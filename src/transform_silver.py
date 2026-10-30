
from pathlib import Path
import pandas as pd

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")

INPUT_FILE = BRONZE_DIR / "olist_orders_dataset.csv"
OUTPUT_FILE = SILVER_DIR / "olist_orders.csv"
DQ_FILE = SILVER_DIR / "orders_quality_report.csv"

TIMESTAMP_COLUMNS = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]


def transform_orders():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    # Read Bronze data. Keep original files unchanged.
    df = pd.read_csv(INPUT_FILE)

    original_rows = len(df)
    dq_issues = []

    # Standardize column names.
    df.columns = [
        column.strip().lower()
        for column in df.columns
    ]

    # Trim text values.
    for column in df.select_dtypes(include="object").columns:
        df[column] = df[column].str.strip()

    # Standardize order status.
    df["order_status"] = (
        df["order_status"]
        .str.lower()
    )

    # Convert timestamps.
    for column in TIMESTAMP_COLUMNS:
        original_non_null = df[column].notna()

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        invalid_count = int(
            (original_non_null & df[column].isna()).sum()
        )

        if invalid_count:
            dq_issues.append({
                "rule_id": "DQ_INVALID_TIMESTAMP",
                "column_name": column,
                "issue_type": "INVALID_TIMESTAMP",
                "issue_count": invalid_count,
            })

    # Identify duplicate order IDs.
    duplicate_count = int(
        df["order_id"].duplicated(keep=False).sum()
    )

    if duplicate_count:
        dq_issues.append({
            "rule_id": "DQ_DUPLICATE_ORDER",
            "column_name": "order_id",
            "issue_type": "DUPLICATE_KEY",
            "issue_count": duplicate_count,
        })

    # Record missing important timestamps.
    for column in TIMESTAMP_COLUMNS:
        missing_count = int(df[column].isna().sum())

        if missing_count:
            dq_issues.append({
                "rule_id": "DQ_MISSING_TIMESTAMP",
                "column_name": column,
                "issue_type": "MISSING_VALUE",
                "issue_count": missing_count,
            })

    # Save cleaned Silver data.
    df.to_csv(OUTPUT_FILE, index=False)

    # Save data-quality report.
    dq_df = pd.DataFrame(
        dq_issues,
        columns=[
            "rule_id",
            "column_name",
            "issue_type",
            "issue_count",
        ],
    )

    dq_df.to_csv(DQ_FILE, index=False)

    print("\nOrders transformation completed!")
    print(f"Bronze rows: {original_rows:,}")
    print(f"Silver rows: {len(df):,}")
    print(f"Duplicate order IDs: {duplicate_count:,}")
    print(f"Silver output: {OUTPUT_FILE}")
    print(f"DQ report: {DQ_FILE}")


if __name__ == "__main__":
    transform_orders()
