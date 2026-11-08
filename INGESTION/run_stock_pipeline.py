
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from stock_prices import fetch_stock_prices


# Load environment variables from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing.")

# Use psycopg2 as the PostgreSQL driver
DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+psycopg2://",
    1
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def load_stock_prices():
    """Fetch stock prices and safely upsert them into Neon."""

    # Fetch the latest five days of stock prices
    stock_prices = fetch_stock_prices()

    if stock_prices is None or stock_prices.empty:
        raise ValueError("No stock prices were retrieved.")

    # Prepare the dataframe
    stock_prices["Date"] = pd.to_datetime(
        stock_prices["Date"],
        utc=True
    )

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

    # Keep only the database columns
    columns = [
        "date", "ticker", "open", "high", "low",
        "close", "volume", "dividends", "stock_splits"
    ]

    stock_prices = stock_prices[columns]

    # Create a temporary staging table
    with engine.begin() as conn:

        stock_prices.to_sql(
            "stock_prices_staging",
            con=conn,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=500
        )

        # Insert new records and update existing records
        conn.execute(text("""
            INSERT INTO public.stock_prices (
                date, ticker, open, high, low,
                close, volume, dividends, stock_splits
            )
            SELECT
                date, ticker, open, high, low,
                close, volume, dividends, stock_splits
            FROM public.stock_prices_staging
            ON CONFLICT (date, ticker)
            DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                dividends = EXCLUDED.dividends,
                stock_splits = EXCLUDED.stock_splits;
        """))

        # Remove the temporary staging table
        conn.execute(text("""
            DROP TABLE IF EXISTS public.stock_prices_staging;
        """))

        # Refresh the warehouse stock prices table
        conn.execute(text("""
            INSERT INTO warehouse.stock_prices (
                date, ticker, open, high, low,
                close, volume, dividends, stock_splits
            )
            SELECT
                date::DATE, ticker, open, high, low,
                close, volume, dividends, stock_splits
            FROM public.stock_prices
            ON CONFLICT (date, ticker)
            DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                dividends = EXCLUDED.dividends,
                stock_splits = EXCLUDED.stock_splits;
        """))

    print(
        f"Successfully processed {len(stock_prices)} stock records."
    )


if __name__ == "__main__":
    load_stock_prices()
