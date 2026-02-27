# orchestration/dags/03_gold_load_dag.py
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

sys.path.append('/opt/airflow/orchestration')
from config import dag_config as config

default_args = config.default_args.copy()

def check_silver_ready():
    """Check if silver tables are populated"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    hook = PostgresHook(postgres_conn_id=config.POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM silver_weather) as weather,
            (SELECT COUNT(*) FROM silver_solar) as solar
    """)
    weather_count, solar_count = cursor.fetchone()
    cursor.close()
    conn.close()
    
    print(f"Silver weather: {weather_count} rows")
    print(f"Silver solar: {solar_count} rows")
    
    if weather_count == 0 or solar_count == 0:
        raise Exception("Silver tables are empty! Run silver transform first.")

with DAG(
    '03_gold_load',
    default_args=default_args,
    description='Step 3: Load Gold aggregations',
    schedule_interval='@daily',
    catchup=False,
    tags=['gold', 'aggregation']
) as dag:

    check_silver = PythonOperator(
        task_id='check_silver_ready',
        python_callable=check_silver_ready
    )

    load_daily_panel = PostgresOperator(
        task_id='load_daily_panel',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql="""
            TRUNCATE gold_daily_panel;
            
            INSERT INTO gold_daily_panel
            SELECT 
                DATE(timestamp) AS date,
                panel_id,
                panel_type,
                COUNT(*) AS readings_count,
                AVG(production_kw) AS avg_production_kw,
                SUM(production_kw) AS total_production_kwh,
                MAX(production_kw) AS peak_production_kw,
                MIN(production_kw) AS min_production_kw,
                AVG(efficiency_ratio) AS avg_efficiency,
                COUNT(CASE WHEN is_valid THEN 1 END) AS valid_readings,
                COUNT(CASE WHEN NOT is_valid THEN 1 END) AS invalid_readings,
                ROUND(100.0 * COUNT(CASE WHEN is_valid THEN 1 END) / COUNT(*), 2) AS data_quality_pct,
                NOW() AS gold_ingestion_time
            FROM silver_solar
            GROUP BY DATE(timestamp), panel_id, panel_type;
        """
    )

    load_hourly_system = PostgresOperator(
        task_id='load_hourly_system',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql="""
            TRUNCATE gold_hourly_system;
            
            INSERT INTO gold_hourly_system
            SELECT 
                DATE_TRUNC('hour', timestamp) AS hour,
                COUNT(DISTINCT panel_id) AS active_panels,
                SUM(production_kw) AS total_production_kw,
                AVG(production_kw) AS avg_production_per_panel,
                MAX(production_kw) AS peak_production_kw,
                AVG(temperature_c) AS avg_temperature,
                AVG(efficiency_ratio) AS avg_system_efficiency,
                COUNT(CASE WHEN is_valid THEN 1 END) AS valid_readings,
                NOW() AS gold_ingestion_time
            FROM silver_solar
            GROUP BY DATE_TRUNC('hour', timestamp);
        """
    )

    load_monthly_kpis = PostgresOperator(
        task_id='load_monthly_kpis',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql="""
            TRUNCATE gold_monthly_kpis;
            
            INSERT INTO gold_monthly_kpis
            SELECT 
                EXTRACT(YEAR FROM timestamp) AS year,
                EXTRACT(MONTH FROM timestamp) AS month,
                COUNT(DISTINCT panel_id) AS total_panels,
                SUM(production_kw) AS total_production_kwh,
                AVG(production_kw) AS avg_production_kw,
                MAX(production_kw) AS peak_production_kw,
                AVG(efficiency_ratio) AS avg_efficiency,
                AVG(temperature_c) AS avg_temperature,
                COUNT(CASE WHEN is_valid THEN 1 END) AS valid_readings,
                ROUND(100.0 * COUNT(CASE WHEN is_valid THEN 1 END) / COUNT(*), 2) AS data_quality_pct,
                NOW() AS gold_ingestion_time
            FROM silver_solar
            GROUP BY EXTRACT(YEAR FROM timestamp), EXTRACT(MONTH FROM timestamp);
        """
    )

    verify_gold = PostgresOperator(
        task_id='verify_gold',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql="""
            SELECT 'gold_daily_panel' as table_name, COUNT(*) FROM gold_daily_panel
            UNION ALL
            SELECT 'gold_hourly_system', COUNT(*) FROM gold_hourly_system
            UNION ALL
            SELECT 'gold_monthly_kpis', COUNT(*) FROM gold_monthly_kpis;
        """
    )

    check_silver >> [load_daily_panel, load_hourly_system, load_monthly_kpis] >> verify_gold