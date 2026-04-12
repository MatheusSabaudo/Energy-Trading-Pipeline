# orchestration/dags/01_ingestion_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
import sys

sys.path.append('/opt/airflow/orchestration')
from config import dag_config as config

default_args = config.default_args.copy()


def check_kafka_health():
    import subprocess

    result = subprocess.run(
        ['python', config.CHECK_KAFKA_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise Exception(f"Kafka health check failed: {result.stderr}")
    print(result.stdout)


def check_postgres_health():
    import subprocess

    result = subprocess.run(
        ['python', config.CHECK_POSTGRES_SCRIPT],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise Exception(f"PostgreSQL health check failed: {result.stderr}")
    print(result.stdout)


with DAG(
    '01_ingestion_pipeline',
    default_args=default_args,
    description='Step 1: Validate ingestion services and bronze freshness',
    schedule_interval='*/15 * * * *',
    catchup=False,
    tags=['ingestion', 'api', 'kafka'],
) as dag:

    check_kafka = PythonOperator(
        task_id='check_kafka_health',
        python_callable=check_kafka_health,
    )

    check_postgres = PythonOperator(
        task_id='check_postgres_health',
        python_callable=check_postgres_health,
    )

    verify_ingestion = PostgresOperator(
        task_id='verify_ingestion',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql="""
            SELECT
                'weather_data' as table_name,
                COUNT(*) as count,
                MAX(timestamp) as latest
            FROM weather_data
            WHERE timestamp > NOW() - INTERVAL '15 minutes'
            UNION ALL
            SELECT
                'solar_panel_readings',
                COUNT(*),
                MAX(timestamp)
            FROM solar_panel_readings
            WHERE timestamp > NOW() - INTERVAL '15 minutes';
        """,
    )

    [check_kafka, check_postgres] >> verify_ingestion
