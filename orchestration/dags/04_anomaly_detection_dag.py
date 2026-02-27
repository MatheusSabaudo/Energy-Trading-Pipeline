from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'solar_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['admin@msr.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    '04_anomaly_detection',
    default_args=default_args,
    description='Step 4: Detect and alert on anomalies',
    schedule_interval='@hourly',
    catchup=False,
    tags=['anomaly', 'alert']
) as dag:

    run_anomaly_detection = PostgresOperator(
        task_id='run_anomaly_detection',
        postgres_conn_id='postgres_solar',
        sql="""
            -- ============================================================
            -- LOW PRODUCTION ANOMALIES
            -- Detect panels producing significantly less than normal
            -- ============================================================
            WITH panel_stats AS (
                SELECT 
                    panel_id,
                    AVG(production_kw) as avg_production,
                    STDDEV(production_kw) as stddev_production
                FROM silver_solar
                WHERE is_valid = true
                AND timestamp > NOW() - INTERVAL '7 days'
                GROUP BY panel_id
            ),
            today_readings AS (
                SELECT 
                    s.panel_id,
                    s.production_kw,
                    p.avg_production,
                    (s.production_kw - p.avg_production) / NULLIF(p.stddev_production, 0) as z_score
                FROM silver_solar s
                JOIN panel_stats p ON s.panel_id = p.panel_id
                WHERE DATE(s.timestamp) = CURRENT_DATE
            )
            INSERT INTO gold_anomalies (
                anomaly_date, 
                panel_id, 
                anomaly_type, 
                severity, 
                expected_value, 
                actual_value, 
                deviation_percentage,
                detection_time,
                resolution_status
            )
            SELECT 
                CURRENT_DATE,
                panel_id,
                CASE 
                    WHEN z_score < -3 THEN 'Critical Low Production'
                    ELSE 'Low Production'
                END,
                CASE 
                    WHEN z_score < -3 THEN 'Critical'
                    ELSE 'Warning'
                END,
                avg_production,
                production_kw,
                ROUND(100.0 * (avg_production - production_kw) / avg_production, 2),
                NOW(),
                'Open'
            FROM today_readings
            WHERE z_score < -2
            AND NOT EXISTS (
                SELECT 1 FROM gold_anomalies g 
                WHERE g.panel_id = today_readings.panel_id 
                AND g.anomaly_type LIKE '%Low Production%'
                AND g.anomaly_date = CURRENT_DATE
            );

            -- ============================================================
            -- HIGH TEMPERATURE ANOMALIES
            -- Detect panels running hotter than normal
            -- ============================================================
            WITH temp_stats AS (
                SELECT 
                    AVG(temperature_c) as avg_temp,
                    STDDEV(temperature_c) as stddev_temp
                FROM silver_solar
                WHERE is_valid = true
                AND timestamp > NOW() - INTERVAL '7 days'
            ),
            today_temps AS (
                SELECT 
                    s.panel_id,
                    s.temperature_c,
                    (s.temperature_c - (SELECT avg_temp FROM temp_stats)) / 
                    NULLIF((SELECT stddev_temp FROM temp_stats), 0) as z_score
                FROM silver_solar s
                WHERE DATE(s.timestamp) = CURRENT_DATE
            )
            INSERT INTO gold_anomalies (
                anomaly_date,
                panel_id,
                anomaly_type,
                severity,
                actual_value,
                expected_value,
                deviation_percentage,
                detection_time,
                resolution_status
            )
            SELECT 
                CURRENT_DATE,
                panel_id,
                'High Temperature',
                CASE 
                    WHEN z_score > 3 THEN 'Critical'
                    WHEN z_score > 2 THEN 'Warning'
                END,
                temperature_c,
                (SELECT avg_temp FROM temp_stats),
                ROUND(100.0 * (temperature_c - (SELECT avg_temp FROM temp_stats)) / 
                     (SELECT avg_temp FROM temp_stats), 2),
                NOW(),
                'Open'
            FROM today_temps
            WHERE z_score > 2
            AND NOT EXISTS (
                SELECT 1 FROM gold_anomalies g 
                WHERE g.panel_id = today_temps.panel_id 
                AND g.anomaly_type = 'High Temperature'
                AND g.anomaly_date = CURRENT_DATE
            );

            -- ============================================================
            -- SMART MISSING DATA DETECTION
            -- Only flag panels that were expected to report but didn't
            -- ============================================================
            WITH 
            -- Get panels that have been active in the last 7 days
            expected_panels AS (
                SELECT DISTINCT panel_id 
                FROM silver_solar
                WHERE timestamp > NOW() - INTERVAL '7 days'
            ),
            -- Get panels that reported in the last hour
            reporting_recent AS (
                SELECT DISTINCT panel_id 
                FROM silver_solar 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
            ),
            -- Get panels that reported today
            reporting_today AS (
                SELECT DISTINCT panel_id 
                FROM silver_solar 
                WHERE DATE(timestamp) = CURRENT_DATE
            ),
            -- Calculate missing data with different severity levels
            missing_data AS (
                SELECT 
                    e.panel_id,
                    CASE 
                        WHEN r_hour.panel_id IS NULL AND r_day.panel_id IS NOT NULL THEN 'Warning'
                        WHEN r_hour.panel_id IS NULL AND r_day.panel_id IS NULL THEN 'Critical'
                        ELSE NULL
                    END as severity
                FROM expected_panels e
                LEFT JOIN reporting_recent r_hour ON e.panel_id = r_hour.panel_id
                LEFT JOIN reporting_today r_day ON e.panel_id = r_day.panel_id
                WHERE r_hour.panel_id IS NULL  -- Not reported in last hour
            )
            -- Insert only new anomalies, avoid duplicates
            INSERT INTO gold_anomalies (
                anomaly_date, 
                panel_id, 
                anomaly_type, 
                severity,
                detection_time,
                resolution_status
            )
            SELECT 
                CURRENT_DATE,
                panel_id,
                'Missing Data',
                severity,
                NOW(),
                'Open'
            FROM missing_data
            WHERE severity IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM gold_anomalies g 
                WHERE g.panel_id = missing_data.panel_id 
                AND g.anomaly_type = 'Missing Data'
                AND g.resolution_status = 'Open'
            );

            -- ============================================================
            -- SUDDEN PRODUCTION DROP (compared to yesterday)
            -- ============================================================
            WITH yesterday_prod AS (
                SELECT 
                    panel_id,
                    AVG(production_kw) as yesterday_avg
                FROM silver_solar
                WHERE DATE(timestamp) = CURRENT_DATE - 1
                GROUP BY panel_id
            ),
            today_prod AS (
                SELECT 
                    panel_id,
                    AVG(production_kw) as today_avg
                FROM silver_solar
                WHERE DATE(timestamp) = CURRENT_DATE
                GROUP BY panel_id
            ),
            drops AS (
                SELECT 
                    t.panel_id,
                    y.yesterday_avg,
                    t.today_avg,
                    (y.yesterday_avg - t.today_avg) / NULLIF(y.yesterday_avg, 0) * 100 as drop_percentage
                FROM today_prod t
                JOIN yesterday_prod y ON t.panel_id = y.panel_id
                WHERE t.today_avg < y.yesterday_avg * 0.5  -- 50% drop
            )
            INSERT INTO gold_anomalies (
                anomaly_date,
                panel_id,
                anomaly_type,
                severity,
                expected_value,
                actual_value,
                deviation_percentage,
                detection_time,
                resolution_status
            )
            SELECT 
                CURRENT_DATE,
                panel_id,
                'Sudden Production Drop',
                CASE 
                    WHEN drop_percentage > 70 THEN 'Critical'
                    ELSE 'Warning'
                END,
                yesterday_avg,
                today_avg,
                ROUND(drop_percentage, 2),
                NOW(),
                'Open'
            FROM drops
            WHERE NOT EXISTS (
                SELECT 1 FROM gold_anomalies g 
                WHERE g.panel_id = drops.panel_id 
                AND g.anomaly_type = 'Sudden Production Drop'
                AND g.anomaly_date = CURRENT_DATE
            );

            -- ============================================================
            -- Log summary of today's anomalies
            -- ============================================================
            SELECT 
                'ANOMALY SUMMARY' as title,
                COUNT(*) as total,
                COUNT(CASE WHEN severity = 'Critical' THEN 1 END) as critical,
                COUNT(CASE WHEN severity = 'Warning' THEN 1 END) as warning
            FROM gold_anomalies
            WHERE anomaly_date = CURRENT_DATE;
        """
    )