
from pathlib import Path
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent.parent
SILVER_DIR = BASE_DIR / "data" / "silver"

load_dotenv(BASE_DIR / ".env")

db_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url)


def load_tier_rates():
    df = pd.read_csv(SILVER_DIR / "commission_rates_clean.csv")

    # Only accepted and corrected rows are loaded.
    df = df[df["cleaning_action"].isin(["accepted", "corrected"])].copy()

    df["effective_from"] = pd.to_datetime(df["effective_from"]).dt.date
    df["effective_to"] = pd.to_datetime(
        df["effective_to"], errors="coerce"
    ).dt.date

    records = df[
    ["tier", "rate", "effective_from", "effective_to"]
].astype(object).where(pd.notna(df), None).to_dict("records")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ref_commission_rate"))

        conn.execute(
            text("""
                INSERT INTO ref_commission_rate
                    (tier, rate, effective_from, effective_to)
                VALUES
                    (:tier, :rate, :effective_from, :effective_to)
            """),
            records
        )

    print(f"Loaded {len(records)} tier commission rates.")


def load_category_overrides():
    df = pd.read_csv(
        SILVER_DIR / "category_commission_overrides_clean.csv"
    )

    df = df[df["cleaning_action"].isin(["accepted", "corrected"])].copy()

    df["effective_from"] = pd.to_datetime(df["effective_from"]).dt.date
    df["effective_to"] = pd.to_datetime(
        df["effective_to"], errors="coerce"
    ).dt.date

    records = df[
    ["category_name_en", "fixed_rate", "effective_from",
     "effective_to", "notes"]
].astype(object).where(pd.notna(df), None).to_dict("records")
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ref_category_commission_override"))

        conn.execute(
            text("""
                INSERT INTO ref_category_commission_override
                    (category_name_en, fixed_rate, effective_from,
                     effective_to, notes)
                VALUES
                    (:category_name_en, :fixed_rate, :effective_from,
                     :effective_to, :notes)
            """),
            records
        )

    print(f"Loaded {len(records)} category commission overrides.")


if __name__ == "__main__":
    load_tier_rates()
    load_category_overrides()

    with engine.connect() as conn:
        tier_count = conn.execute(
            text("SELECT COUNT(*) FROM ref_commission_rate")
        ).scalar()

        override_count = conn.execute(
            text("SELECT COUNT(*) FROM ref_category_commission_override")
        ).scalar()

    print("\nCommission reference data loaded successfully!")
    print("Tier rates:", tier_count)
    print("Category overrides:", override_count)
