
import os
import re

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import URL, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

# Database connection
database_url = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "marketplace_db"),
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=3600
)

app = FastAPI(
    title="Marketplace Seller Performance API",
    description="API for marketplace orders, seller performance and analytics.",
    version="1.0.0"
)


def fetch_one(query, params=None):
    with engine.connect() as conn:
        row = conn.execute(text(query), params or {}).mappings().first()
        return dict(row) if row else None


def fetch_all(query, params=None):
    with engine.connect() as conn:
        rows = conn.execute(text(query), params or {}).mappings().all()
        return [dict(row) for row in rows]


# --------------------------------------------------
# 1. HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():
    try:
        fetch_one("SELECT 1 AS database_status")

        return {
            "status": "healthy",
            "database": "connected"
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )


# --------------------------------------------------
# 2. ORDER DETAILS
# --------------------------------------------------

@app.get("/orders/{order_id}")
def get_order_details(order_id: str):

    order = fetch_one("""
        SELECT
            o.order_id,
            o.order_status,
            o.purchase_timestamp,
            o.approved_timestamp,
            o.delivered_carrier_timestamp,
            o.delivered_customer_timestamp,
            o.estimated_delivery_timestamp,
            o.revenue_eligible,
            o.payment_total_brl,
            o.net_cash_paid_brl,
            o.payment_difference_brl,
            o.delivery_business_days,
            o.is_on_time,
            c.customer_id,
            c.customer_unique_id,
            c.city AS customer_city,
            c.state AS customer_state,
            c.region AS customer_region
        FROM fact_order o
        LEFT JOIN dim_customer c
            ON o.customer_key = c.customer_key
        WHERE o.order_id = :order_id
    """, {"order_id": order_id})

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    items = fetch_all("""
        SELECT
            i.order_item_id,
            s.seller_id,
            p.product_id,
            p.category_name_english,
            i.price_brl,
            i.freight_brl,
            i.gross_brl,
            i.commission_rate,
            i.commission_brl,
            i.commission_usd,
            i.gross_usd,
            i.seller_delivery_status,
            i.seller_customer_distance_km,
            c.campaign_id,
            c.campaign_name
        FROM fact_order_item i
        LEFT JOIN dim_seller s
            ON i.seller_key = s.seller_key
        LEFT JOIN dim_product p
            ON i.product_key = p.product_key
        LEFT JOIN dim_campaign c
            ON i.campaign_key = c.campaign_key
        WHERE i.order_id = :order_id
        ORDER BY i.order_item_id
    """, {"order_id": order_id})

    payments = fetch_all("""
        SELECT
            payment_sequential,
            payment_type,
            payment_installments,
            payment_value_brl
        FROM fact_order_payment
        WHERE order_id = :order_id
        ORDER BY payment_sequential
    """, {"order_id": order_id})

    return {
        "order": order,
        "items": items,
        "payments": payments
    }


# --------------------------------------------------
# 3. SELLER MONTHLY SCORECARD
# --------------------------------------------------

@app.get("/sellers/{seller_id}/scorecard")
def seller_scorecard(
    seller_id: str,
    month: str = Query(..., description="Month in YYYY-MM format")
):

    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise HTTPException(
            status_code=400,
            detail="Invalid month format. Use YYYY-MM."
        )

    seller = fetch_one("""
        SELECT
            seller_key,
            seller_id,
            city,
            state,
            region
        FROM dim_seller
        WHERE seller_id = :seller_id
    """, {"seller_id": seller_id})

    if not seller:
        raise HTTPException(
            status_code=404,
            detail="Seller not found"
        )

    performance = fetch_one("""
        SELECT
            COUNT(DISTINCT CASE
                WHEN o.revenue_eligible = 1 THEN i.order_id
            END) AS eligible_orders,

            COUNT(CASE
                WHEN o.revenue_eligible = 1 THEN i.order_item_key
            END) AS eligible_items,

            ROUND(SUM(CASE
                WHEN o.revenue_eligible = 1 THEN i.price_brl
                ELSE 0
            END), 2) AS revenue_brl,

            ROUND(SUM(CASE
                WHEN o.revenue_eligible = 1 THEN i.commission_brl
                ELSE 0
            END), 2) AS commission_brl,

            ROUND(SUM(CASE
                WHEN o.revenue_eligible = 1 THEN i.commission_usd
                ELSE 0
            END), 2) AS commission_usd,

            SUM(CASE
                WHEN o.revenue_eligible = 1
                 AND i.seller_delivery_status = 'on_time'
                THEN 1 ELSE 0
            END) AS on_time_items,

            SUM(CASE
                WHEN o.revenue_eligible = 1
                 AND i.seller_delivery_status IN
                     ('on_time', 'seller_late', 'carrier_late')
                THEN 1 ELSE 0
            END) AS classified_delivery_items

        FROM fact_order_item i
        JOIN fact_order o
            ON i.order_id = o.order_id
        WHERE i.seller_key = :seller_key
          AND o.purchase_timestamp >= :month_start
          AND o.purchase_timestamp < DATE_ADD(:month_start, INTERVAL 1 MONTH)
    """, {
        "seller_key": seller["seller_key"],
        "month_start": f"{month}-01"
    })

    review = fetch_one("""
        SELECT
            ROUND(AVG(r.review_score), 2) AS average_review_score,
            COUNT(DISTINCT r.review_key) AS review_count
        FROM bridge_seller_review b
        JOIN fact_order_review r
            ON b.review_key = r.review_key
        JOIN fact_order o
            ON b.order_id = o.order_id
        WHERE b.seller_key = :seller_key
          AND o.purchase_timestamp >= :month_start
          AND o.purchase_timestamp < DATE_ADD(:month_start, INTERVAL 1 MONTH)
    """, {
        "seller_key": seller["seller_key"],
        "month_start": f"{month}-01"
    })

    tier = fetch_one("""
        SELECT
            seller_tier,
            previous_month_revenue_brl
        FROM seller_monthly_tier
        WHERE seller_key = :seller_key
          AND tier_month = :tier_month
    """, {
        "seller_key": seller["seller_key"],
        "tier_month": f"{month}-01"
    })

    classified = performance["classified_delivery_items"] or 0
    on_time = performance["on_time_items"] or 0

    on_time_rate = (
        round(on_time * 100 / classified, 2)
        if classified else None
    )

    return {
        "seller": seller,
        "month": month,
        "performance": performance,
        "on_time_rate_percent": on_time_rate,
        "reviews": review,
        "tier": tier
    }



# --------------------------------------------------
# 4. TOP SELLERS
# --------------------------------------------------

@app.get("/sellers/top")
def top_sellers(
    month: str = Query(..., description="Month in YYYY-MM format"),
    metric: str = Query(
        "commission_usd",
        description="commission_usd, on_time_rate, avg_review"
    ),
    limit: int = Query(10, ge=1, le=100)
):
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise HTTPException(400, "Month must be YYYY-MM")

    if metric not in ["commission_usd", "on_time_rate", "avg_review"]:
        raise HTTPException(400, "Invalid metric")

    query = """
        SELECT
            s.seller_id,
            s.city,
            s.state,
            ROUND(SUM(i.commission_usd), 2) AS commission_usd,
            ROUND(
                100.0 * SUM(
                    CASE WHEN i.seller_delivery_status = 'on_time'
                    THEN 1 ELSE 0 END
                ) / NULLIF(SUM(
                    CASE WHEN i.seller_delivery_status IN
                    ('on_time', 'seller_late', 'carrier_late')
                    THEN 1 ELSE 0 END
                ), 0), 2
            ) AS on_time_rate,
            (
                SELECT ROUND(AVG(r.review_score), 2)
                FROM bridge_seller_review b
                JOIN fact_order_review r
                    ON b.review_key = r.review_key
                JOIN fact_order ro
                    ON b.order_id = ro.order_id
                WHERE b.seller_key = s.seller_key
                  AND ro.purchase_timestamp >= :month_start
                  AND ro.purchase_timestamp < DATE_ADD(
                      :month_start, INTERVAL 1 MONTH
                  )
            ) AS avg_review
        FROM dim_seller s
        JOIN fact_order_item i ON s.seller_key = i.seller_key
        JOIN fact_order o ON i.order_id = o.order_id
        WHERE o.revenue_eligible = 1
          AND o.purchase_timestamp >= :month_start
          AND o.purchase_timestamp < DATE_ADD(
              :month_start, INTERVAL 1 MONTH
          )
        GROUP BY s.seller_key, s.seller_id, s.city, s.state
        ORDER BY
    """

    # Metric is selected from a fixed allowlist, not user SQL.
    query += f" {metric} DESC"
    query += " LIMIT :limit"

    results = fetch_all(query, {
        "month_start": f"{month}-01",
        "limit": limit
    })

    return {
        "month": month,
        "metric": metric,
        "count": len(results),
        "sellers": results
    }


# --------------------------------------------------
# 5. MONTHLY REGIONAL KPIs
# --------------------------------------------------

@app.get("/kpis/monthly")
def monthly_kpis(
    start: str = Query(..., description="Start month YYYY-MM"),
    end: str = Query(..., description="End month YYYY-MM"),
    region: str = Query(None)
):
    month_pattern = r"\d{4}-(0[1-9]|1[0-2])"

    if not re.fullmatch(month_pattern, start):
        raise HTTPException(400, "Invalid start month")

    if not re.fullmatch(month_pattern, end):
        raise HTTPException(400, "Invalid end month")

    if start > end:
        raise HTTPException(400, "Start month cannot exceed end month")

    
    query = """
        WITH order_metrics AS (
            SELECT
                DATE_FORMAT(o.purchase_timestamp, '%Y-%m') AS month,
                c.region,
                COUNT(*) AS total_orders,
                SUM(o.revenue_eligible = 1) AS eligible_orders,
                ROUND(
                    AVG(
                        CASE
                            WHEN o.revenue_eligible = 1
                            THEN o.is_on_time
                        END
                    ) * 100, 2
                ) AS order_on_time_rate_percent
            FROM fact_order o
            JOIN dim_customer c
                ON o.customer_key = c.customer_key
            WHERE o.purchase_timestamp >= :start_date
              AND o.purchase_timestamp < DATE_ADD(
                  :end_date, INTERVAL 1 MONTH
              )
              AND (:region IS NULL OR LOWER(c.region) = LOWER(:region))
            GROUP BY
                DATE_FORMAT(o.purchase_timestamp, '%Y-%m'),
                c.region
        ),
        item_metrics AS (
            SELECT
                DATE_FORMAT(o.purchase_timestamp, '%Y-%m') AS month,
                c.region,
                ROUND(SUM(
                    CASE WHEN o.revenue_eligible = 1
                    THEN i.gross_brl ELSE 0 END
                ), 2) AS gross_revenue_brl,
                ROUND(SUM(
                    CASE WHEN o.revenue_eligible = 1
                    THEN i.commission_usd ELSE 0 END
                ), 2) AS commission_usd
            FROM fact_order o
            JOIN dim_customer c
                ON o.customer_key = c.customer_key
            LEFT JOIN fact_order_item i
                ON o.order_id = i.order_id
            WHERE o.purchase_timestamp >= :start_date
              AND o.purchase_timestamp < DATE_ADD(
                  :end_date, INTERVAL 1 MONTH
              )
              AND (:region IS NULL OR LOWER(c.region) = LOWER(:region))
            GROUP BY
                DATE_FORMAT(o.purchase_timestamp, '%Y-%m'),
                c.region
        )
        SELECT
            om.month,
            om.region,
            om.total_orders,
            om.eligible_orders,
            im.gross_revenue_brl,
            im.commission_usd,
            om.order_on_time_rate_percent
        FROM order_metrics om
        LEFT JOIN item_metrics im
            ON om.month = im.month
           AND om.region = im.region
        ORDER BY om.month, om.region
    """

    params = {
        "start_date": f"{start}-01",
        "end_date": f"{end}-01",
        "region": region
    }

    results = fetch_all(query, params)


    return {
        "start": start,
        "end": end,
        "region": region,
        "results": results
    }


# --------------------------------------------------
# 6. CAMPAIGN PERFORMANCE
# --------------------------------------------------

@app.get("/campaigns/{campaign_id}/performance")
def campaign_performance(campaign_id: str):

    campaign = fetch_one("""
        SELECT
            campaign_key,
            campaign_id,
            campaign_name,
            start_date,
            end_date,
            priority
        FROM dim_campaign
        WHERE campaign_id = :campaign_id
    """, {"campaign_id": campaign_id})

    if not campaign:
        raise HTTPException(404, "Campaign not found")

    performance = fetch_one("""
        SELECT
            COUNT(i.order_item_key) AS attributed_items,
            COUNT(DISTINCT i.order_id) AS attributed_orders,
            COUNT(DISTINCT i.seller_key) AS participating_sellers,
            ROUND(SUM(i.price_brl), 2) AS item_price_brl,
            ROUND(SUM(i.gross_brl), 2) AS gross_revenue_brl,
            ROUND(SUM(i.commission_brl), 2) AS commission_brl,
            ROUND(SUM(i.commission_usd), 2) AS commission_usd
        FROM fact_order_item i
        JOIN fact_order o ON i.order_id = o.order_id
        WHERE i.campaign_key = :campaign_key
          AND o.revenue_eligible = 1
    """, {"campaign_key": campaign["campaign_key"]})

    return {
        "campaign": campaign,
        "performance": performance
    }


# --------------------------------------------------
# 7. DATA QUALITY SUMMARY
# --------------------------------------------------

@app.get("/data-quality/summary")
def data_quality_summary(run_id: int = Query(None, ge=1)):

    if run_id is not None:
        run = fetch_one("""
            SELECT *
            FROM pipeline_run
            WHERE run_id = :run_id
        """, {"run_id": run_id})

        if not run:
            raise HTTPException(404, "Pipeline run not found")

        issues = fetch_all("""
            SELECT
                rule_id,
                issue_type,
                COUNT(*) AS issue_count
            FROM data_quality_issue
            WHERE run_id = :run_id
            GROUP BY rule_id, issue_type
            ORDER BY rule_id, issue_type
        """, {"run_id": run_id})

        return {
            "run": run,
            "issues": issues
        }

    total = fetch_one("""
        SELECT COUNT(*) AS total_issues
        FROM data_quality_issue
    """)

    issues = fetch_all("""
        SELECT
            rule_id,
            issue_type,
            COUNT(*) AS issue_count
        FROM data_quality_issue
        GROUP BY rule_id, issue_type
        ORDER BY rule_id, issue_type
    """)

    return {
        "total_issues": total["total_issues"],
        "issues": issues
    }
