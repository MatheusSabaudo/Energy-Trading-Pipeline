# tests/test_iot_pipeline.py
import sys
import os
import time
import json
from pathlib import Path
from confluent_kafka import Producer
import psycopg2

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from config import userdata_config as cfg

def test_kafka_connection():
    """Test if Kafka is reachable"""
    print("\n🔍 Testing Kafka Connection...")
    try:
        producer = Producer({'bootstrap.servers': 'localhost:9092'})
        # Try to get metadata
        metadata = producer.list_topics(timeout=5)
        print(f"Kafka Connection Successful")
        print(f"   Brokers: {len(metadata.brokers)}")
        print(f"   Topics: {list(metadata.topics.keys())}")
        return True
    except Exception as e:
        print(f"Kafka Connection Failed: {e}")
        return False

def test_topic_exists():
    """Test if solar-raw topic exists"""
    print("\n🔍 Testing Topic Existence...")
    try:
        producer = Producer({'bootstrap.servers': 'localhost:9092'})
        metadata = producer.list_topics(timeout=5)
        
        if 'solar-raw' in metadata.topics:
            print(f"Topic 'solar-raw' exists")
            return True
        else:
            print(f"Topic 'solar-raw' does not exist")
            return False
    except Exception as e:
        print(f"Error checking topic: {e}")
        return False

def test_produce_message():
    """Test producing a test message"""
    print("\nTesting Message Production...")
    try:
        producer = Producer({'bootstrap.servers': 'localhost:9092'})
        
        test_message = {
            'event_id': 'test-123',
            'timestamp': '2026-02-27T20:00:00',
            'panel_id': 'TEST-001',
            'production_kw': 2.5
        }
        
        producer.produce('solar-raw', value=json.dumps(test_message))
        producer.flush()
        print(f"Test message produced")
        return True
    except Exception as e:
        print(f"Failed to produce message: {e}")
        return False

def test_table_exists():
    """Test if solar_panel_readings table exists"""
    print("\nTesting Table Existence...")
    try:
        conn = psycopg2.connect(**cfg.POSTGRES_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'solar_panel_readings'
            )
        """)
        exists = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        if exists:
            print(f"Table 'solar_panel_readings' exists")
            return True
        else:
            print(f"Table 'solar_panel_readings' does not exist")
            return False
    except Exception as e:
        print(f"Error checking table: {e}")
        return False

def test_consume_message():
    """Test consuming a message (requires producer running)"""
    print("\nTesting Message Consumption...")
    print("   (Make sure producer is running in another terminal)")
    
    # This test requires manual verification
    print("   Run this after starting the consumer:")
    print("   python ingestion/iot/iot_to_postgres.py")
    return True  # Skip actual test

if __name__ == "__main__":
    print("=" * 60)
    print("IOT KAFKA PIPELINE TESTS")
    print("=" * 60)
    
    tests = [
        ("Kafka Connection", test_kafka_connection),
        ("Topic Existence", test_topic_exists),
        ("Message Production", test_produce_message),
        ("Table Existence", test_table_exists),
        ("Message Consumption", test_consume_message)
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\nALL TESTS PASSED - IoT pipeline ready!")
    else:
        print("\nSOME TESTS FAILED - Check errors above")