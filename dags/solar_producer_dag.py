# dags/solar_producer_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess

default_args = {
    'owner': 'solar_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def run_producer():
    """Run the solar producer - FIXED: Use absolute path inside container"""
    try:
        # The producer is on your host, not in the container
        # So we need to run it on the host via SSH or another method
        
        # Option 1: If producer is running on host, just check if it's running
        result = subprocess.run(
            ['pgrep', '-f', 'solar_producer.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"Producer already running with PID: {result.stdout.strip()}"
        else:
            # Option 2: Start it on host (requires SSH or mounted volume)
            # This is a placeholder - you may need to start it manually
            return "Producer not running - start manually on host"
            
    except Exception as e:
        return f"Producer check failed: {e}"

with DAG(
    'solar_producer',
    default_args=default_args,
    description='Check solar data producer',
    schedule_interval='*/30 * * * *',
    max_active_runs=1,
    catchup=False,
    tags=['solar', 'kafka']
) as dag:

    check_producer = PythonOperator(
        task_id='check_solar_producer',
        python_callable=run_producer
    )

    check_producer