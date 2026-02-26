# dags/solar_monitor_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import json

default_args = {
    'owner': 'solar_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

def check_containers():
    """Check Docker containers - FIXED: Use docker commands without host path"""
    try:
        # Run docker-compose ps command
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass
        
        running = [c for c in containers if c.get('State') == 'running']
        output = f"Running containers: {len(running)}/{len(containers)}"
        print(output)
        return output
        
    except Exception as e:
        print(f"Error checking containers: {e}")
        # Alternative: list all containers directly
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        containers = result.stdout.strip().split('\n')
        return f"Containers running: {len(containers)}"

def check_kafka_messages():
    """Check Kafka message count"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'kafka', '/opt/kafka/bin/kafka-run-class.sh',
             'kafka.tools.GetOffsetShell', '--broker-list', 'localhost:9092',
             '--topic', 'solar-raw', '--time', '-1'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            partitions = result.stdout.strip().split('\n')
            total = 0
            for p in partitions:
                if ':' in p:
                    _, offset = p.split(':')
                    total += int(offset)
            output = f"Kafka messages: {total}"
            print(output)
            return output
        return "Could not read Kafka topic"
        
    except Exception as e:
        print(f"Error checking Kafka: {e}")
        return f"Kafka check failed: {e}"

def check_database():
    """Check PostgreSQL records"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'postgres', 'psql', '-U', 'airflow', '-d', 'solar_data',
             '-t', '-c', 'SELECT COUNT(*) FROM solar_panel_readings'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            count = result.stdout.strip()
            output = f"PostgreSQL records: {count}"
            print(output)
            return output
        return "Could not query PostgreSQL"
        
    except Exception as e:
        print(f"Error checking PostgreSQL: {e}")
        return f"Database check failed: {e}"

with DAG(
    'solar_pipeline_monitor',
    default_args=default_args,
    description='Monitor solar data pipeline',
    schedule_interval='*/5 * * * *',
    max_active_runs=1,
    catchup=False,
    tags=['solar', 'monitoring']
) as dag:

    check_docker = PythonOperator(
        task_id='check_docker_containers',
        python_callable=check_containers
    )
    
    check_kafka = PythonOperator(
        task_id='check_kafka_messages',
        python_callable=check_kafka_messages
    )
    
    check_db = PythonOperator(
        task_id='check_database',
        python_callable=check_database
    )
    
    [check_docker, check_kafka, check_db]