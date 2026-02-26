# dags/solar_consumer_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import subprocess
import time

sys.path.append('/home/msr/Energy-Trading-Pipeline')

default_args = {
    'owner': 'solar_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}

def check_kafka_topic():
    """Check if Kafka topic exists and has messages"""
    result = subprocess.run(
        ['docker', 'exec', 'kafka', '/opt/kafka/bin/kafka-topics.sh', 
         '--list', '--bootstrap-server', 'localhost:9092'],
        capture_output=True,
        text=True
    )
    
    if 'solar-raw' not in result.stdout:
        raise Exception("Kafka topic 'solar-raw' not found")
    
    return "Kafka topic OK"

def start_postgres_consumer():
    """Start the PostgreSQL consumer"""
    try:
        # Run consumer in background
        process = subprocess.Popen([
            'python3',
            '/home/msr/Energy-Trading-Pipeline/consumers/kafka_to_postgres.py'
        ])
        
        # Wait a bit to check if it starts
        time.sleep(5)
        
        if process.poll() is None:
            return f"Consumer started with PID: {process.pid}"
        else:
            raise Exception("Consumer failed to start")
            
    except Exception as e:
        raise Exception(f"Failed to start consumer: {e}")

def verify_data_flow():
    """Verify data is flowing to PostgreSQL"""
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='solar_data',
            user='airflow',
            password='airflow'
        )
        cur = conn.cursor()
        
        # Check records in last minute
        cur.execute("""
            SELECT COUNT(*) 
            FROM solar_panel_readings 
            WHERE timestamp > NOW() - INTERVAL '1 minute'
        """)
        count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        if count > 0:
            return f"✅ Data flowing: {count} records in last minute"
        else:
            return "⚠️ No new data in last minute"
            
    except Exception as e:
        raise Exception(f"Database check failed: {e}")

# FIXED: Changed schedule and added max_active_runs=1
with DAG(
    'solar_consumer',
    default_args=default_args,
    description='Run PostgreSQL consumer',
    schedule_interval='*/10 * * * *',  # Every 10 minutes (not continuous)
    max_active_runs=1,  # Required for certain schedules
    catchup=False,
    tags=['solar', 'postgres', 'kafka']
) as dag:

    check_kafka = PythonOperator(
        task_id='check_kafka_topic',
        python_callable=check_kafka_topic
    )
    
    start_consumer = PythonOperator(
        task_id='start_postgres_consumer',
        python_callable=start_postgres_consumer
    )
    
    verify_data = PythonOperator(
        task_id='verify_data_flow',
        python_callable=verify_data_flow
    )
    
    check_kafka >> start_consumer >> verify_data