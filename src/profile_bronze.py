
from pathlib import Path
import pandas as pd

BRONZE_DIR = Path("data/bronze")

csv_files = sorted(BRONZE_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in {BRONZE_DIR.resolve()}"
    )

print(f"\nFound {len(csv_files)} CSV files\n")
print("=" * 80)

for file_path in csv_files:
    print(f"\nFile: {file_path.name}")

    try:
        
        df = pd.read_csv(file_path, nrows=5)
        row_count = sum(
            len(chunk)
            for chunk in pd.read_csv(
                file_path,
                chunksize=50_000
            )
        )

        print(f"Rows: {row_count:,}")
        print(f"Columns: {len(df.columns)}")
        print("Column names:", list(df.columns))

        missing_values = {}
        for column in df.columns:
            missing_count = sum(
                chunk[column].isna().sum()
                for chunk in pd.read_csv(
                    file_path,
                    usecols=[column],
                    chunksize=50_000
                )
            )
            if missing_count:
                missing_values[column] = int(missing_count)

        if missing_values:
            print("Missing values:", missing_values)
        else:
            print("Missing values: None detected")

    except Exception as exc:
        print(f"ERROR reading file: {exc}")

    print("-" * 80)
