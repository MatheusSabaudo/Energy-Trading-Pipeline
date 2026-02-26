# monitor_enhanced.py
import subprocess
import json
from datetime import datetime, timedelta
import sys
import os

def check_containers():
    """Check if all Docker containers are running"""
    print("\nCONTAINER STATUS:")
    print("-" * 40)
    
    result = subprocess.run(
        ['docker', 'compose', 'ps', '--format', 'json'],
        capture_output=True,
        text=True
    )
    
    containers = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                containers.append(json.loads(line))
            except:
                pass
    
    running = [c for c in containers if c.get('State') == 'running']
    print(f"Running: {len(running)}/{len(containers)}")
    
    for c in containers:
        status_icon = "[OK]" if c.get('State') == 'running' else "[ERROR]"
        name = c.get('Name', '')
        print(f"   {status_icon} {name:20} {c.get('State', 'unknown')}")

def check_kafka():
    """Detailed Kafka checks"""
    print("\nKAFKA STATUS:")
    print("-" * 40)
    
    result = subprocess.run(
        ['docker', 'exec', 'kafka', '/opt/kafka/bin/kafka-broker-api-versions.sh',
         '--bootstrap-server', 'localhost:9092'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] Kafka broker is reachable")
    else:
        print("[ERROR] Cannot connect to Kafka broker")
        return
    
    result = subprocess.run(
        ['docker', 'exec', 'kafka', '/opt/kafka/bin/kafka-topics.sh',
         '--list', '--bootstrap-server', 'localhost:9092'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        topics = [t for t in result.stdout.strip().split('\n') if t]
        print(f"Topics: {', '.join(topics) if topics else 'None'}")
        
        if 'solar-raw' in topics:
            result = subprocess.run(
                ['docker', 'exec', 'kafka', '/opt/kafka/bin/kafka-get-offsets.sh',
                 '--bootstrap-server', 'localhost:9092',
                 '--topic', 'solar-raw'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                total_messages = 0
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) == 3:
                            total_messages += int(parts[2])
                print(f"solar-raw: {total_messages} messages")
            else:
                print("[WARN] Could not get message count")
        else:
            print("[WARN] Topic 'solar-raw' not found")

def check_postgres():
    """Detailed PostgreSQL checks"""
    print("\nPOSTGRESQL STATUS:")
    print("-" * 40)
    
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'pg_isready', '-U', 'airflow'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] PostgreSQL is accepting connections")
    else:
        print("[ERROR] PostgreSQL not responding")
        return
    
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'psql', '-U', 'airflow', '-d', 'airflow',
         '-c', "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'solar_panel_readings')"],
        capture_output=True,
        text=True
    )
    
    if 't' in result.stdout:
        print("[OK] Table 'solar_panel_readings' exists")
        
        result = subprocess.run(
            ['docker', 'exec', 'postgres', 'psql', '-U', 'airflow', '-d', 'airflow',
             '-t', '-c', 'SELECT COUNT(*) FROM solar_panel_readings'],
            capture_output=True,
            text=True
        )
        count = result.stdout.strip()
        print(f"Records: {count}")
        
        result = subprocess.run(
            ['docker', 'exec', 'postgres', 'psql', '-U', 'airflow', '-d', 'airflow',
             '-t', '-c', "SELECT MAX(timestamp) FROM solar_panel_readings"],
            capture_output=True,
            text=True
        )
        
        latest = result.stdout.strip()
        if latest and latest != ' ':
            print(f"Latest record: {latest[:19]}")
            
            try:
                latest_time = datetime.fromisoformat(latest.replace(' ', 'T').split('+')[0])
                delay = datetime.now() - latest_time
                if delay < timedelta(minutes=1):
                    print("[OK] Real-time: Data is current")
                elif delay < timedelta(minutes=5):
                    print(f"[WARN] Delay: {delay.seconds} seconds")
                else:
                    print(f"[INFO] Stale: {int(delay.total_seconds())} seconds old")
            except Exception as e:
                print(f"[WARN] Could not parse timestamp: {e}")
    else:
        print("[ERROR] Table 'solar_panel_readings' missing")

def check_producer():
    """Check if producer is running"""
    print("\nPRODUCER STATUS:")
    print("-" * 40)
    
    result = subprocess.run(
        ['pgrep', '-f', 'solar_producer.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] Producer is running")
    else:
        print("[PAUSED] Producer not running (start with: python3 producers/solar_producer.py)")

def check_consumers():
    """Check if consumers are running"""
    print("\nCONSUMER STATUS:")
    print("-" * 40)
    
    result = subprocess.run(
        ['pgrep', '-f', 'test_consumer.py'],
        capture_output=True,
        text=True
    )
    print("[OK] Test consumer is running" if result.returncode == 0 else "[PAUSED] Test consumer not running")
    
    result = subprocess.run(
        ['pgrep', '-f', 'kafka_to_postgres.py'],
        capture_output=True,
        text=True
    )
    print("[OK] PostgreSQL consumer is running" if result.returncode == 0 else "[PAUSED] PostgreSQL consumer not running")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(f"PIPELINE MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    check_containers()
    check_kafka()
    check_postgres()
    check_producer()
    check_consumers()
    
    print("\n" + "=" * 60)
    print("Monitor complete")
    print("=" * 60)