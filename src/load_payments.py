
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL

load_dotenv()

INPUT_FILE = Path("data/silver/olist_order_payments.csv")

url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(url)


def load_payments():
    payments = pd.read_csv(INPUT_FILE)

    payments = payments.rename(columns={
        "payment_value": "payment_value_brl"
    })

    payments["payment_value_brl"] = pd.to_numeric(
        payments["payment_value_brl"],
        errors="raise"
    )

    with engine.begin() as conn:
        payments.to_sql(
            "fact_order_payment",
            con=conn,
            if_exists="append",
            index=False,
            chunksize=2000
        )

    print("Payment loading completed!")
    print(f"Payment records loaded: {len(payments):,}")


if __name__ == "__main__":
    load_payments()
