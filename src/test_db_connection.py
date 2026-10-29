
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

connection_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(connection_url, pool_pre_ping=True)

try:
    with engine.connect() as connection:
        version = connection.execute(
            text("SELECT VERSION()")
        ).scalar_one()

        database = connection.execute(
            text("SELECT DATABASE()")
        ).scalar_one()

        print("MySQL connection successful!")
        print("Server version:", version)
        print("Database:", database)
except Exception as error:
    print("MySQL connection failed.")
    print("Error:", error)
finally:
    engine.dispose()
