
import sys
import requests

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.models import ConnectorSpecification
from airbyte_cdk.entrypoint import launch


# Frankfurter exchange rate stream
class ExchangeRateStream(HttpStream):

    url_base = "https://api.frankfurter.dev/v2/"
    primary_key = ["date", "base", "quote"]

    def __init__(self, config):
        super().__init__()
        self.config = config

    # API endpoint
    def path(self, **kwargs):
        return "rates"

    # API request parameters
    def request_params(self, stream_state=None, **kwargs):
        return {
            "base": self.config["base"],
            "quotes": self.config["quote"],
            "from": self.config["start_date"],
            "to": self.config["end_date"]
        }

    # Extract exchange rate records
    def parse_response(self, response, **kwargs):
        yield from response.json()

    # No pagination required
    def next_page_token(self, response):
        return None

    # Exchange rate data schema
    def get_json_schema(self):
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "date": {"type": "string"},
                "base": {"type": "string"},
                "quote": {"type": "string"},
                "rate": {"type": "number"}
            },
            "required": ["date", "base", "quote", "rate"]
        }


# Airbyte source connector
class SourceExchangeRate(AbstractSource):

    # Connector configuration
    def spec(self, logger):
        return ConnectorSpecification(
            connectionSpecification={
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "required": ["base", "quote", "start_date", "end_date"],
                "properties": {
                    "base": {"type": "string", "default": "USD"},
                    "quote": {"type": "string", "default": "NGN"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"}
                }
            }
        )

    # Test API connection
    def check_connection(self, logger, config):
        try:
            response = requests.get(
                "https://api.frankfurter.dev/v2/rates",
                params={
                    "base": config["base"],
                    "quotes": config["quote"],
                    "from": config["start_date"],
                    "to": config["end_date"]
                },
                timeout=30
            )

            response.raise_for_status()
            return True, None

        except Exception as error:
            return False, str(error)

    # Register the exchange rate stream
    def streams(self, config):
        return [ExchangeRateStream(config)]


# Run the Airbyte connector
if __name__ == "__main__":
    launch(SourceExchangeRate(), sys.argv[1:])
