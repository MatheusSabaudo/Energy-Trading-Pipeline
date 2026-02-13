from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2
import psycopg2.extras
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("WEATHERSTACK_API_KEY", "YOUR_API_KEY")
CITIES = ["Turin"]

def create_table():
    """Create table with error handling and logging"""
    try:
        conn = psycopg2.connect(
            dbname="airflow",
            user="airflow",
            password="airflow",
            host="postgres"
        )
        cursor = conn.cursor()
        
        # Drop the table if it exists
        cursor.execute("DROP TABLE IF EXISTS weather_data CASCADE;")
        
        # Create table with new schema
        cursor.execute("""
            CREATE TABLE weather_data (
                id SERIAL PRIMARY KEY,
                city VARCHAR(100),
                country VARCHAR(100),
                region VARCHAR(100),
                lat DECIMAL(10,6),
                lon DECIMAL(10,6),
                local_time TIMESTAMP,        
                temperature DECIMAL(5,2),
                weather_code INT,
                weather_descriptions TEXT,
                wind_speed INT,
                wind_degree INT,
                wind_dir VARCHAR(10),
                pressure INT,
                precip DECIMAL(5,1),
                humidity INT,
                cloudcover INT,
                feelslike INT,
                uv_index INT,
                visibility INT,
                sunrise VARCHAR(20),
                sunset VARCHAR(20),
                moon_phase VARCHAR(50),
                moon_illumination INT,
                air_quality_co DECIMAL(10,2),
                air_quality_no2 DECIMAL(10,2),
                air_quality_o3 DECIMAL(10,2),
                air_quality_so2 DECIMAL(10,2),
                air_quality_pm2_5 DECIMAL(10,2),
                air_quality_pm10 DECIMAL(10,2),
                us_epa_index INT,
                gb_defra_index INT,
                observation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Table created successfully")
        
    except Exception as e:
        logger.error(f"Error creating table: {str(e)}")
        raise e

def fetch_weather():
    """Fetch weather data with safe field extraction"""
    results = []
    for city in CITIES:
        try:
            url = f"http://api.weatherstack.com/current?access_key={API_KEY}&query={city}"
            logger.info(f"Fetching data for {city}...")
            
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "error" in data:
                logger.error(f"API Error for {city}: {data['error'].get('info', 'Unknown error')}")
                continue
            
            # Safely extract all fields with defaults
            location = data.get('location', {})
            current = data.get('current', {})
            astro = current.get('astro', {})
            air_quality = current.get('air_quality', {})
            
            weather_data = {
                # Basic fields (always present)
                "city": city,
                "temperature": current.get('temperature', 0),
                "humidity": current.get('humidity', 0),
                "wind_speed": current.get('wind_speed', 0),
                
                # Location fields
                "country": location.get('country', ''),
                "region": location.get('region', ''),
                "lat": location.get('lat', 0),
                "lon": location.get('lon', 0),
                "local_time": location.get('localtime', ''),  # Changed to match column name
                
                # Weather fields
                "weather_code": current.get('weather_code', 0),
                "weather_descriptions": str(current.get('weather_descriptions', [''])[0]),
                "wind_degree": current.get('wind_degree', 0),
                "wind_dir": current.get('wind_dir', ''),
                "pressure": current.get('pressure', 0),
                "precip": float(current.get('precip', 0)),
                "cloudcover": current.get('cloudcover', 0),
                "feelslike": current.get('feelslike', 0),
                "uv_index": current.get('uv_index', 0),
                "visibility": current.get('visibility', 0),
                
                # Astro fields
                "sunrise": astro.get('sunrise', ''),
                "sunset": astro.get('sunset', ''),
                "moon_phase": astro.get('moon_phase', ''),
                "moon_illumination": int(astro.get('moon_illumination', 0)),
                
                # Air quality fields (may be None on free tier)
                "air_quality_co": float(air_quality.get('co', 0)) if air_quality else 0,
                "air_quality_no2": float(air_quality.get('no2', 0)) if air_quality else 0,
                "air_quality_o3": float(air_quality.get('o3', 0)) if air_quality else 0,
                "air_quality_so2": float(air_quality.get('so2', 0)) if air_quality else 0,
                "air_quality_pm2_5": float(air_quality.get('pm2_5', 0)) if air_quality else 0,
                "air_quality_pm10": float(air_quality.get('pm10', 0)) if air_quality else 0,
                "us_epa_index": int(air_quality.get('us-epa-index', 0)) if air_quality else 0,
                "gb_defra_index": int(air_quality.get('gb-defra-index', 0)) if air_quality else 0
            }
            
            results.append(weather_data)
            logger.info(f"Successfully fetched data for {city}")
            
        except Exception as e:
            logger.error(f"Error fetching data for {city}: {str(e)}")
            continue
            
    return results

def insert_weather():
    """Insert weather data with all fields"""
    try:
        conn = psycopg2.connect(
            dbname="airflow",
            user="airflow",
            password="airflow",
            host="postgres"
        )
        cursor = conn.cursor()
        weather_data = fetch_weather()
        
        for data in weather_data:
            cursor.execute("""
                INSERT INTO weather_data (
                    city, country, region, lat, lon, local_time, temperature,
                    weather_code, weather_descriptions, wind_speed, wind_degree,
                    wind_dir, pressure, precip, humidity, cloudcover, feelslike,
                    uv_index, visibility, sunrise, sunset, moon_phase,
                    moon_illumination, air_quality_co, air_quality_no2,
                    air_quality_o3, air_quality_so2, air_quality_pm2_5,
                    air_quality_pm10, us_epa_index, gb_defra_index
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                data['city'], data['country'], data['region'], data['lat'], 
                data['lon'], data['local_time'], data['temperature'],
                data['weather_code'], data['weather_descriptions'], data['wind_speed'],
                data['wind_degree'], data['wind_dir'], data['pressure'],
                data['precip'], data['humidity'], data['cloudcover'],
                data['feelslike'], data['uv_index'], data['visibility'],
                data['sunrise'], data['sunset'], data['moon_phase'],
                data['moon_illumination'], data['air_quality_co'],
                data['air_quality_no2'], data['air_quality_o3'],
                data['air_quality_so2'], data['air_quality_pm2_5'],
                data['air_quality_pm10'], data['us_epa_index'],
                data['gb_defra_index']
            ))
        
        conn.commit()
        logger.info(f"Inserted {len(weather_data)} records successfully")
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        raise e

# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2026, 2, 13),
}

with DAG(
    'weather_etl_complete',
    default_args=default_args,
    description='Complete weather ETL with all API fields',
    schedule_interval='@hourly',
    catchup=False,
    tags=['weather', 'solar']
) as dag:

    create_table_task = PythonOperator(
        task_id='create_table',
        python_callable=create_table
    )
    
    load_weather_task = PythonOperator(
        task_id='load_weather',
        python_callable=insert_weather
    )
    
    create_table_task >> load_weather_task