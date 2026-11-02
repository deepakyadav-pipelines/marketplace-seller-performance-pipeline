
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

load_dotenv()

required_env = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME",
]

missing = [key for key in required_env if not os.getenv(key)]

if missing:
    raise RuntimeError(f"Missing environment variables: {missing}")

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(connection_url)

products = pd.read_csv(
    Path("data/silver/olist_products_resolved.csv")
)

# Prepare only the columns needed for the update
products = products[
    ["product_id", "category_name_english"]
].copy()

products["category_name_english"] = (
    products["category_name_english"].fillna("uncategorized")
)

update_sql = text("""
    UPDATE dim_product
    SET category_name_english = :category_name_english
    WHERE product_id = :product_id
""")

records = products.to_dict(orient="records")

with engine.begin() as connection:
    result = connection.execute(update_sql, records)

    print("Products processed:", len(records))
    print("Rows updated:", result.rowcount)

    validation = connection.execute(text("""
        SELECT
            COUNT(*) AS total_products,
            SUM(category_name_english = 'unknown') AS unknown_count,
            SUM(category_name_english = 'uncategorized') AS uncategorized_count,
            SUM(category_name_english IS NULL) AS null_count
        FROM dim_product
    """)).mappings().one()

    print("\nMySQL validation:")
    print(dict(validation))

engine.dispose()
