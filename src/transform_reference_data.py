
from pathlib import Path
import pandas as pd

BRONZE = Path("data/bronze")
SILVER = Path("data/silver")

SILVER.mkdir(parents=True, exist_ok=True)


def clean_dataset(input_name, output_name, key_column):
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

    # Trim string values
    for column in df.select_dtypes(include=["object","str"]).columns:
        df[column] = df[column].str.strip()

    # Identify duplicate business keys
    duplicate_count = int(
        df[key_column].duplicated(keep=False).sum()
    )

    # Preserve first occurrence for duplicate keys.
    # Duplicates are reported for later investigation.
    df = df.drop_duplicates(
        subset=[key_column],
        keep="first"
    )

    df.to_csv(output_file, index=False)

    print(f"\nDataset: {input_name}")
    print(f"Rows after cleaning: {len(df):,}")
    print(f"Duplicate key rows detected: {duplicate_count:,}")
    print(f"Output: {output_file}")


if __name__ == "__main__":

    clean_dataset(
        "olist_customers_dataset.csv",
        "olist_customers.csv",
        "customer_id"
    )

    clean_dataset(
        "olist_sellers_dataset.csv",
        "olist_sellers.csv",
        "seller_id"
    )

    clean_dataset(
        "olist_products_dataset.csv",
        "olist_products.csv",
        "product_id"
    )

    clean_dataset(
        "product_category_name_translation.csv",
        "product_category_translation.csv",
        "product_category_name"
    )
