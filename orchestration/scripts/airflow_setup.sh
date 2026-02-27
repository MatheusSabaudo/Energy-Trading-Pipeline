#!/bin/bash
# orchestration/scripts/airflow_setup.sh

echo "=================================================="
echo "🚀 AIRFLOW SETUP SCRIPT"
echo "=================================================="

# Step 2: Create Airflow PostgreSQL connection
echo "🔍 Creating PostgreSQL connection..."
docker exec -it airflow airflow connections delete postgres_solar 2>/dev/null
docker exec -it airflow airflow connections add 'postgres_solar' \
    --conn-type 'postgres' \
    --conn-host 'postgres' \
    --conn-port '5432' \
    --conn-login 'airflow' \
    --conn-password 'airflow' \
    --conn-schema 'solar_data'
echo "✅ PostgreSQL connection created"

# Step 3: Verify DAG files are visible (mounted via docker-compose volume)
echo ""
echo "📁 DAG files in /opt/airflow/dags:"
docker exec -it airflow ls -la /opt/airflow/dags/

# Step 4: Test imports
echo ""
echo "🔍 Testing DAG imports..."
docker exec -it airflow python -c "
import sys, os
sys.path.insert(0, '/opt/airflow/orchestration')
sys.path.insert(0, '/opt/airflow/ingestion')
sys.path.insert(0, '/opt/airflow/config')

try:
    from config import dag_config
    print('✅ dag_config imported successfully')
except Exception as e:
    print(f'❌ dag_config import failed: {e}')

dag_files = [
    '01_ingestion_dag.py',
    '02_silver_transform_dag.py',
    '03_gold_load_dag.py',
    '04_anomaly_detection_dag.py',
    '05_pipeline_monitor_dag.py'
]
for dag_file in dag_files:
    filepath = f'/opt/airflow/dags/{dag_file}'
    if os.path.exists(filepath):
        print(f'✅ {dag_file} exists')
    else:
        print(f'❌ {dag_file} missing')
"

# Step 5: Trigger DAG rescan
echo ""
echo "🔍 Triggering DAG rescan..."
docker exec -it airflow airflow dags reserialize
echo "✅ DAGs reserialized"

# Step 6: List loaded DAGs
echo ""
echo "📋 Loaded DAGs:"
docker exec -it airflow airflow dags list

# Step 7: Check for import errors
echo ""
echo "🔍 Checking for import errors..."
docker exec -it airflow airflow dags list-import-errors

echo ""
echo "=================================================="
echo "✅ AIRFLOW SETUP COMPLETE"
echo "=================================================="
echo ""
echo "🌐 Access Airflow UI: http://localhost:8080"
echo "   Username: admin"
echo "   Password: admin"
echo "=================================================="