import os
import time
import requests

from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# Load project environment variables
load_dotenv()

# Airbyte credentials from GitHub Actions secrets
CLIENT_ID = os.getenv("AIRBYTE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AIRBYTE_CLIENT_SECRET")
TRADES_CONNECTION_ID = os.getenv("AIRBYTE_TRADES_CONNECTION_ID")
FX_CONNECTION_ID = os.getenv("AIRBYTE_FX_CONNECTION_ID")

# Neon database connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not all([
    CLIENT_ID,
    CLIENT_SECRET,
    TRADES_CONNECTION_ID,
    FX_CONNECTION_ID,
    DATABASE_URL
]):
    raise ValueError("One or more required environment variables are missing.")

# Convert the URL if it uses SQLAlchemy's psycopg2 driver notation
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg2://",
        1
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

AIRBYTE_URL = "https://api.airbyte.com/v1"
session = requests.Session()

access_token = None
token_expiry = 0


def get_access_token():
    """Obtain or refresh the Airbyte API access token."""
    global access_token, token_expiry

    if access_token and time.time() < token_expiry - 60:
        return access_token

    response = session.post(
        f"{AIRBYTE_URL}/applications/token",
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant-type": "client_credentials"
        },
        headers={"accept": "application/json"},
        timeout=30
    )

    response.raise_for_status()

    token_data = response.json()
    access_token = token_data["access_token"]
    token_expiry = time.time() + token_data.get("expires_in", 900)

    return access_token


def airbyte_request(method, endpoint, **kwargs):
    """Make an authenticated Airbyte API request."""
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {get_access_token()}"
    headers["Accept"] = "application/json"

    response = session.request(
        method,
        f"{AIRBYTE_URL}{endpoint}",
        headers=headers,
        timeout=60,
        **kwargs
    )

    # Refresh the token once if Airbyte rejects it
    if response.status_code == 401:
        global access_token
        access_token = None
        headers["Authorization"] = f"Bearer {get_access_token()}"

        response = session.request(
            method,
            f"{AIRBYTE_URL}{endpoint}",
            headers=headers,
            timeout=60,
            **kwargs
        )

    response.raise_for_status()
    return response.json()


def run_airbyte_sync(connection_id, connection_name):
    """Trigger a sync and wait until Airbyte finishes."""
    print(f"\nStarting Airbyte sync: {connection_name}")

    job = airbyte_request(
        "POST",
        "/jobs",
        json={
            "connectionId": connection_id,
            "jobType": "sync"
        }
    )

    job_id = job["jobId"]
    print(f"Airbyte job ID: {job_id}")

    start_time = time.time()
    timeout_seconds = 3600

    while time.time() - start_time < timeout_seconds:
        result = airbyte_request("GET", f"/jobs/{job_id}")
        status = result.get("status", "").lower()

        print(f"{connection_name} status: {status}")

        if status == "succeeded":
            print(f"{connection_name} sync completed successfully.")
            return

        if status in ["failed", "cancelled", "incomplete"]:
            raise RuntimeError(
                f"{connection_name} sync ended with status: {status}"
            )

        time.sleep(20)

    raise TimeoutError(f"{connection_name} sync timed out.")


def load_airbyte_data_into_warehouse():
    """Upsert raw Airbyte records into the warehouse schema."""

    print("\nLoading trade records into warehouse...")

    trades_sql = text("""
        INSERT INTO warehouse.trades (
            trade_id,
            trade_date,
            ticker,
            shares_bought,
            price_paid_usd
        )
        SELECT
            TRIM(id::text),
            CAST(date AS DATE),
            UPPER(TRIM(ticker)),
            CAST(shares_bought AS INTEGER),
            CAST(price_paid_usd AS NUMERIC)
        FROM public."Trade_sheet"
        WHERE id IS NOT NULL
          AND date IS NOT NULL
          AND ticker IS NOT NULL
        ON CONFLICT (trade_id)
        DO UPDATE SET
            trade_date = EXCLUDED.trade_date,
            ticker = EXCLUDED.ticker,
            shares_bought = EXCLUDED.shares_bought,
            price_paid_usd = EXCLUDED.price_paid_usd;
    """)

    print("Loading exchange-rate records into warehouse...")

    exchange_rates_sql = text("""
        INSERT INTO warehouse.exchange_rates (
            date,
            base,
            quote,
            rate
        )
        SELECT
            CAST(date AS DATE),
            UPPER(TRIM(base)),
            UPPER(TRIM(quote)),
            CAST(rate AS NUMERIC)
        FROM public.exchange_rate_stream
        WHERE date IS NOT NULL
          AND base IS NOT NULL
          AND quote IS NOT NULL
          AND rate IS NOT NULL
        ON CONFLICT (date, base, quote)
        DO UPDATE SET
            rate = EXCLUDED.rate;
    """)

    with engine.begin() as connection:
        connection.execute(trades_sql)
        connection.execute(exchange_rates_sql)

    print("Trade and exchange-rate warehouse tables updated.")


if __name__ == "__main__":

    # Sync both Airbyte connections
    run_airbyte_sync(
        TRADES_CONNECTION_ID,
        "Google Sheets Trade Log"
    )

    run_airbyte_sync(
        FX_CONNECTION_ID,
        "Frankfurter USD/NGN"
    )

    # Transfer the new raw records into the warehouse
    load_airbyte_data_into_warehouse()

    print("\nAirbyte ingestion and warehouse loading completed.")
    