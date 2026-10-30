
import json
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv()

from sqlalchemy import create_engine, URL

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


INPUT_FILE = Path("data/bronze/api/brazil_holidays.json")


def map_holiday(record):
    holiday_date = record["date"]
    holiday_name = record["name"]
    holiday_type = ",".join(record.get("types") or [])

    if record["global"]:
        return [{
            "holiday_date": holiday_date,
            "state": "BR",
            "holiday_name": holiday_name,
            "holiday_type": holiday_type
        }]

    counties = record.get("counties") or []
    mapped_records = []

    for county in counties:
        # API format: BR-SP, BR-RJ, etc.
        state_code = county.split("-")[-1]

        mapped_records.append({
            "holiday_date": holiday_date,
            "state": state_code,
            "holiday_name": holiday_name,
            "holiday_type": holiday_type
        })

    return mapped_records


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"File not found: {INPUT_FILE}")

    with open(INPUT_FILE, encoding="utf-8") as file:
        holidays = json.load(file)

    rows = []

    for record in holidays:
        rows.extend(map_holiday(record))

    if not rows:
        raise ValueError("No holiday records available to load")

    query = text("""
        INSERT INTO ref_holiday
            (holiday_date, state, holiday_name, holiday_type)
        VALUES
            (:holiday_date, :state, :holiday_name, :holiday_type)
        ON DUPLICATE KEY UPDATE
            holiday_name = VALUES(holiday_name),
            holiday_type = VALUES(holiday_type)
    """)

    with engine.begin() as connection:
        connection.execute(query, rows)

    national_count = sum(1 for row in rows if row["state"] == "BR")
    regional_count = len(rows) - national_count

    print("Holiday loading completed!")
    print(f"Source API records: {len(holidays)}")
    print(f"Database rows prepared: {len(rows)}")
    print(f"National holiday rows: {national_count}")
    print(f"Regional holiday rows: {regional_count}")


if __name__ == "__main__":
    main()
