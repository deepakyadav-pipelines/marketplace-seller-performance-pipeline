
from pathlib import Path
import pandas as pd

BRONZE_DIR = Path("data/bronze")
SILVER_DIR = Path("data/silver")

INPUT_FILE = BRONZE_DIR / "olist_geolocation_dataset.csv"
OUTPUT_FILE = SILVER_DIR / "olist_geolocation.csv"
DQ_FILE = SILVER_DIR / "geolocation_quality_report.csv"

CHUNK_SIZE = 100_000


def transform_geolocation():
    SILVER_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    valid_chunks = []
    total_rows = 0
    invalid_rows = 0

    # Read large CSV in chunks to manage memory.
    for chunk in pd.read_csv(
        INPUT_FILE,
        usecols=[
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
        ],
        dtype={
            "geolocation_zip_code_prefix": "string"
        },
        chunksize=CHUNK_SIZE,
    ):
        total_rows += len(chunk)

        chunk["geolocation_lat"] = pd.to_numeric(
            chunk["geolocation_lat"],
            errors="coerce"
        )

        chunk["geolocation_lng"] = pd.to_numeric(
            chunk["geolocation_lng"],
            errors="coerce"
        )

        # Apply assignment bounding box.
        valid_mask = (
            chunk["geolocation_lat"].between(-33.75, 5.27)
            & chunk["geolocation_lng"].between(-73.99, -34.79)
            & chunk["geolocation_zip_code_prefix"].notna()
        )

        valid = chunk.loc[
            valid_mask,
            [
                "geolocation_zip_code_prefix",
                "geolocation_lat",
                "geolocation_lng",
            ],
        ].copy()

        invalid_rows += int((~valid_mask).sum())

        valid_chunks.append(valid)

    if not valid_chunks:
        raise ValueError("No valid geolocation records found.")

    # Combine valid records before calculating exact medians.
    valid_df = pd.concat(valid_chunks, ignore_index=True)

    # Median coordinates for each ZIP-code prefix.
    result = (
        valid_df.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            median_latitude=("geolocation_lat", "median"),
            median_longitude=("geolocation_lng", "median"),
        )
    )

    result.to_csv(OUTPUT_FILE, index=False)

    dq_report = pd.DataFrame([
        {
            "rule_id": "R15",
            "issue_type": "OUTSIDE_BOUNDING_BOX_OR_INVALID",
            "issue_count": invalid_rows,
        }
    ])

    dq_report.to_csv(DQ_FILE, index=False)

    print("\nGeolocation transformation completed!")
    print(f"Original rows: {total_rows:,}")
    print(f"Valid coordinate rows: {len(valid_df):,}")
    print(f"Excluded rows: {invalid_rows:,}")
    print(f"Unique ZIP prefixes: {len(result):,}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"DQ report: {DQ_FILE}")


if __name__ == "__main__":
    transform_geolocation()
