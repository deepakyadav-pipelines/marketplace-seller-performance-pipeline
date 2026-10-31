
import pandas as pd
from sqlalchemy import create_engine, URL, text
from dotenv import load_dotenv
import os

# Load database configuration
load_dotenv()

db_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url)

# Read Silver review data
file_path = "data/silver/olist_order_reviews.csv"

df = pd.read_csv(file_path)

# Parse timestamps
df["review_answer_timestamp"] = pd.to_datetime(
    df["review_answer_timestamp"],
    errors="coerce"
)

df["review_creation_date"] = pd.to_datetime(
    df["review_creation_date"],
    errors="coerce"
)

# Select latest review per order
latest_reviews = (
    df.sort_values(
        ["review_answer_timestamp"],
        kind="stable"
    )
    .drop_duplicates(
        subset=["order_id"],
        keep="last"
    )
    .copy()
)

# Prepare records for MySQL
columns = [
    "review_id",
    "order_id",
    "review_score",
    "review_creation_date",
    "review_answer_timestamp",
]

# Keep optional comments if present in source
for col in ["review_comment_title", "review_comment_message"]:
    if col not in latest_reviews.columns:
        latest_reviews[col] = None

reviews_to_load = latest_reviews[columns].copy()

# Convert pandas NaN / NaT values to Python None
reviews_to_load = reviews_to_load.astype(object).where(
    pd.notna(reviews_to_load),
    None
)

# Insert reviews and seller mappings in one transaction
with engine.begin() as conn:

    # Insert latest reviews (ignore already loaded review/order pairs)
    insert_review = text("""
        INSERT INTO fact_order_review (
            review_id,
            order_id,
            review_score,
            review_creation_date,
            review_answer_timestamp
        )
        VALUES (
            :review_id,
            :order_id,
            :review_score,
            :review_creation_date,
            :review_answer_timestamp
        )
        ON DUPLICATE KEY UPDATE
            review_score = VALUES(review_score),
            review_answer_timestamp = VALUES(review_answer_timestamp)
    """)
    conn.execute(
        insert_review,
        reviews_to_load.to_dict("records")
    )

    # Map every review to every seller in its order
    conn.execute(text("""
        INSERT IGNORE INTO bridge_seller_review (
            seller_key,
            review_key,
            order_id
        )
        SELECT DISTINCT
            i.seller_key,
            r.review_key,
            r.order_id
        FROM fact_order_review r
        JOIN fact_order_item i
            ON r.order_id = i.order_id
    """))

# Verification
with engine.connect() as conn:

    review_count = conn.execute(text("""
        SELECT COUNT(*) FROM fact_order_review
    """)).scalar()

    mapping_count = conn.execute(text("""
        SELECT COUNT(*) FROM bridge_seller_review
    """)).scalar()

    orders_without_seller_mapping = conn.execute(text("""
        SELECT COUNT(*)
        FROM fact_order_review r
        WHERE NOT EXISTS (
            SELECT 1
            FROM bridge_seller_review b
            WHERE b.review_key = r.review_key
        )
    """)).scalar()

print("Original review records:", len(df))
print("Latest reviews selected:", len(latest_reviews))
print("Reviews in MySQL:", review_count)
print("Seller-review mappings:", mapping_count)
print("Reviews without seller mapping:", orders_without_seller_mapping)

print("\nR14 review loading completed successfully!")
