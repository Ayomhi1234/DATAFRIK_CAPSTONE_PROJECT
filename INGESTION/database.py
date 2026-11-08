
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

# Load environment variables from .env file
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

# Retrieve the NEON connection string
DATABASE_URL = os.getenv('DATABASE_URL')

# Stop the execution if the connection string is missing
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables.")

# Specify psycopg2 as the PostgreSQL driver
DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+psycopg2://",
    1
)

# Create a SQLAlchemy database engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


def test_connection():

    # Establish a connection and check the database
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT current_database()")
        )

        database_name = result.scalar()

        print("Connection successful!")
        print(f"Connected to database: {database_name}")


def create_stock_prices_table():

    # Define the structure of the stock_prices table
    create_table_query = """
        CREATE TABLE IF NOT EXISTS stock_prices (
            date TIMESTAMPTZ NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            open NUMERIC(18, 6),
            high NUMERIC(18, 6),
            low NUMERIC(18, 6),
            close NUMERIC(18, 6),
            volume BIGINT,
            dividends NUMERIC(18, 6),
            stock_splits NUMERIC(18, 6),

            PRIMARY KEY (date, ticker)
        );
    """

    # Execute the query to create the table
    with engine.begin() as conn:
        conn.execute(text(create_table_query))

    print("Table 'stock_prices' created successfully.")


def load_stock_prices():

    # Locate the existing CSV file in the project root
    csv_path = Path(__file__).resolve().parent.parent / "stock_prices.csv"

    # Read stock prices from the CSV file
    stock_prices = pd.read_csv(csv_path)

    # Convert the Date column to timezone-aware datetime
    stock_prices["Date"] = pd.to_datetime(
        stock_prices["Date"],
        utc=True
    )

    # Rename columns to match the Neon table structure
    stock_prices = stock_prices.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "Dividends": "dividends",
        "Stock Splits": "stock_splits"
    })

    # Insert stock prices into Neon
    stock_prices.to_sql(
        name="stock_prices",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500
    )

    print(f"Successfully loaded {len(stock_prices)} records into Neon.")


if __name__ == "__main__":
    test_connection()
    create_stock_prices_table()
    load_stock_prices()
