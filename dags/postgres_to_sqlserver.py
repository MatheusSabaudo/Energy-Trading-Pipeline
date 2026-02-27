# dags/bronze_raw_load.py (modified version without MsSqlHook)
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import logging
import pandas as pd
import pyodbc
import os

default_args = {
    'owner': 'solar_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 2, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def extract_raw_from_postgres(**context):
    """Extract RAW data from PostgreSQL"""
    logging.info("📤 Extracting RAW data from PostgreSQL...")
    
    pg_hook = PostgresHook(postgres_conn_id='postgres_solar')
    last_id = context['task_instance'].xcom_pull(key='last_id') or 0
    
    query = """
        SELECT 
            id,
            event_id,
            timestamp,
            panel_id,
            panel_type,
            panel_power_kw,
            production_kw,
            temperature_c,
            cloud_factor,
            temp_efficiency,
            status,
            city,
            created_at
        FROM solar_panel_readings
        WHERE id > %s
        ORDER BY id
    """
    
    df = pg_hook.get_pandas_df(query, parameters=[last_id])
    logging.info(f"   Extracted {len(df)} RAW rows")
    
    output_file = f"/tmp/bronze_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
    df.to_parquet(output_file, index=False)
    
    if len(df) > 0:
        max_id = df['id'].max()
        context['task_instance'].xcom_push(key='last_id', value=max_id)
        context['task_instance'].xcom_push(key='data_file', value=output_file)
    
    return f"Extracted {len(df)} raw rows"

def load_raw_to_sqlserver(**context):
    """Load RAW data to SQL Server Bronze using pyodbc directly"""
    logging.info("📥 Loading RAW data to SQL Server Bronze...")
    
    data_file = context['task_instance'].xcom_pull(key='data_file')
    
    if not data_file:
        logging.info("No new data to load")
        return "No data loaded"
    
    df = pd.read_parquet(data_file)
    
    # Direct pyodbc connection (no Airflow hook)
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=host.docker.internal;"  # Use host.docker.internal from container to Windows host
        "DATABASE=EnergyTradingPipeline;"
        "Trusted_Connection=yes;"  # Windows authentication
        # Or use SQL auth:
        # "UID=your_username;"
        # "PWD=your_password;"
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        batch_size = 1000
        rows_inserted = 0
        
        for index, row in df.iterrows():
            cursor.execute("""
                INSERT INTO bronze.api_data (
                    event_id, timestamp, panel_id, panel_type, panel_power_kw,
                    production_kw, temperature_c, cloud_factor, temp_efficiency,
                    actual_status, city, ingestion_time, kafka_topic, 
                    kafka_partition, kafka_offset, source_file, raw_json, 
                    is_processed, first_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            str(row['event_id']), row['timestamp'], row['panel_id'], row['panel_type'], 
            float(row['panel_power_kw']) if row['panel_power_kw'] else None,
            float(row['production_kw']) if row['production_kw'] else None,
            float(row['temperature_c']) if row['temperature_c'] else None,
            float(row['cloud_factor']) if row['cloud_factor'] else None,
            float(row['temp_efficiency']) if row['temp_efficiency'] else None,
            row['status'], row['city'], datetime.now(),
            'solar-raw', 0, 0, 'postgres_export', '{}', 0, datetime.now()
            )
            
            rows_inserted += 1
            
            if rows_inserted % batch_size == 0:
                conn.commit()
                logging.info(f"   Committed {rows_inserted} rows")
        
        conn.commit()
        logging.info(f"✅ Loaded {rows_inserted} RAW rows to Bronze")
        
    except Exception as e:
        logging.error(f"❌ Error loading to SQL Server: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()
    
    return f"✅ Loaded {rows_inserted} rows"

def get_last_loaded_id(**context):
    """Get the last loaded ID from previous run"""
    last_id = context['task_instance'].xcom_pull(key='last_id') or 0
    logging.info(f"📌 Last loaded ID: {last_id}")
    return last_id

with DAG(
    'bronze_raw_load',
    default_args=default_args,
    description='Load RAW data from PostgreSQL to SQL Server Bronze',
    schedule_interval='*/15 * * * *',
    catchup=False,
    tags=['solar', 'bronze', 'raw'],
    max_active_runs=1
) as dag:

    get_last_id = PythonOperator(
        task_id='get_last_loaded_id',
        python_callable=get_last_loaded_id
    )
    
    extract_task = PythonOperator(
        task_id='extract_raw_from_postgres',
        python_callable=extract_raw_from_postgres
    )
    
    load_task = PythonOperator(
        task_id='load_raw_to_sqlserver',
        python_callable=load_raw_to_sqlserver
    )
    
    get_last_id >> extract_task >> load_task