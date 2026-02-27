# orchestration/dags/02_silver_transform_dag.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime
import sys

sys.path.append('/opt/airflow/orchestration')
from config import dag_config as config

default_args = config.default_args.copy()
default_args['retries'] = 2

def check_bronze_data():
    """Check if bronze tables have new data"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    hook = PostgresHook(postgres_conn_id=config.POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) FROM weather_data) as weather_count,
            (SELECT COUNT(*) FROM solar_panel_readings) as solar_count,
            (SELECT MAX(ingestion_timestamp) FROM weather_data) as last_weather,
            (SELECT MAX(ingestion_timestamp) FROM solar_panel_readings) as last_solar
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    print(f"📊 Bronze status:")
    print(f"   Weather: {result[0]} records, last: {result[2]}")
    print(f"   Solar: {result[1]} records, last: {result[3]}")
    
    if result[0] == 0 and result[1] == 0:
        raise Exception("No data in bronze tables!")

with DAG(
    '02_silver_transform',
    default_args=default_args,
    description='Step 2: Transform Bronze → Silver',
    schedule_interval='@hourly',
    catchup=False,
    tags=['silver', 'transform']
) as dag:

    check_bronze = PythonOperator(
        task_id='check_bronze_data',
        python_callable=check_bronze_data
    )

    create_silver_weather = PostgresOperator(
        task_id='create_silver_weather',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql=f"""
            TRUNCATE silver_weather;
            
            INSERT INTO silver_weather
            SELECT 
                w.*,
                EXTRACT(YEAR FROM timestamp) AS year,
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(DAY FROM timestamp) AS day,
                EXTRACT(HOUR FROM timestamp) AS hour,
                EXTRACT(DOW FROM timestamp) AS day_of_week,
                CASE 
                    WHEN temperature < 0 THEN 'Freezing'
                    WHEN temperature < 10 THEN 'Cold'
                    WHEN temperature < 20 THEN 'Mild'
                    WHEN temperature < 30 THEN 'Warm'
                    ELSE 'Hot'
                END AS temperature_category,
                CASE 
                    WHEN cloud_cover < 20 THEN 'Clear'
                    WHEN cloud_cover < 60 THEN 'Partly Cloudy'
                    ELSE 'Cloudy'
                END AS sky_condition,
                CASE 
                    WHEN uv_index < 3 THEN 'Low'
                    WHEN uv_index < 6 THEN 'Moderate'
                    WHEN uv_index < 8 THEN 'High'
                    ELSE 'Very High'
                END AS uv_category,
                CASE 
                    WHEN temperature BETWEEN -30 AND 50 
                         AND humidity BETWEEN 0 AND 100
                         AND wind_speed >= 0
                         AND cloud_cover BETWEEN 0 AND 100
                    THEN TRUE
                    ELSE FALSE
                END AS is_valid,
                NOW() AS silver_ingestion_time
            FROM weather_data w;
        """
    )

    create_silver_solar = PostgresOperator(
        task_id='create_silver_solar',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql=f"""
            TRUNCATE silver_solar;
            
            INSERT INTO silver_solar
            SELECT 
                s.*,
                EXTRACT(YEAR FROM timestamp) AS year,
                EXTRACT(MONTH FROM timestamp) AS month,
                EXTRACT(DAY FROM timestamp) AS day,
                EXTRACT(HOUR FROM timestamp) AS hour,
                EXTRACT(DOW FROM timestamp) AS day_of_week,
                production_kw / NULLIF(panel_power_kw, 0) AS efficiency_ratio,
                CASE 
                    WHEN production_kw / NULLIF(panel_power_kw, 0) > 0.8 THEN 'Excellent'
                    WHEN production_kw / NULLIF(panel_power_kw, 0) > 0.5 THEN 'Good'
                    WHEN production_kw / NULLIF(panel_power_kw, 0) > 0.2 THEN 'Fair'
                    ELSE 'Poor'
                END AS performance_category,
                CASE 
                    WHEN production_kw >= 0 
                         AND temperature_c BETWEEN -30 AND 60
                         AND cloud_factor BETWEEN 0 AND 1
                         AND temp_efficiency BETWEEN 0.5 AND 1.5
                    THEN TRUE
                    ELSE FALSE
                END AS is_valid,
                NOW() AS silver_ingestion_time
            FROM solar_panel_readings s;
        """
    )

    verify_silver = PostgresOperator(
        task_id='verify_silver',
        postgres_conn_id=config.POSTGRES_CONN_ID,
        sql="""
            SELECT 'silver_weather' as table_name, COUNT(*) as rows FROM silver_weather
            UNION ALL
            SELECT 'silver_solar', COUNT(*) FROM silver_solar;
        """
    )

    check_bronze >> [create_silver_weather, create_silver_solar] >> verify_silver