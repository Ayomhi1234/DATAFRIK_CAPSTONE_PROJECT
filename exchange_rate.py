import requests
from datetime import date

API_URL = "https://api.frankfurter.dev/v2/rates"


def get_exchange_rates(start_date, end_date):
    params = {
        "base": "USD",
        "quotes": "NGN",
        "from": start_date,
        "to": end_date
    }

    response = requests.get(API_URL, params=params)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    rates = get_exchange_rates("2025-11-05", "2026-11-04")

    print(f"Total records: {len(rates)}")
    print(rates[:5])