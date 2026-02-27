# postgres_to_sqlserver_bronze.py (FIXED for your actual schema)
import psycopg2
import pyodbc
import pandas as pd
from datetime import datetime
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

# PostgreSQL Connection (Source)
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'airflow',
    'user': 'airflow',
    'password': 'airflow'
}

# SQL Server Connection (Destination)
SQLSERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'localhost',
    'database': 'EnergyTradingPipeline',
    'trusted_connection': 'yes',
}

# Batch size for loading
BATCH_SIZE = 1000

# State file to track last loaded timestamp (since no numeric ID)
STATE_FILE = 'bronze_load_state.txt'

# ============================================
# FUNCTIONS
# ============================================

def get_last_loaded_timestamp():
    """Get the last loaded timestamp from state file"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                last_timestamp = f.read().strip()
                logger.info(f"📌 Last loaded timestamp: {last_timestamp}")
                return last_timestamp
        else:
            logger.info("📌 No state file found, starting from beginning")
            return '2020-01-01'  # Start from beginning of time
    except Exception as e:
        logger.error(f"Error reading state file: {e}")
        return '2020-01-01'

def save_last_loaded_timestamp(last_timestamp):
    """Save the last loaded timestamp to state file"""
    try:
        with open(STATE_FILE, 'w') as f:
            f.write(str(last_timestamp))
        logger.info(f"💾 Saved last loaded timestamp: {last_timestamp}")
    except Exception as e:
        logger.error(f"Error saving state file: {e}")

def extract_from_postgres(last_timestamp):
    """Extract RAW data from PostgreSQL - USING YOUR ACTUAL COLUMNS"""
    logger.info("📤 Connecting to PostgreSQL...")
    
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        
        # Using timestamp for incremental loading (since no numeric ID)
        query = """
            SELECT 
                event_id::text,
                timestamp,
                panel_id,
                panel_type,
                panel_power_kw,
                production_kw,
                temperature_c,
                cloud_factor,
                temp_efficiency,
                status,
                city
            FROM solar_panel_readings
            WHERE timestamp > %s::timestamp
            ORDER BY timestamp
        """
        
        logger.info(f"📤 Extracting rows with timestamp > {last_timestamp}...")
        df = pd.read_sql_query(query, pg_conn, params=[last_timestamp])
        
        pg_conn.close()
        
        logger.info(f"   ✅ Extracted {len(df)} RAW rows")
        
        if len(df) > 0:
            # Show sample of what we got
            logger.info(f"   Sample: {df.iloc[0]['event_id']} - {df.iloc[0]['production_kw']} kW")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error extracting from PostgreSQL: {e}")
        raise

def create_sqlserver_connection():
    """Create connection to SQL Server"""
    try:
        conn_str = (
            f"DRIVER={SQLSERVER_CONFIG['driver']};"
            f"SERVER={SQLSERVER_CONFIG['server']};"
            f"DATABASE={SQLSERVER_CONFIG['database']};"
            f"Trusted_Connection={SQLSERVER_CONFIG['trusted_connection']};"
        )
        
        conn = pyodbc.connect(conn_str)
        logger.info("✅ Connected to SQL Server")
        return conn
        
    except Exception as e:
        logger.error(f"❌ Error connecting to SQL Server: {e}")
        raise

def load_to_sqlserver(df):
    """Load RAW data to SQL Server Bronze"""
    if len(df) == 0:
        logger.info("📭 No data to load")
        return 0, None
    
    logger.info(f"📥 Loading {len(df)} rows to SQL Server Bronze...")
    
    conn = None
    cursor = None
    rows_loaded = 0
    max_timestamp = None
    
    try:
        conn = create_sqlserver_connection()
        cursor = conn.cursor()
        
        for index, row in df.iterrows():
            # Track max timestamp for state file
            if max_timestamp is None or row['timestamp'] > max_timestamp:
                max_timestamp = row['timestamp']
            
            cursor.execute("""
                INSERT INTO bronze.api_data (
                    event_id, timestamp, panel_id, panel_type, panel_power_kw,
                    production_kw, temperature_c, cloud_factor, temp_efficiency,
                    actual_status, city, ingestion_time, kafka_topic, 
                    kafka_partition, kafka_offset, source_file, raw_json, 
                    is_processed, first_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            str(row['event_id']), 
            row['timestamp'], 
            row['panel_id'], 
            row['panel_type'],
            float(row['panel_power_kw']) if row['panel_power_kw'] else None,
            float(row['production_kw']) if row['production_kw'] else None,
            float(row['temperature_c']) if row['temperature_c'] else None,
            float(row['cloud_factor']) if row['cloud_factor'] else None,
            float(row['temp_efficiency']) if row['temp_efficiency'] else None,
            row['status'], 
            row['city'], 
            datetime.now(),  # ingestion_time
            'solar-raw',     # kafka_topic
            0,               # kafka_partition
            0,               # kafka_offset
            'postgres_export',  # source_file
            '{}',            # raw_json placeholder (can add later)
            0,               # is_processed
            datetime.now()   # first_seen
            )
            
            rows_loaded += 1
            
            if rows_loaded % BATCH_SIZE == 0:
                conn.commit()
                logger.info(f"   ✅ Committed {rows_loaded} rows")
        
        conn.commit()
        logger.info(f"   ✅ Successfully loaded {rows_loaded} rows")
        
        return rows_loaded, max_timestamp
        
    except Exception as e:
        logger.error(f"❌ Error loading to SQL Server: {e}")
        if conn:
            conn.rollback()
        raise
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def verify_load():
    """Quick verification of loaded data"""
    try:
        conn = create_sqlserver_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM bronze.api_data")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(timestamp) FROM bronze.api_data")
        latest = cursor.fetchone()[0]
        
        logger.info(f"📊 Bronze layer stats:")
        logger.info(f"   Total rows: {total}")
        logger.info(f"   Latest data: {latest}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error verifying load: {e}")

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("🚀 STARTING BRONZE LAYER LOAD")
    logger.info("=" * 60)
    
    try:
        # Step 1: Get last loaded timestamp
        last_timestamp = get_last_loaded_timestamp()
        
        # Step 2: Extract from PostgreSQL
        df = extract_from_postgres(last_timestamp)
        
        # Step 3: Load to SQL Server
        if len(df) > 0:
            rows_loaded, max_timestamp = load_to_sqlserver(df)
            
            # Step 4: Update state file with max timestamp
            if rows_loaded > 0 and max_timestamp:
                save_last_loaded_timestamp(max_timestamp)
            
            # Step 5: Verify
            verify_load()
        else:
            logger.info("📭 No new data to process")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f"✅ BRONZE LOAD COMPLETED in {duration:.2f} seconds")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()