# ingestion/api/weatherstack_fetcher.py
import requests
import psycopg2
from datetime import datetime
import time
import logging
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import userdata_config as cfg

# Configure logging
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
        """Fetch current weather from WeatherStack API"""
        try:
            url = f"{self.base_url}{self.api_config['endpoints']['current']}"
            params = {
                'access_key': self.access_key,
                'query': self.city
            }
            
            logger.info(f"Fetching weather data for {self.city}...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                logger.error(f"API Error: {data['error']['info']}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
    
    def transform_weather_data(self, raw_data):
        """Transform API response to database format"""
        if not raw_data or 'current' not in raw_data:
            return None
            
        current = raw_data['current']
        location = raw_data.get('location', {})
        
        # Fix: Parse the observation_time correctly
        obs_time = current.get('observation_time')  # Format: "07:34 PM"
        
        # Convert to proper timestamp
        if obs_time:
            # Get today's date and combine with the time
            today = datetime.now().date()
            # Parse the time string
            time_obj = datetime.strptime(obs_time, "%I:%M %p").time()
            # Combine with today's date
            full_timestamp = datetime.combine(today, time_obj)
        else:
            full_timestamp = datetime.now()
        
        return {
            'city': location.get('name', self.city),
            'timestamp': datetime.now(),
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
            'observation_time': full_timestamp  # Now it's a proper timestamp
    }
    
    def save_to_postgres(self, data):
        """Save transformed data to PostgreSQL"""
        if not data:
            return False
            
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            insert_query = """
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
            """
            
            cur.execute(insert_query, data)
            conn.commit()
            
            logger.info(f"Weather data saved for {data['city']}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving to PostgreSQL: {e}")
            # Log the data that caused the error for debugging
            logger.debug(f"Problematic data: {data}")
            return False
    
    def run_once(self):
        """Run one fetch and save cycle"""
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
        """Run continuously at specified interval"""
        logger.info(f"Starting continuous fetch every {interval_minutes} minutes")
        
        try:
            while True:
                self.run_once()
                logger.info(f"Waiting {interval_minutes} minutes until next fetch...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Stopping weather fetcher")

if __name__ == "__main__":
    # Parse command line arguments
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