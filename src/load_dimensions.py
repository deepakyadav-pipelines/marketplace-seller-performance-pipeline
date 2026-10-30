
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

load_dotenv()

SILVER_DIR = Path("data/silver")

required_env = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
]

missing = [key for key in required_env if not os.getenv(key)]

if missing:
    raise RuntimeError(
        f"Missing environment variables: {missing}"
    )

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(connection_url)


def load_table(df, table_name):
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )

    print(f"{table_name}: {len(df):,} rows loaded")


def load_customers():
    df = pd.read_csv(SILVER_DIR / "olist_customers.csv")

    df = df.rename(columns={
        "customer_zip_code_prefix": "zip_code_prefix",
        "customer_city": "city",
        "customer_state": "state",
    })

    df = df[[
        "customer_id",
        "customer_unique_id",
        "zip_code_prefix",
        "city",
        "state",
    ]]

    load_table(df, "dim_customer")


def load_sellers():
    df = pd.read_csv(SILVER_DIR / "olist_sellers.csv")

    df = df.rename(columns={
        "seller_zip_code_prefix": "zip_code_prefix",
        "seller_city": "city",
        "seller_state": "state",
    })

    df["region"] = df["state"].map({
        "AC": "Norte", "AP": "Norte", "AM": "Norte",
        "PA": "Norte", "RO": "Norte", "RR": "Norte",
        "TO": "Norte",
        "AL": "Nordeste", "BA": "Nordeste",
        "CE": "Nordeste", "MA": "Nordeste",
        "PB": "Nordeste", "PE": "Nordeste",
        "PI": "Nordeste", "RN": "Nordeste",
        "SE": "Nordeste",
        "DF": "Centro-Oeste", "GO": "Centro-Oeste",
        "MT": "Centro-Oeste", "MS": "Centro-Oeste",
        "ES": "Sudeste", "MG": "Sudeste",
        "RJ": "Sudeste", "SP": "Sudeste",
        "PR": "Sul", "RS": "Sul", "SC": "Sul",
    })

    df = df.rename(columns={"seller_id": "seller_id"})

    df = df[[
        "seller_id",
        "zip_code_prefix",
        "city",
        "state",
        "region",
    ]]

    load_table(df, "dim_seller")


def load_products():
    products = pd.read_csv(SILVER_DIR / "olist_products.csv")

    translations = pd.read_csv(
        SILVER_DIR / "product_category_translation.csv"
    )

    # Translation patch has higher priority than Kaggle mapping.
    patch = pd.read_csv(
        "data/internal/category_translation_patch.csv"
    )

    patch = patch.rename(columns={
        "product_category_name": "product_category_name",
        "product_category_name_english": "patch_english",
    })

    translations = translations.merge(
        patch,
        on="product_category_name",
        how="left",
    )

    translations["category_name_english"] = (
        translations["patch_english"]
        .fillna(translations["product_category_name_english"])
    )

    products = products.merge(
        translations[
            ["product_category_name", "category_name_english"]
        ],
        on="product_category_name",
        how="left",
    )

    products["category_name_english"] = (
        products["category_name_english"]
        .fillna("unknown")
    )

    products = products.rename(columns={
        "product_category_name": "category_name",
        "product_weight_g": "weight_g",
        "product_length_cm": "length_cm",
        "product_height_cm": "height_cm",
        "product_width_cm": "width_cm",
    })

    products = products[[
        "product_id",
        "category_name",
        "category_name_english",
        "weight_g",
        "length_cm",
        "height_cm",
        "width_cm",
    ]]

    load_table(products, "dim_product")


if __name__ == "__main__":
    with engine.begin():
        load_customers()
        load_sellers()
        load_products()

    print("\nDimension loading completed!")
