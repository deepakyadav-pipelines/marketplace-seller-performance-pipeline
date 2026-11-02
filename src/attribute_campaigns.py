
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

load_dotenv()

DB_URL = URL.create(
    "mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME", "marketplace_db"),
)

engine = create_engine(DB_URL, pool_pre_ping=True)
SAO_PAULO = ZoneInfo("America/Sao_Paulo")


def to_sao_paulo(value):
    """Treat naive Olist timestamps as Sao Paulo local time."""
    if pd.isna(value):
        return None

    timestamp = pd.Timestamp(value)

    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(
            SAO_PAULO,
            ambiguous=False,
            nonexistent="shift_forward"
        )
    else:
        timestamp = timestamp.tz_convert(SAO_PAULO)

    return timestamp.tz_localize(None).to_pydatetime()



def main():
    with engine.connect() as conn:
        items = pd.read_sql(text("""
            SELECT
                i.order_id,
                i.order_item_id,
                i.product_key,
                o.purchase_timestamp,
                c.state AS customer_state,
                c.region AS customer_region,
                p.category_name_english
            FROM fact_order_item i
            JOIN fact_order o
                ON i.order_id = o.order_id
            JOIN dim_customer c
                ON o.customer_key = c.customer_key
            JOIN dim_product p
                ON i.product_key = p.product_key
            WHERE o.purchase_timestamp IS NOT NULL
        """), conn)

        campaigns = pd.read_sql(text("""
            SELECT
                campaign_key,
                campaign_id,
                start_date,
                end_date,
                priority
            FROM dim_campaign
        """), conn)

        targets = pd.read_sql(text("""
            SELECT campaign_key, target_type, target_value
            FROM bridge_campaign_target
        """), conn)

    if items.empty:
        print("No order items found.")
        return

    items["purchase_local"] = items["purchase_timestamp"].apply(
        to_sao_paulo
    )

    items["customer_state"] = (
        items["customer_state"].fillna("").str.strip().str.upper()
    )
    items["customer_region"] = (
        items["customer_region"].fillna("").str.strip()
    )
    items["category_name_english"] = (
        items["category_name_english"].fillna("").str.strip().str.lower()
    )

    # Build a lookup of targets for every campaign.
    target_lookup = {}
    for campaign_key, group in targets.groupby("campaign_key"):
        target_lookup[campaign_key] = {
            target_type: set(group.loc[
                group["target_type"] == target_type, "target_value"
            ].str.strip().str.lower())
            for target_type in ["STATE", "REGION", "CATEGORY"]
        }

    campaign_records = campaigns.to_dict("records")
    campaign_by_key = {
        row["campaign_key"]: row for row in campaign_records
    }

    def matches(item, campaign):
        campaign_key = campaign["campaign_key"]
        target = target_lookup.get(campaign_key, {})

        purchase_time = item["purchase_local"]
        if purchase_time is None:
            return False

        if not (campaign["start_date"] <= purchase_time <= campaign["end_date"]):
            return False

        states = target.get("STATE", set())
        regions = target.get("REGION", set())
        categories = target.get("CATEGORY", set())

        state_match = (
            "all" in states
            or item["customer_state"].lower() in states
        )
        region_match = (
            "all" in regions
            or item["customer_region"].lower() in regions
        )
        category_match = (
            "all" in categories
            or item["category_name_english"] in categories
        )

        # At least one geographic target and one category target
        # must match.
        geography_match = state_match or region_match

        return geography_match and category_match

    assignments = []

    for item in items.to_dict("records"):
        matching = [
            campaign
            for campaign in campaign_records
            if matches(item, campaign)
        ]

        if matching:
            # Highest priority, then latest start date.
            # campaign_id is a deterministic final tie-breaker.
            selected = sorted(
                matching,
                key=lambda x: (
                    -int(x["priority"]),
                    -x["start_date"].timestamp(),
                    x["campaign_id"],
                ),
            )[0]

            campaign_key = selected["campaign_key"]
        else:
            campaign_key = None

        assignments.append({
            "order_id": item["order_id"],
            "order_item_id": item["order_item_id"],
            "campaign_key": campaign_key,
        })

    # Update fact_order_item in batches.
    update_sql = text("""
        UPDATE fact_order_item
        SET campaign_key = :campaign_key
        WHERE order_id = :order_id
          AND order_item_id = :order_item_id
    """)

    batch_size = 5000

    with engine.begin() as conn:
        for start in range(0, len(assignments), batch_size):
            batch = assignments[start:start + batch_size]
            conn.execute(update_sql, batch)

    assigned = sum(
        1 for row in assignments if row["campaign_key"] is not None
    )
    unmatched = len(assignments) - assigned

    print(f"Total items processed: {len(assignments)}")
    print(f"Campaign-attributed items: {assigned}")
    print(f"Items without campaign: {unmatched}")

    with engine.connect() as conn:
        print("\nCampaign attribution summary:")
        summary = conn.execute(text("""
            SELECT
                c.campaign_id,
                c.campaign_name,
                COUNT(i.order_item_key) AS attributed_items
            FROM dim_campaign c
            LEFT JOIN fact_order_item i
                ON c.campaign_key = i.campaign_key
            GROUP BY c.campaign_key, c.campaign_id, c.campaign_name
            ORDER BY c.campaign_id
        """))

        for row in summary:
            print(row)

        print("\nTotal attributed items in MySQL:")
        total = conn.execute(text("""
            SELECT COUNT(*)
            FROM fact_order_item
            WHERE campaign_key IS NOT NULL
        """)).scalar_one()

        print(total)


if __name__ == "__main__":
    main()
