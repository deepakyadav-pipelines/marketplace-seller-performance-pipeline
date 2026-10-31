
import os
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import create_engine, text, URL

load_dotenv()

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

START_MONTH = date(2017, 1, 1)

MONTHS = [
    "2017-01-01", "2017-02-01", "2017-03-01",
    "2017-04-01", "2017-05-01", "2017-06-01",
    "2017-07-01", "2017-08-01", "2017-09-01",
    "2017-10-01", "2017-11-01", "2017-12-01",
    "2018-01-01", "2018-02-01", "2018-03-01",
    "2018-04-01", "2018-05-01", "2018-06-01",
    "2018-07-01", "2018-08-01",
]


def calculate_seller_tiers():
    print("Starting monthly seller tier calculation...")

    with engine.begin() as connection:

        # Create temporary month table
        connection.execute(text("""
            CREATE TEMPORARY TABLE temp_tier_months (
                tier_month DATE PRIMARY KEY
            )
        """))

        connection.execute(
            text("""
                INSERT INTO temp_tier_months (tier_month)
                VALUES (:month)
            """),
            [{"month": month} for month in MONTHS]
        )

        # Calculate previous month's revenue and seller tier
        connection.execute(text("""
            CREATE TEMPORARY TABLE temp_seller_tiers AS
            SELECT
                s.seller_key,
                m.tier_month,
                COALESCE(r.previous_month_revenue, 0)
                    AS previous_month_revenue_brl,
                CASE
                    WHEN COALESCE(r.previous_month_revenue, 0) < 5000
                        THEN 'Bronze'
                    WHEN COALESCE(r.previous_month_revenue, 0) <= 20000
                        THEN 'Silver'
                    ELSE 'Gold'
                END AS seller_tier
            FROM dim_seller s
            CROSS JOIN temp_tier_months m
            LEFT JOIN (
                SELECT
                    i.seller_key,
                    DATE_SUB(
                        DATE(o.purchase_timestamp),
                        INTERVAL DAYOFMONTH(o.purchase_timestamp) - 1 DAY
                    ) AS revenue_month,
                    SUM(i.price_brl) AS previous_month_revenue
                FROM fact_order_item i
                JOIN fact_order o
                    ON i.order_id = o.order_id
                WHERE o.revenue_eligible = 1
                AND o.purchase_timestamp >= '2016-12-01'
                AND o.purchase_timestamp < '2018-09-01'
                GROUP BY
                    i.seller_key,
                    DATE_SUB(
                        DATE(o.purchase_timestamp),
                        INTERVAL DAYOFMONTH(o.purchase_timestamp) - 1 DAY
                    )
            ) r
                ON r.seller_key = s.seller_key
                AND r.revenue_month = DATE_SUB(
                    m.tier_month, INTERVAL 1 MONTH
                )

        """))

        # Upsert into permanent table
        connection.execute(text("""
        INSERT INTO seller_monthly_tier (
            seller_key,
            tier_month,
            previous_month_revenue_brl,
            seller_tier
        )
        SELECT
            seller_key,
            tier_month,
            previous_month_revenue_brl,
            seller_tier
        FROM temp_seller_tiers
        ON DUPLICATE KEY UPDATE
            previous_month_revenue_brl =
                VALUES(previous_month_revenue_brl),
            seller_tier = VALUES(seller_tier)
        """))

        

        total = connection.execute(text("""
            SELECT COUNT(*) FROM seller_monthly_tier
        """)).scalar_one()

        print(f"Total tier records: {total}")

    print("Seller tier calculation completed successfully!")


if __name__ == "__main__":
    try:
        calculate_seller_tiers()
    except Exception as error:
        print(f"Seller tier calculation failed: {error}")
        raise
