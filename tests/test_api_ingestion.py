# tests/test_api_ingestion.py
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ingestion.api.weatherstack_fetcher import WeatherStackFetcher
import psycopg2
from config import userdata_config as cfg

def test_api_connection():
    """Test if API is reachable"""
    print("\nTesting API Connection...")
    fetcher = WeatherStackFetcher(city="Turin")
    data = fetcher.fetch_current_weather()
    
    if data and 'current' in data:
        print(f"API Connection Successful")
        print(f"   Temperature: {data['current'].get('temperature')}°C")
        print(f"   Weather: {data['current'].get('weather_descriptions', [''])[0]}")
        return True
    else:
        print("API Connection Failed")
        return False

def test_database_connection():
    """Test if PostgreSQL is reachable"""
    print("\nTesting Database Connection...")
    try:
        conn = psycopg2.connect(**cfg.POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            print("Database Connection Successful")
            return True
    except Exception as e:
        print(f"Database Connection Failed: {e}")
        return False

def test_table_exists():
    """Test if weather_data table exists"""
    print("\nTesting Table Existence...")
    try:
        conn = psycopg2.connect(**cfg.POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'weather_data'
            )
        """)
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if exists:
            print("Table 'weather_data' exists")
            return True
        else:
            print("Table 'weather_data' does not exist")
            return False
    except Exception as e:
        print(f"Error checking table: {e}")
        return False

def test_full_pipeline():
    """Test complete API to database pipeline"""
    print("\nTesting Complete Pipeline...")
    fetcher = WeatherStackFetcher(city="Turin")
    
    # Fetch
    raw = fetcher.fetch_current_weather()
    if not raw:
        print("Fetch failed")
        return False
    
    # Transform
    transformed = fetcher.transform_weather_data(raw)
    if not transformed:
        print("Transform failed")
        return False
    
    # Save
    success = fetcher.save_to_postgres(transformed)
    if success:
        print("Full pipeline successful")
        
        # Verify
        conn = psycopg2.connect(**cfg.POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM weather_data")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"   Total records in database: {count}")
        return True
    else:
        print("Save failed")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("WEATHER API INGESTION TESTS")
    print("=" * 60)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Database Connection", test_database_connection),
        ("Table Existence", test_table_exists),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, result in results:
        status = "PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\nALL TESTS PASSED - API ingestion ready!")
    else:
        print("\nSOME TESTS FAILED - Check errors above")