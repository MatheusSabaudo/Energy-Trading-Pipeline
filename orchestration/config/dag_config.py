# orchestration/config/dag_config.py
from datetime import datetime, timedelta

# Default DAG arguments
default_args = {
    'owner': 'Matheus Sabaudo Rodrigues',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': True,
    'email_on_retry': True,
    'email': ['matteosabaudo@outlook.it'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Database connections
POSTGRES_CONN_ID = 'postgres_solar'
POSTGRES_DB = 'solar_data'
POSTGRES_SCHEMA = 'public'

# Kafka config
KAFKA_BROKER = 'localhost:9093'  # External port from docker-compose
KAFKA_TOPIC = 'solar-raw'

# File paths (inside Airflow container)
BASE_PATH = '/opt/airflow'
INGESTION_PATH = f'{BASE_PATH}/ingestion'
ORCHESTRATION_PATH = f'{BASE_PATH}/orchestration'
POSTGRES_PATH = f'{BASE_PATH}/postgres'

# Python scripts
CHECK_KAFKA_SCRIPT = f'{ORCHESTRATION_PATH}/scripts/check_kafka.py'
CHECK_POSTGRES_SCRIPT = f'{ORCHESTRATION_PATH}/scripts/check_postgres.py'
ALERT_SCRIPT = f'{ORCHESTRATION_PATH}/scripts/alert.py'