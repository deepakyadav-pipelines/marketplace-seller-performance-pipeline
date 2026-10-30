
import json
import time
from pathlib import Path

import requests

BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"
OUTPUT_DIR = Path("data/bronze/api")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = [2016, 2017, 2018]
COUNTRY_CODE = "BR"


def fetch_holidays(year, max_attempts=3):
    url = f"{BASE_URL}/{year}/{COUNTRY_CODE}"

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Fetching holidays for {year}, attempt {attempt}...")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, list):
                raise ValueError(f"Unexpected API response for {year}")

            if not data:
                raise ValueError(f"No holiday records returned for {year}")

            print(f"{year}: {len(data)} holidays fetched")
            return data

        except (requests.RequestException, ValueError) as error:
            print(f"Attempt {attempt} failed: {error}")

            if attempt == max_attempts:
                raise RuntimeError(
                    f"Holiday extraction failed for {year}"
                ) from error

            time.sleep(2 ** attempt)


def main():
    all_holidays = []

    for year in YEARS:
        holidays = fetch_holidays(year)
        all_holidays.extend(holidays)

    output_file = OUTPUT_DIR / "brazil_holidays.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(all_holidays, file, indent=2, ensure_ascii=False)

    print("\nHoliday extraction completed!")
    print(f"Total holidays: {len(all_holidays)}")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
