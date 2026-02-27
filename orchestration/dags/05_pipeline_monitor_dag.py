from airflow import DAG
from airflow.operators.python import PythonOperator
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

def calculate_pipeline_health():
    """Calculate overall pipeline health score with weighted scoring"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    hook = PostgresHook(postgres_conn_id='postgres_solar')
    conn = hook.get_conn()
    cursor = conn.cursor()
    
    health_score = 100
    deductions = []
    
    # ============================================================
    # 1. Data Freshness (Max 30 points deduction)
    # ============================================================
    cursor.execute("""
        SELECT 
            EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))/3600 as hours_since_last
        FROM solar_panel_readings
    """)
    hours_since = cursor.fetchone()[0] or 0
    
    if hours_since > 24:
        health_score -= 30
        deductions.append(f"Stale data: -30 ({hours_since:.1f} hours)")
    elif hours_since > 6:
        health_score -= 10
        deductions.append(f"Data delay: -10 ({hours_since:.1f} hours)")
    else:
        print(f"✓ Data fresh: {hours_since:.1f} hours")
    
    # ============================================================
    # 2. Anomaly Scoring with weighted categories
    # ============================================================
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN severity = 'Critical' AND anomaly_type != 'Missing Data' THEN 1 END) as critical_real,
            COUNT(CASE WHEN severity = 'Critical' AND anomaly_type = 'Missing Data' THEN 1 END) as critical_missing,
            COUNT(CASE WHEN severity = 'Warning' THEN 1 END) as warning,
            COUNT(*) as total_open
        FROM gold_anomalies
        WHERE resolution_status = 'Open'
    """)
    result = cursor.fetchone()
    critical_real = result[0] or 0
    critical_missing = result[1] or 0
    warning = result[2] or 0
    
    # Weighted scoring:
    # - Real critical issues: 5 points each
    # - Missing data critical: 1 point each (less severe)
    # - Warnings: 1 point each
    anomaly_penalty = (critical_real * 5) + (critical_missing * 1) + (warning * 1)
    anomaly_penalty = min(anomaly_penalty, 40)  # Cap at 40 points
    
    health_score -= anomaly_penalty
    if anomaly_penalty > 0:
        deductions.append(f"Anomalies: -{anomaly_penalty} ({critical_real} critical real, {critical_missing} missing, {warning} warning)")
    else:
        print("✓ No open anomalies")
    
    # ============================================================
    # 3. Data Quality (Max 20 points deduction)
    # ============================================================
    cursor.execute("""
        SELECT AVG(data_quality_pct) FROM gold_daily_panel
        WHERE date >= CURRENT_DATE - 7
    """)
    quality = cursor.fetchone()[0]
    
    if quality is None:
        print("ℹ️ No quality data available for last 7 days")
    elif quality < 80:
        health_score -= 20
        deductions.append(f"Poor data quality: -20 ({quality:.1f}%)")
    elif quality < 90:
        health_score -= 10
        deductions.append(f"Fair data quality: -10 ({quality:.1f}%)")
    else:
        print(f"✓ Good data quality: {quality:.1f}%")
    
    # ============================================================
    # 4. Pipeline Completeness (Check if all tables have data)
    # ============================================================
    cursor.execute("""
        SELECT 
            (SELECT COUNT(*) > 0 FROM weather_data) as has_weather,
            (SELECT COUNT(*) > 0 FROM solar_panel_readings) as has_solar,
            (SELECT COUNT(*) > 0 FROM silver_weather) as has_silver_weather,
            (SELECT COUNT(*) > 0 FROM silver_solar) as has_silver_solar,
            (SELECT COUNT(*) > 0 FROM gold_daily_panel) as has_gold
    """)
    tables = cursor.fetchone()
    missing_tables = sum(1 for t in tables if not t)
    if missing_tables > 0:
        penalty = missing_tables * 5
        health_score -= penalty
        deductions.append(f"Missing tables: -{penalty} ({missing_tables} tables empty)")
    
    cursor.close()
    conn.close()
    
    # ============================================================
    # 5. Ensure health score doesn't go below 0
    # ============================================================
    health_score = max(0, health_score)
    
    # Print summary
    print("\n" + "="*60)
    print("PIPELINE HEALTH SCORE SUMMARY")
    print("="*60)
    if deductions:
        print("Deductions:")
        for d in deductions:
            print(f"  {d}")
    else:
        print("✓ No deductions - Pipeline fully healthy!")
    
    print(f"\n📊 FINAL HEALTH SCORE: {health_score}/100")
    
    # Determine health status
    if health_score >= 90:
        status = "EXCELLENT"
        print(f"STATUS: ✅ {status} - All systems operational")
    elif health_score >= 70:
        status = "GOOD"
        print(f"STATUS: 👍 {status} - Minor issues detected")
    elif health_score >= 50:
        status = "FAIR"
        print(f"STATUS: ⚠️ {status} - Issues require attention")
    else:
        status = "POOR"
        print(f"STATUS: ❌ {status} - Critical issues - Investigate immediately!")
        raise Exception(f"Pipeline health critical: {health_score}/100 - Immediate attention required!")
    
    print("="*60)
    
    return health_score

with DAG(
    '05_pipeline_monitor',
    default_args=default_args,
    description='Step 5: Monitor pipeline health',
    schedule_interval='@hourly',
    catchup=False,
    tags=['monitor', 'health']
) as dag:

    check_tables = PostgresOperator(
        task_id='check_table_counts',
        postgres_conn_id='postgres_solar',
        sql="""
            SELECT 
                table_name,
                row_count,
                layer
            FROM (
                SELECT 'weather_data' as table_name, COUNT(*) as row_count, 'bronze' as layer
                FROM weather_data
                UNION ALL
                SELECT 'solar_panel_readings', COUNT(*), 'bronze'
                FROM solar_panel_readings
                UNION ALL
                SELECT 'silver_weather', COUNT(*), 'silver'
                FROM silver_weather
                UNION ALL
                SELECT 'silver_solar', COUNT(*), 'silver'
                FROM silver_solar
                UNION ALL
                SELECT 'gold_daily_panel', COUNT(*), 'gold'
                FROM gold_daily_panel
                UNION ALL
                SELECT 'gold_hourly_system', COUNT(*), 'gold'
                FROM gold_hourly_system
                UNION ALL
                SELECT 'gold_monthly_kpis', COUNT(*), 'gold'
                FROM gold_monthly_kpis
                UNION ALL
                SELECT 'gold_anomalies', COUNT(*), 'gold'
                FROM gold_anomalies
            ) counts
            ORDER BY layer, table_name;
        """
    )

    calculate_health = PythonOperator(
        task_id='calculate_health_score',
        python_callable=calculate_pipeline_health
    )

    check_tables >> calculate_health