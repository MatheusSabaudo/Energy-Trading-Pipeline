#!/usr/bin/env python3
"""
PostgreSQL Health Check Script
Checks if PostgreSQL is running, database exists, tables exist, and recent data is present.
Compatible both inside Docker containers and on host machine.
"""

import sys
import os
import time
import psycopg2
from psycopg2 import OperationalError

# -----------------------------
# Detect Docker environment
# -----------------------------
def is_running_in_docker():
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        return 'DOCKER_CONTAINER' in os.environ

IN_DOCKER = is_running_in_docker()

# -----------------------------
# Database configuration
# -----------------------------
DB_CONFIG = {
    'host': 'postgres' if IN_DOCKER else 'localhost',
    'port': 5432,
    'user': 'airflow',
    'password': 'airflow',
    'database': 'solar_data'
}

print(f"Running {'inside Docker' if IN_DOCKER else 'on host machine'}")
print(f"Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}")

# -----------------------------
# Connection check with retries
# -----------------------------
def check_connection(retries=5, delay=5):
    for i in range(retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            print(f"✅ PostgreSQL connection successful")
            return True
        except OperationalError as e:
            print(f"Attempt {i+1}/{retries} - Connection failed: {e}")
            time.sleep(delay)
    return False

# -----------------------------
# Check if database exists
# -----------------------------
def check_database_exists():
    try:
        config = DB_CONFIG.copy()
        config['database'] = 'postgres'
        conn = psycopg2.connect(**config)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'solar_data'")
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        if exists:
            print("✅ Database 'solar_data' exists")
            return True
        else:
            print("❌ Database 'solar_data' does not exist")
            return False
    except Exception as e:
        print(f"Failed to check database: {e}")
        return False

# -----------------------------
# Check required tables
# -----------------------------
def check_tables():
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
                print(f"✅ Table exists - {table}")
            else:
                print(f"❌ Table missing - {table}")
                missing_tables.append(table)
        cur.close()
        conn.close()
        if missing_tables:
            print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
            return False
        print("\n✅ All required tables exist")
        return True
    except Exception as e:
        print(f"Failed to check tables: {e}")
        return False

# -----------------------------
# Check recent data
# -----------------------------
def check_recent_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Weather data
        cur.execute("SELECT COUNT(*) FROM weather_data WHERE timestamp > NOW() - INTERVAL '1 hour'")
        weather_count = cur.fetchone()[0]
        print(f"Weather data last hour: {weather_count} records")
        # Solar data
        cur.execute("SELECT COUNT(*) FROM solar_panel_readings WHERE timestamp > NOW() - INTERVAL '1 hour'")
        solar_count = cur.fetchone()[0]
        print(f"Solar data last hour: {solar_count} records")
        cur.close()
        conn.close()
        if weather_count == 0 and solar_count == 0:
            print("❌ No recent data in any table")
            return False
        return True
    except Exception as e:
        print(f"Failed to check recent data: {e}")
        return False

# -----------------------------
# Main health check
# -----------------------------
def check_postgres_health():
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
    for name, func in checks:
        print(f"\nChecking {name}...")
        if not func():
            failed += 1

    print("\n" + "="*50)
    if failed == 0:
        print("✅ All PostgreSQL checks passed")
        return 0
    else:
        print(f"❌ PostgreSQL health check failed: {failed} failed check(s)")
        return 1

# -----------------------------
# Run as script
# -----------------------------
if __name__ == "__main__":
    sys.exit(check_postgres_health())