
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

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

file_path = Path("data/internal/brazil_states_fallback.json")

with file_path.open("r", encoding="utf-8") as file:
    states = json.load(file)

if len(states) != 27:
    raise ValueError(f"Expected 27 states, found {len(states)}")

if len({state["sigla"] for state in states}) != 27:
    raise ValueError("Duplicate state codes found")

insert_query = text("""
    INSERT INTO ref_brazil_state (
        ibge_state_id,
        state_code,
        state_name,
        region_name
    )
    VALUES (
        :id,
        :sigla,
        :nome,
        :regiao
    )
    ON DUPLICATE KEY UPDATE
        state_name = VALUES(state_name),
        region_name = VALUES(region_name)
""")

with engine.begin() as conn:
    conn.execute(insert_query, states)

with engine.connect() as conn:
    total = conn.execute(
        text("SELECT COUNT(*) FROM ref_brazil_state")
    ).scalar()

    print("States loaded:", total)

    rows = conn.execute(text("""
        SELECT state_code, state_name, region_name
        FROM ref_brazil_state
        ORDER BY state_code
    """)).fetchall()

    for row in rows:
        print(row)

print("\nR17 state reference loading completed!")
