
from pathlib import Path
import time

import pandas as pd
import requests

OUTPUT_DIR = Path("data/bronze/api")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

API_URL = (
    "https://api.frankfurter.dev/v1/"
    "2016-01-01..2018-08-31"
    "?from=BRL&to=USD"
)

PARAMS = {
    "from": "BRL",
    "to": "USD",
}


def fetch_fx_rates():
    for attempt in range(1, 4):
        try:
            response = requests.get(
                API_URL,
                params=PARAMS,
                timeout=30,
            )

            response.raise_for_status()

            data = response.json()

            if not data.get("rates"):
                raise ValueError("API returned no exchange rates.")

            records = []

            for rate_date, currencies in data["rates"].items():
                records.append({
                    "rate_date": rate_date,
                    "from_currency": "BRL",
                    "to_currency": "USD",
                    "exchange_rate": currencies["USD"],
                })

            df = pd.DataFrame(records)

            df["rate_date"] = pd.to_datetime(
                df["rate_date"]
            )

            df["exchange_rate"] = pd.to_numeric(
                df["exchange_rate"],
                errors="raise"
            )

            if df["exchange_rate"].isna().any():
                raise ValueError("Null FX rates detected.")

            output_file = OUTPUT_DIR / "fx_rates.json"

            output_file.write_text(
                response.text,
                encoding="utf-8"
            )

            print("FX extraction successful!")
            print(f"Records fetched: {len(df):,}")
            print(f"First date: {df['rate_date'].min()}")
            print(f"Last date: {df['rate_date'].max()}")
            print(f"Raw API response: {output_file}")

            return df

        except Exception as exc:
            print(f"Attempt {attempt} failed: {exc}")

            if attempt == 3:
                raise RuntimeError(
                    "FX API failed after 3 attempts."
                ) from exc

            time.sleep(2 ** attempt)


if __name__ == "__main__":
    fetch_fx_rates()
