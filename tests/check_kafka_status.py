# check_kafka_status.py
import subprocess
import json

def check_docker():
    print("🔍 Checking Docker containers...")
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    if 'kafka' in result.stdout:
        print("✅ Kafka container is running")
    else:
        print("❌ Kafka container NOT running")
        
    if 'postgres' in result.stdout:
        print("✅ PostgreSQL container is running")
    else:
        print("❌ PostgreSQL container NOT running")

def check_kafka():
    print("\n🔍 Testing Kafka connection...")
    result = subprocess.run(
        ['docker', 'exec', 'kafka', '/opt/kafka/bin/kafka-topics.sh', 
         '--list', '--bootstrap-server', 'localhost:9092'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ Kafka is accessible")
        print(f"   Topics: {result.stdout.strip()}")
    else:
        print("❌ Cannot connect to Kafka")
        print(f"   Error: {result.stderr}")

if __name__ == "__main__":
    print("=" * 60)
    print("KAFKA STATUS CHECK")
    print("=" * 60)
    check_docker()
    check_kafka()