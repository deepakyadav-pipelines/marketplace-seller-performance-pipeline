import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

load_dotenv()

# Database connection
db_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url)

# Read cleaned Silver geolocation data
file_path = "data/silver/olist_geolocation.csv"
df = pd.read_csv(file_path)

# Validate source data
required_columns = [
    "geolocation_zip_code_prefix",
    "median_latitude",
    "median_longitude",
]

if not all(col in df.columns for col in required_columns):
    raise ValueError("Required geolocation columns are missing.")

df = df[required_columns].copy()

if df.isnull().any().any():
    raise ValueError("Null values found in geolocation data.")

if df["geolocation_zip_code_prefix"].duplicated().any():
    raise ValueError("Duplicate ZIP prefixes found.")

# Load into MySQL using upsert
insert_query = text("""
    INSERT INTO ref_geolocation (
        zip_code_prefix,
        median_latitude,
        median_longitude
    )
    VALUES (
        :zip_code_prefix,
        :median_latitude,
        :median_longitude
    )
    ON DUPLICATE KEY UPDATE
        median_latitude = VALUES(median_latitude),
        median_longitude = VALUES(median_longitude)
""")

records = df.rename(
    columns={
        "geolocation_zip_code_prefix": "zip_code_prefix"
    }
).to_dict("records")

with engine.begin() as conn:
    conn.execute(insert_query, records)

# Verify load
with engine.connect() as conn:
    total_records = conn.execute(
        text("SELECT COUNT(*) FROM ref_geolocation")
    ).scalar()

    sample = conn.execute(text("""
        SELECT *
        FROM ref_geolocation
        ORDER BY zip_code_prefix
        LIMIT 5
    """)).fetchall()

print("Silver records:", len(df))
print("MySQL records:", total_records)
print("\nSample records:")

for row in sample:
    print(row)

print("\nR15 geolocation loading completed successfully!")