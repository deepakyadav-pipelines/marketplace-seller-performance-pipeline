
from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

db_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(db_url)

BATCH_SIZE = 5000


def calculate_commissions():
    print("Starting R13 commission calculation...")

    with engine.begin() as conn:

        # Calculate applicable rate:
        # 1. Active category override
        # 2. Otherwise active seller-tier rate
        conn.execute(text("""
            UPDATE fact_order_item i
            JOIN fact_order o
                ON i.order_id = o.order_id
            JOIN dim_product p
                ON i.product_key = p.product_key
            LEFT JOIN seller_monthly_tier st
                ON st.seller_key = i.seller_key
                AND st.tier_month =
                    DATE_SUB(
                        DATE(o.purchase_timestamp),
                        INTERVAL DAYOFMONTH(o.purchase_timestamp) - 1 DAY
                    )
            LEFT JOIN ref_category_commission_override co
                ON LOWER(TRIM(co.category_name_en)) =
                   LOWER(TRIM(p.category_name_english))
                AND DATE(o.purchase_timestamp) >= co.effective_from
                AND (
                    co.effective_to IS NULL
                    OR DATE(o.purchase_timestamp) <= co.effective_to
                )
            LEFT JOIN ref_commission_rate cr
                ON cr.tier = st.seller_tier
                AND DATE(o.purchase_timestamp) >= cr.effective_from
                AND (
                    cr.effective_to IS NULL
                    OR DATE(o.purchase_timestamp) <= cr.effective_to
                )
            SET i.commission_rate =
                COALESCE(co.fixed_rate, cr.rate)
            WHERE o.revenue_eligible = 1
        """))

        # Reset non-revenue-eligible items
        conn.execute(text("""
            UPDATE fact_order_item i
            JOIN fact_order o ON i.order_id = o.order_id
            SET
                i.commission_rate = NULL,
                i.commission_brl = NULL,
                i.commission_usd = NULL
            WHERE o.revenue_eligible = 0
        """))

        # Calculate BRL commission and USD commission.
        # ROUND only final monetary values.
        conn.execute(text("""
            UPDATE fact_order_item i
            JOIN fact_order o ON i.order_id = o.order_id
            SET
                i.commission_brl =
                    CASE
                        WHEN i.commission_rate IS NOT NULL
                        THEN ROUND(i.price_brl * i.commission_rate, 2)
                        ELSE NULL
                    END,
                i.commission_usd =
                    CASE
                        WHEN i.commission_rate IS NOT NULL
                             AND i.fx_rate_brl_to_usd IS NOT NULL
                        THEN ROUND(
                            i.price_brl
                            * i.commission_rate
                            * i.fx_rate_brl_to_usd,
                            2
                        )
                        ELSE NULL
                    END
            WHERE o.revenue_eligible = 1
        """))

        # Log missing commission rates.
        conn.execute(text("""
            INSERT INTO data_quality_issue
                (rule_id, entity_type, entity_id,
                 issue_type, details)
            SELECT
                'R13',
                'order_item',
                CAST(i.order_item_key AS CHAR),
                'MISSING_COMMISSION_RATE',
                CONCAT(
                    'No active category override or seller tier rate. ',
                    'Order: ', i.order_id,
                    ', category: ', COALESCE(p.category_name_english, 'NULL')
                )
            FROM fact_order_item i
            JOIN fact_order o ON i.order_id = o.order_id
            JOIN dim_product p ON i.product_key = p.product_key
            WHERE o.revenue_eligible = 1
              AND i.commission_rate IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM data_quality_issue dq
                  WHERE dq.rule_id = 'R13'
                    AND dq.entity_type = 'order_item'
                    AND dq.entity_id = CAST(i.order_item_key AS CHAR)
                    AND dq.issue_type = 'MISSING_COMMISSION_RATE'
              )
        """))

        # Missing FX rate is separately recorded.
        conn.execute(text("""
            INSERT INTO data_quality_issue
                (rule_id, entity_type, entity_id,
                 issue_type, details)
            SELECT
                'R13',
                'order_item',
                CAST(i.order_item_key AS CHAR),
                'MISSING_FX_RATE_FOR_COMMISSION',
                CONCAT('Missing FX rate for order ', i.order_id)
            FROM fact_order_item i
            JOIN fact_order o ON i.order_id = o.order_id
            WHERE o.revenue_eligible = 1
              AND i.commission_rate IS NOT NULL
              AND i.fx_rate_brl_to_usd IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM data_quality_issue dq
                  WHERE dq.rule_id = 'R13'
                    AND dq.entity_type = 'order_item'
                    AND dq.entity_id = CAST(i.order_item_key AS CHAR)
                    AND dq.issue_type = 'MISSING_FX_RATE_FOR_COMMISSION'
              )
        """))

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) AS total_items,
                SUM(commission_rate IS NOT NULL) AS rated_items,
                SUM(commission_rate IS NULL) AS missing_rate_items,
                SUM(commission_brl IS NOT NULL) AS calculated_brl,
                SUM(commission_usd IS NOT NULL) AS calculated_usd,
                ROUND(SUM(commission_brl), 2) AS total_commission_brl,
                ROUND(SUM(commission_usd), 2) AS total_commission_usd
            FROM fact_order_item i
            JOIN fact_order o ON i.order_id = o.order_id
            WHERE o.revenue_eligible = 1
        """)).mappings().one()

        print("\nR13 calculation summary:")
        for key, value in result.items():
            print(f"{key}: {value}")

    print("\nR13 commission calculation completed!")


if __name__ == "__main__":
    calculate_commissions()
