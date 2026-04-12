import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from ingestion.api.weatherstack_fetcher import WeatherStackFetcher


def test_transform_weather_data_maps_expected_fields():
    fetcher = WeatherStackFetcher(city="Turin")
    raw = {
        "location": {"name": "Turin"},
        "current": {
            "temperature": 24,
            "humidity": 55,
            "wind_speed": 12,
            "wind_dir": "NW",
            "pressure": 1012,
            "precip": 0.0,
            "cloudcover": 30,
            "uv_index": 6,
            "weather_code": 113,
            "weather_descriptions": ["Sunny"],
            "is_day": "yes",
            "observation_time": "07:34 PM",
        },
    }

    transformed = fetcher.transform_weather_data(raw)

    assert transformed is not None
    assert transformed["city"] == "Turin"
    assert transformed["temperature"] == 24
    assert transformed["weather_description"] == "Sunny"
    assert transformed["is_day"] is True
    assert transformed["observation_time"] is not None


def test_transform_weather_data_handles_missing_current_block():
    fetcher = WeatherStackFetcher(city="Turin")
    assert fetcher.transform_weather_data({}) is None
