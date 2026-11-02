
import os
import math
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

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in kilometres."""

    lat1, lon1, lat2, lon2 = map(
        math.radians,
        [lat1, lon1, lat2, lon2]
    )

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    a = min(1.0, max(0.0, a))

    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


# Fetch order item and coordinate data
query = text("""
    SELECT
        i.order_item_key,
        i.order_id,
        c.zip_code_prefix AS customer_zip,
        s.zip_code_prefix AS seller_zip,
        cg.median_latitude AS customer_lat,
        cg.median_longitude AS customer_lon,
        sg.median_latitude AS seller_lat,
        sg.median_longitude AS seller_lon
    FROM fact_order_item i
    JOIN fact_order o
        ON i.order_id = o.order_id
    JOIN dim_customer c
        ON o.customer_key = c.customer_key
    JOIN dim_seller s
        ON i.seller_key = s.seller_key
    LEFT JOIN ref_geolocation cg
        ON c.zip_code_prefix = cg.zip_code_prefix
    LEFT JOIN ref_geolocation sg
        ON s.zip_code_prefix = sg.zip_code_prefix
""")

with engine.connect() as conn:
    df = pd.read_sql(query, conn)

print("Total order items:", len(df))

# Calculate distance
distances = []

for row in df.itertuples(index=False):

    coordinates = [
        row.customer_lat,
        row.customer_lon,
        row.seller_lat,
        row.seller_lon
    ]

    if any(pd.isna(value) for value in coordinates):
        distances.append(None)
    else:
        distance = haversine_distance(
            row.customer_lat,
            row.customer_lon,
            row.seller_lat,
            row.seller_lon
        )
        distances.append(round(distance, 3))

df["seller_customer_distance_km"] = distances

# Separate valid and missing coordinate records
valid_df = df.dropna(
    subset=["seller_customer_distance_km"]
)

missing_df = df[
    df["seller_customer_distance_km"].isna()
]

print("Distances calculated:", len(valid_df))
print("Missing coordinate records:", len(missing_df))

# Update MySQL in batches
update_query = text("""
    UPDATE fact_order_item
    SET seller_customer_distance_km =
        :seller_customer_distance_km
    WHERE order_item_key = :order_item_key
""")

records = [
    {
        "order_item_key": int(row.order_item_key),
        "seller_customer_distance_km":
            float(row.seller_customer_distance_km)
    }
    for row in valid_df.itertuples(index=False)
]

with engine.begin() as conn:

    batch_size = 2000

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        conn.execute(update_query, batch)

    # Log missing-coordinate issues without creating duplicates
    for row in missing_df.itertuples(index=False):

        conn.execute(text("""
            INSERT INTO data_quality_issue (
                rule_id,
                entity_type,
                entity_id,
                issue_type,
                details
            )
            SELECT
                'R16',
                'order_item',
                :entity_id,
                'MISSING_GEOLOCATION',
                :details
            WHERE NOT EXISTS (
                SELECT 1
                FROM data_quality_issue
                WHERE rule_id = 'R16'
                  AND entity_type = 'order_item'
                  AND entity_id = :entity_id
                  AND issue_type = 'MISSING_GEOLOCATION'
            )
        """), {
            "entity_id": str(row.order_item_key),
            "details": (
                f"Missing coordinates. Customer ZIP: "
                f"{row.customer_zip}; Seller ZIP: {row.seller_zip}"
            )
        })

# Final verification
with engine.connect() as conn:

    result = conn.execute(text("""
        SELECT
            COUNT(*) AS total_items,
            COUNT(seller_customer_distance_km) AS calculated,
            SUM(seller_customer_distance_km IS NULL) AS missing
        FROM fact_order_item
    """)).fetchone()

    dq_count = conn.execute(text("""
        SELECT COUNT(*)
        FROM data_quality_issue
        WHERE rule_id = 'R16'
          AND issue_type = 'MISSING_GEOLOCATION'
    """)).scalar()

print("\nFinal MySQL verification:")
print("Total items:", result[0])
print("Calculated distances:", result[1])
print("NULL distances:", result[2])
print("R16 DQ issues:", dq_count)

print("\nR16 distance calculation completed!")
