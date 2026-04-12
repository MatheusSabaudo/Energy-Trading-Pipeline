# FETCH DATA FROM THE API

import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import requests

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import userdata_config as cfg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeatherStackFetcher:
    def __init__(self, city="Turin"):
        self.city = city
        self.api_config = cfg.API_CONFIG['weatherstack']
        self.db_config = cfg.POSTGRES_CONFIG
        self.base_url = self.api_config['base_url']
        self.access_key = self.api_config['access_key']

    def fetch_current_weather(self):
        if not self.access_key:
            logger.error("WeatherStack access key is not configured")
            return None

        try:
            url = f"{self.base_url}{self.api_config['endpoints']['current']}"
            params = {
                'access_key': self.access_key,
                'query': self.city,
            }

            logger.info("Fetching weather data for %s...", self.city)
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            if 'error' in data:
                logger.error("API Error: %s", data['error']['info'])
                return None
            return data

        except requests.exceptions.RequestException as exc:
            logger.error("Error fetching weather data: %s", exc)
            return None

    def transform_weather_data(self, raw_data):
        if not raw_data or 'current' not in raw_data:
            return None

        current = raw_data['current']
        location = raw_data.get('location', {})
        obs_time = current.get('observation_time')

        if obs_time:
            try:
                today = datetime.now(timezone.utc).date()
                time_obj = datetime.strptime(obs_time, "%I:%M %p").time()
                full_timestamp = datetime.combine(today, time_obj, tzinfo=timezone.utc)
            except ValueError:
                logger.warning("Unexpected observation_time format: %s", obs_time)
                full_timestamp = datetime.now(timezone.utc)
        else:
            full_timestamp = datetime.now(timezone.utc)

        return {
            'city': location.get('name', self.city),
            'timestamp': datetime.now(timezone.utc),
            'temperature': current.get('temperature'),
            'humidity': current.get('humidity'),
            'wind_speed': current.get('wind_speed'),
            'wind_direction': current.get('wind_dir'),
            'pressure': current.get('pressure'),
            'precipitation': current.get('precip'),
            'cloud_cover': current.get('cloudcover'),
            'uv_index': current.get('uv_index'),
            'weather_code': current.get('weather_code'),
            'weather_description': current.get('weather_descriptions', [''])[0],
            'is_day': current.get('is_day') == 'yes',
            'observation_time': full_timestamp,
        }

    def save_to_postgres(self, data):
        if not data:
            return False

        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO weather_data (
                            city, timestamp, temperature, humidity, wind_speed,
                            wind_direction, pressure, precipitation, cloud_cover,
                            uv_index, weather_code, weather_description, is_day,
                            observation_time
                        ) VALUES (
                            %(city)s, %(timestamp)s, %(temperature)s, %(humidity)s,
                            %(wind_speed)s, %(wind_direction)s, %(pressure)s,
                            %(precipitation)s, %(cloud_cover)s, %(uv_index)s,
                            %(weather_code)s, %(weather_description)s, %(is_day)s,
                            %(observation_time)s
                        )
                        """,
                        data,
                    )

            logger.info("Weather data saved for %s", data['city'])
            return True

        except Exception as exc:
            logger.error("Error saving to PostgreSQL: %s", exc)
            logger.debug("Problematic data: %s", data)
            return False

    def run_once(self):
        logger.info("=" * 60)
        logger.info("Starting WeatherStack API fetch")

        raw_data = self.fetch_current_weather()
        if raw_data:
            transformed = self.transform_weather_data(raw_data)
            if transformed:
                self.save_to_postgres(transformed)
                logger.info("Weather data fetch complete")
            else:
                logger.error("Failed to transform weather data")
        else:
            logger.error("Failed to fetch weather data")

    def run_continuous(self, interval_minutes=15):
        logger.info("Starting continuous fetch every %s minutes", interval_minutes)
        try:
            while True:
                self.run_once()
                logger.info("Waiting %s minutes until next fetch...", interval_minutes)
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            logger.info("Stopping weather fetcher")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='WeatherStack API Fetcher')
    parser.add_argument('--city', default='Turin', help='City to fetch weather for')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=15, help='Interval in minutes')

    args = parser.parse_args()

    fetcher = WeatherStackFetcher(city=args.city)

    if args.continuous:
        fetcher.run_continuous(interval_minutes=args.interval)
    else:
        fetcher.run_once()
