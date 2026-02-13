# weather_data_analyzer.py - FIXED VERSION
import psycopg2
import pandas as pd
from tabulate import tabulate
from datetime import datetime
import os
import numpy as np

class WeatherDataAnalyzer:
    def __init__(self):
        self.connection_params = {
            "dbname": "airflow",
            "user": "airflow",
            "password": "airflow",
            "host": "localhost",
            "port": "5432"
        }
        self.export_dir = "solar_analysis_data"
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
    
    def connect(self):
        return psycopg2.connect(**self.connection_params)
    
    def export_complete_weather_data(self, city="Turin"):
        """Export ALL weather data fields for comprehensive solar analysis"""
        conn = self.connect()
        
        # FIXED: Changed 'timestamp' to 'observation_time' to match your table schema
        query = """
            SELECT 
                id, city, country, region, lat, lon, local_time,
                temperature, weather_code, weather_descriptions,
                wind_speed, wind_degree, wind_dir, pressure, precip,
                humidity, cloudcover, feelslike, uv_index, visibility,
                sunrise, sunset, moon_phase, moon_illumination,
                air_quality_co, air_quality_no2, air_quality_o3,
                air_quality_so2, air_quality_pm2_5, air_quality_pm10,
                us_epa_index, gb_defra_index, observation_time  -- FIXED: was 'timestamp'
            FROM weather_data 
            WHERE city = %s
            ORDER BY observation_time  -- FIXED: was 'timestamp'
        """
        
        df = pd.read_sql_query(query, conn, params=(city,))
        conn.close()
        
        if df.empty:
            print(f"No data found for {city}")
            return None
        
        # Parse timestamps
        df['observation_time'] = pd.to_datetime(df['observation_time'])
        df['date'] = df['observation_time'].dt.date
        df['hour'] = df['observation_time'].dt.hour
        df['month'] = df['observation_time'].dt.month
        df['day_of_week'] = df['observation_time'].dt.dayofweek
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/{city.lower()}_complete_weather_{timestamp}.csv"
        
        # Save to CSV
        df.to_csv(filename, index=False)
        
        print(f"\nComplete weather data exported to: {filename}")
        print(f"Total records: {len(df)}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Fields included: {', '.join(df.columns[:10])}...")
        
        return filename
    
    def export_solar_data(self, city="Turin"):
        """Export simplified solar-relevant data"""
        conn = self.connect()
        
        # Focus on solar-relevant fields
        query = """
            SELECT 
                city,
                temperature,
                humidity,
                wind_speed,
                cloudcover,
                uv_index,
                observation_time
            FROM weather_data 
            WHERE city = %s
            ORDER BY observation_time
        """
        
        df = pd.read_sql_query(query, conn, params=(city,))
        conn.close()
        
        if df.empty:
            print(f"No data found for {city}")
            return None
        
        # Parse timestamps
        df['observation_time'] = pd.to_datetime(df['observation_time'])
        df['date'] = df['observation_time'].dt.date
        df['hour'] = df['observation_time'].dt.hour
        df['month'] = df['observation_time'].dt.month
        
        # Calculate solar potential
        df['solar_potential'] = self.calculate_solar_potential(df)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.export_dir}/{city.lower()}_solar_data_{timestamp}.csv"
        df.to_csv(filename, index=False)
        
        print(f"\nSolar analysis data exported to: {filename}")
        print(f"Total records: {len(df)}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        
        return filename
    
    def calculate_solar_potential(self, df):
        """Calculate solar energy potential based on weather conditions"""
        # Solar angle factor (simplified - based on hour)
        df['solar_angle'] = np.sin(np.radians(15 * (df['hour'] - 12)))
        df['solar_angle'] = df['solar_angle'].clip(lower=0)
        
        # Cloud factor (0-1, higher clouds = lower factor)
        df['cloud_factor'] = 1 - (df['cloudcover'] / 100)
        df['cloud_factor'] = df['cloud_factor'].clip(lower=0.1, upper=1)
        
        # Temperature efficiency (panels work better in cooler temps)
        df['temp_efficiency'] = 1 - (0.004 * (df['temperature'] - 25).clip(lower=0))
        df['temp_efficiency'] = df['temp_efficiency'].clip(lower=0.7, upper=1)
        
        # UV index factor (proxy for solar intensity)
        df['uv_factor'] = df['uv_index'] / 10
        df['uv_factor'] = df['uv_factor'].clip(lower=0, upper=1)
        
        # Combined solar potential (0-1 scale)
        df['solar_potential'] = (
            df['solar_angle'] * 
            df['cloud_factor'] * 
            df['temp_efficiency'] * 
            df['uv_factor']
        ).clip(lower=0, upper=1)
        
        return df['solar_potential']
    
    def get_statistics(self):
        """Get basic statistics from the data"""
        conn = self.connect()
        
        query = """
            SELECT 
                city,
                COUNT(*) as total_readings,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(temperature)::numeric(10,2) as avg_temp,
                AVG(humidity)::numeric(10,2) as avg_humidity,
                AVG(wind_speed)::numeric(10,2) as avg_wind_speed,
                AVG(cloudcover)::numeric(10,2) as avg_cloudcover,
                MIN(observation_time) as first_record,
                MAX(observation_time) as last_record
            FROM weather_data 
            GROUP BY city
            ORDER BY city
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        print("\n" + "=" * 60)
        print("WEATHER DATA STATISTICS")
        print("=" * 60)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        
        return df

if __name__ == "__main__":
    analyzer = WeatherDataAnalyzer()
    
    # Show statistics first
    analyzer.get_statistics()
    
    # Export data for solar analysis
    print("\n" + "=" * 60)
    csv_file = analyzer.export_solar_data(city="Turin")
    
    if csv_file:
        print(f"\nData ready for solar analysis in Jupyter!")
        print(f"Load it with:")
        print(f'    import pandas as pd')
        print(f'    df = pd.read_csv("{csv_file}")')
        print(f'    df.head()')