
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INTERNAL_DIR = BASE_DIR / "data" / "internal"
SILVER_DIR = BASE_DIR / "data" / "silver"

SILVER_DIR.mkdir(parents=True, exist_ok=True)


def clean_commission_rates():
    source = INTERNAL_DIR / "commission_rates.csv"

    df = pd.read_csv(source)
    original = df.copy()

    df["tier"] = df["tier"].astype(str).str.strip().str.title()
    df["rate"] = pd.to_numeric(df["rate"], errors="coerce")

    df["effective_from"] = pd.to_datetime(
        df["effective_from"], errors="coerce"
    )
    df["effective_to"] = pd.to_datetime(
        df["effective_to"], errors="coerce"
    )

    df["effective_to"] = df["effective_to"].fillna(
        pd.Timestamp("2262-04-11")
    )

    df["cleaning_action"] = "accepted"
    df["cleaning_reason"] = ""

    normalized = original["tier"].astype(str).str.strip() != df["tier"]
    df.loc[normalized, "cleaning_action"] = "corrected"
    df.loc[normalized, "cleaning_reason"] = "Tier name normalized"

    invalid = (
        ~df["tier"].isin(["Bronze", "Silver", "Gold"])
        | df["rate"].isna()
        | (df["rate"] <= 0)
        | (df["rate"] > 1)
        | df["effective_from"].isna()
        | (df["effective_from"] > df["effective_to"])
    )

    df.loc[invalid, "cleaning_action"] = "rejected"
    df.loc[invalid, "cleaning_reason"] = "Invalid tier, rate, or effective dates"

    return df


def clean_category_overrides():
    source = INTERNAL_DIR / "category_commission_overrides.csv"

    df = pd.read_csv(source)
    original = df.copy()

    df["category_name_en"] = (
        df["category_name_en"].astype(str).str.strip().str.lower()
    )

    df["fixed_rate"] = pd.to_numeric(
        df["fixed_rate"], errors="coerce"
    )

    df["effective_from"] = pd.to_datetime(
        df["effective_from"], errors="coerce"
    )
    df["effective_to"] = pd.to_datetime(
        df["effective_to"], errors="coerce"
    )

    df["effective_to"] = df["effective_to"].fillna(
        pd.Timestamp("2262-04-11")
    )

    df["cleaning_action"] = "accepted"
    df["cleaning_reason"] = ""

    normalized = (
        original["category_name_en"].astype(str).str.strip().str.lower()
        != original["category_name_en"].astype(str).str.strip()
    )

    df.loc[normalized, "cleaning_action"] = "corrected"
    df.loc[normalized, "cleaning_reason"] = "Category name normalized"

    invalid = (
        df["category_name_en"].eq("")
        | df["fixed_rate"].isna()
        | (df["fixed_rate"] <= 0)
        | (df["fixed_rate"] > 1)
        | df["effective_from"].isna()
        | (df["effective_from"] > df["effective_to"])
    )

    df.loc[invalid, "cleaning_action"] = "rejected"
    df.loc[invalid, "cleaning_reason"] = "Invalid category, rate, or effective dates"

    return df


if __name__ == "__main__":
    rates = clean_commission_rates()
    overrides = clean_category_overrides()

    rates.to_csv(
        SILVER_DIR / "commission_rates_clean.csv", index=False
    )

    overrides.to_csv(
        SILVER_DIR / "category_commission_overrides_clean.csv",
        index=False
    )

    audit = pd.concat(
        [
            rates.assign(source_file="commission_rates.csv"),
            overrides.assign(source_file="category_commission_overrides.csv"),
        ],
        ignore_index=True,
        sort=False
    )

    audit = audit[
        audit["cleaning_action"].isin(["corrected", "rejected"])
    ]

    audit.to_csv(
        SILVER_DIR / "commission_cleaning_audit.csv",
        index=False
    )

    print("Commission files cleaned successfully!")
    print("\nTier rates:")
    print(rates[["tier", "rate", "cleaning_action", "cleaning_reason"]])

    print("\nCategory overrides:")
    print(overrides[
        ["category_name_en", "fixed_rate", "cleaning_action", "cleaning_reason"]
    ])

    print("\nAudit summary:")
    print(audit.groupby(
        ["source_file", "cleaning_action"]
    ).size())
