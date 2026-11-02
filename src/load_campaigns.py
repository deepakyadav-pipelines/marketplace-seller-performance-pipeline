
import json
import os
from datetime import datetime, time, timedelta
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


def parse_campaign_datetime(value, is_end=False, date_format=None):
    """Convert campaign dates to naive Sao Paulo local datetimes."""

    if date_format:
        parsed = datetime.strptime(value, "%d/%m/%Y").date()
        parsed_time = time(23, 59, 59) if is_end else time(0, 0, 0)
        return datetime.combine(parsed, parsed_time)

    # Date-only values are Sao Paulo local dates.
    if len(value) == 10:
        parsed = datetime.strptime(value, "%Y-%m-%d").date()
        parsed_time = time(23, 59, 59) if is_end else time(0, 0, 0)
        return datetime.combine(parsed, parsed_time)

    # ISO timestamps with Z/offset are converted to Sao Paulo.
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(SAO_PAULO).replace(tzinfo=None)

    return parsed


def main():
    campaign_path = "data/internal/campaigns.json"

    with open(campaign_path, "r", encoding="utf-8") as file:
        campaigns = json.load(file)

    campaign_count = 0
    target_count = 0

    with engine.begin() as conn:
        for campaign in campaigns:
            start_date = parse_campaign_datetime(
                campaign["start"],
                date_format=campaign.get("date_format")
            )

            end_date = parse_campaign_datetime(
                campaign["end"],
                is_end=True,
                date_format=campaign.get("date_format")
            )

            if end_date < start_date:
                raise ValueError(
                    f"Invalid date range for {campaign['campaign_id']}"
                )

            conn.execute(
                text("""
                    INSERT INTO dim_campaign
                    (campaign_id, campaign_name, start_date, end_date, priority)
                    VALUES
                    (:campaign_id, :campaign_name, :start_date, :end_date, :priority)
                    ON DUPLICATE KEY UPDATE
                        campaign_name = VALUES(campaign_name),
                        start_date = VALUES(start_date),
                        end_date = VALUES(end_date),
                        priority = VALUES(priority)
                """),
                {
                    "campaign_id": campaign["campaign_id"],
                    "campaign_name": campaign["name"],
                    "start_date": start_date,
                    "end_date": end_date,
                    "priority": campaign["priority"],
                },
            )

            campaign_key = conn.execute(
                text("""
                    SELECT campaign_key
                    FROM dim_campaign
                    WHERE campaign_id = :campaign_id
                """),
                {"campaign_id": campaign["campaign_id"]},
            ).scalar_one()

            targets = []

            for state in campaign.get("target_states", []):
                targets.append(("STATE", state.upper()))

            for region in campaign.get("target_regions", []):
                targets.append(("REGION", region))

            for category in campaign.get("categories", []):
                targets.append(("CATEGORY", category.lower()))

            for target_type, target_value in targets:
                conn.execute(
                    text("""
                        INSERT INTO bridge_campaign_target
                        (campaign_key, target_type, target_value)
                        VALUES
                        (:campaign_key, :target_type, :target_value)
                        ON DUPLICATE KEY UPDATE
                            target_value = VALUES(target_value)
                    """),
                    {
                        "campaign_key": campaign_key,
                        "target_type": target_type,
                        "target_value": target_value,
                    },
                )
                target_count += 1

            campaign_count += 1

    print(f"Campaigns loaded: {campaign_count}")
    print(f"Campaign targets processed: {target_count}")

    with engine.connect() as conn:
        print("\nCampaign verification:")
        rows = conn.execute(text("""
            SELECT campaign_id, campaign_name,
                   start_date, end_date, priority
            FROM dim_campaign
            ORDER BY campaign_id
        """))

        for row in rows:
            print(row)

        print("\nTarget verification:")
        rows = conn.execute(text("""
            SELECT c.campaign_id, t.target_type, t.target_value
            FROM bridge_campaign_target t
            JOIN dim_campaign c
              ON c.campaign_key = t.campaign_key
            ORDER BY c.campaign_id, t.target_type, t.target_value
        """))

        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
