
from pathlib import Path
import pandas as pd

BRONZE = Path("data/bronze")
SILVER = Path("data/silver")

SILVER.mkdir(parents=True, exist_ok=True)


def clean_transaction_file(input_name, output_name, timestamp_columns=None):
    input_file = BRONZE / input_name
    output_file = SILVER / output_name

    if not input_file.exists():
        raise FileNotFoundError(input_file)

    df = pd.read_csv(input_file)

    # Standardize column names
    df.columns = [
        column.strip().lower()
        for column in df.columns
    ]

    # Trim text columns
    for column in df.select_dtypes(
        include=["object", "str"]
    ).columns:
        df[column] = df[column].str.strip()

    # Convert specified timestamps
    if timestamp_columns:
        for column in timestamp_columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    df.to_csv(output_file, index=False)

    print(f"\nDataset: {input_name}")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Output: {output_file}")


if __name__ == "__main__":

    clean_transaction_file(
        "olist_order_items_dataset.csv",
        "olist_order_items.csv",
        ["shipping_limit_date"]
    )

    clean_transaction_file(
        "olist_order_payments_dataset.csv",
        "olist_order_payments.csv"
    )

    clean_transaction_file(
        "olist_order_reviews_dataset.csv",
        "olist_order_reviews.csv",
        [
            "review_creation_date",
            "review_answer_timestamp"
        ]
    )
