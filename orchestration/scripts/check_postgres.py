#!/usr/bin/env python3
"""
PostgreSQL Health Check Script
Checks if PostgreSQL is running and tables exist
Works both inside Docker containers and on host machine
"""

import sys
import socket
import psycopg2
from psycopg2 import OperationalError

def is_running_in_docker():
    """Detect if we're running inside a Docker container"""
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        # Check for Docker-specific env var
        if 'DOCKER_CONTAINER' in os.environ:
            return True
        return False

# Set the correct host based on environment
IN_DOCKER = is_running_in_docker()

# Database configuration - different hosts for different environments
DB_CONFIG = {
    'host': 'postgres' if IN_DOCKER else 'localhost',
    'port': 5432,
    'user': 'airflow',
    'password': 'airflow',
    'database': 'solar_data'
}

print(f"Running {'inside Docker' if IN_DOCKER else 'on host machine'}")
print(f"Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")

def check_connection():
    """Check if PostgreSQL is reachable"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print(f"PostgreSQL connection successful")
        return True
    except OperationalError as e:
        print(f"PostgreSQL connection failed: {e}")
        return False

def check_database_exists():
    """Check if solar_data database exists"""
    try:
        # Connect to default postgres database to check
        config = DB_CONFIG.copy()
        config['database'] = 'postgres'
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'solar_data'")
        exists = cur.fetchone() is not None
        
        cur.close()
        conn.close()
        
        if exists:
            print("Database 'solar_data' exists")
            return True
        else:
            print("Database 'solar_data' does not exist")
            return False
            
    except Exception as e:
        print(f"Failed to check database: {e}")
        return False

def check_tables():
    """Check if required tables exist"""
    required_tables = [
        'weather_data',
        'solar_panel_readings',
        'silver_weather',
        'silver_solar',
        'gold_daily_panel',
        'gold_hourly_system',
        'gold_monthly_kpis',
        'gold_anomalies'
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        missing_tables = []
        for table in required_tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]
            if exists:
                print(f"  OK (200) - {table}")
            else:
                print(f"  ERROR - {table}")
                missing_tables.append(table)
        
        cur.close()
        conn.close()
        
        if missing_tables:
            print(f"\nMissing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("\nAll required tables exist")
            return True
            
    except Exception as e:
        print(f"Failed to check tables: {e}")
        return False

def check_recent_data():
    """Check if there's recent data in the tables"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Check weather_data
        cur.execute("SELECT COUNT(*) FROM weather_data WHERE timestamp > NOW() - INTERVAL '1 hour'")
        weather_count = cur.fetchone()[0]
        print(f"  Weather data last hour: {weather_count} records")
        
        # Check solar data
        cur.execute("SELECT COUNT(*) FROM solar_panel_readings WHERE timestamp > NOW() - INTERVAL '1 hour'")
        solar_count = cur.fetchone()[0]
        print(f"  Solar data last hour: {solar_count} records")
        
        cur.close()
        conn.close()
        
        if weather_count == 0 and solar_count == 0:
            print("No recent data in any table")
            return False
        return True
        
    except Exception as e:
        print(f"Failed to check recent data: {e}")
        return False

def check_postgres_health():
    """Main health check function"""
    print("\n" + "="*50)
    print("POSTGRESQL HEALTH CHECK")
    print("="*50)
    print(f"Environment: {'Docker' if IN_DOCKER else 'Host'}")
    print(f"Target: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("="*50)
    
    checks = [
        ("Connection", check_connection),
        ("Database", check_database_exists),
        ("Tables", check_tables),
        ("Recent Data", check_recent_data)
    ]
    
    failed = 0
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if not check_func():
            failed += 1
    
    print("\n" + "="*50)
    if failed == 0:
        print("All PostgreSQL checks passed")
        return 0
    else:
        print(f"ERROR - {failed} checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(check_postgres_health())