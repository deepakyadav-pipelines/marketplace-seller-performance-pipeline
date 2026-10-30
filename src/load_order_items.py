
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

load_dotenv()

SILVER_DIR = Path("data/silver")
INPUT_FILE = SILVER_DIR / "olist_order_items.csv"

url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(url)


def load_order_items():

    items = pd.read_csv(INPUT_FILE)

    items["shipping_limit_date"] = pd.to_datetime(
        items["shipping_limit_date"],
        errors="coerce"
    )

    # Fetch dimension key mappings.
    with engine.connect() as conn:
        sellers = pd.read_sql(
            text("SELECT seller_id, seller_key FROM dim_seller"),
            conn
        )

        products = pd.read_sql(
            text("SELECT product_id, product_key FROM dim_product"),
            conn
        )

        orders = pd.read_sql(
            text("SELECT order_id FROM fact_order"),
            conn
        )

    # Map seller keys.
    items = items.merge(
        sellers,
        on="seller_id",
        how="left",
        validate="many_to_one"
    )

    # Map product keys.
    items = items.merge(
        products,
        on="product_id",
        how="left",
        validate="many_to_one"
    )

    # Validate order references.
    items = items.merge(
        orders.assign(order_exists=True),
        on="order_id",
        how="left",
        validate="many_to_one"
    )

    unmatched_sellers = int(items["seller_key"].isna().sum())
    unmatched_products = int(items["product_key"].isna().sum())
    unmatched_orders = int(items["order_exists"].isna().sum())

    if unmatched_sellers or unmatched_products or unmatched_orders:
        raise ValueError(
            f"Unmatched references: sellers={unmatched_sellers}, "
            f"products={unmatched_products}, orders={unmatched_orders}"
        )

    # Gross = item price + freight.
    items["gross_brl"] = (
        items["price"] + items["freight_value"]
    )

    fact_items = items[[
        "order_id",
        "order_item_id",
        "seller_key",
        "product_key",
        "shipping_limit_date",
        "price",
        "freight_value",
        "gross_brl",
    ]].copy()

    fact_items = fact_items.rename(columns={
        "shipping_limit_date": "shipping_limit_timestamp",
        "price": "price_brl",
        "freight_value": "freight_brl",
    })

    # Commission and FX values will be calculated later.
    fact_items["commission_rate"] = None
    fact_items["commission_brl"] = None
    fact_items["commission_usd"] = None
    fact_items["gross_usd"] = None
    fact_items["campaign_key"] = None

    fact_items = fact_items.where(
        pd.notna(fact_items),
        None
    )

    with engine.begin() as conn:
        fact_items.to_sql(
            "fact_order_item",
            con=conn,
            if_exists="append",
            index=False,
            chunksize=2000
        )

    print("\nOrder item loading completed!")
    print(f"Order items loaded: {len(fact_items):,}")
    print(f"Unmatched sellers: {unmatched_sellers}")
    print(f"Unmatched products: {unmatched_products}")
    print(f"Unmatched orders: {unmatched_orders}")


if __name__ == "__main__":
    load_order_items()
