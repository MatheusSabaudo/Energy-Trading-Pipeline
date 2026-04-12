"""Compatibility wrapper for API-to-Postgres ingestion."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from ingestion.api.weatherstack_fetcher import WeatherStackFetcher


def main():
    fetcher = WeatherStackFetcher()
    fetcher.run_once()


if __name__ == "__main__":
    main()
