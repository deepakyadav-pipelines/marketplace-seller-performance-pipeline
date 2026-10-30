
import json
from pathlib import Path

from dotenv import load_dotenv
import os

from sqlalchemy import create_engine, URL, text

load_dotenv()

INPUT_FILE = Path("data/bronze/api/fx_rates.json")

url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(url)


def load_fx_rates():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    rates = data.get("rates", {})

    if not rates:
        raise ValueError("No FX rates found in API response.")

    records = []

    for rate_date, currencies in rates.items():
        usd_rate = currencies.get("USD")

        if usd_rate is None or float(usd_rate) <= 0:
            raise ValueError(
                f"Invalid USD exchange rate for {rate_date}"
            )

        records.append({
            "rate_date": rate_date,
            "from_currency": "BRL",
            "to_currency": "USD",
            "exchange_rate": round(float(usd_rate), 6),
        })

    insert_query = text("""
        INSERT INTO ref_fx_rate (
            rate_date,
            from_currency,
            to_currency,
            exchange_rate
        )
        VALUES (
            :rate_date,
            :from_currency,
            :to_currency,
            :exchange_rate
        )
        ON DUPLICATE KEY UPDATE
            exchange_rate = VALUES(exchange_rate)
    """)

    with engine.begin() as conn:
        conn.execute(insert_query, records)

    print("\nFX rates loaded successfully!")
    print(f"Records processed: {len(records):,}")
    print(f"First date: {min(r['rate_date'] for r in records)}")
    print(f"Last date: {max(r['rate_date'] for r in records)}")


if __name__ == "__main__":
    load_fx_rates()
