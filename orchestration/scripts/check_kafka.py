#!/usr/bin/env python3
"""
Kafka Health Check Script
Checks if Kafka is running and topics exist
Works both inside Docker containers and on host machine
"""

import os
import socket
import sys
from confluent_kafka import Producer

def is_running_in_docker():
    """Detect if we're running inside a Docker container"""
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        return False

# Set the correct broker based on environment
IN_DOCKER = is_running_in_docker()
KAFKA_BROKER = 'kafka:9092' if IN_DOCKER else 'localhost:9093'

def check_kafka_connection(broker=KAFKA_BROKER, timeout=5):
    """Check if Kafka broker is reachable"""
    try:
        # Test socket connection first
        host, port = broker.split(':')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        
        if result != 0:
            print(f"❌ Cannot connect to Kafka at {broker}")
            return False
        
        # Try to create a test producer
        producer = Producer({'bootstrap.servers': broker})
        # Try to get metadata
        metadata = producer.list_topics(timeout=timeout)
        print(f"✅ Kafka broker at {broker} is reachable")
        return True
        
    except Exception as e:
        print(f"❌ Kafka connection failed: {e}")
        return False

def check_topic_exists(topic='solar-raw', broker=KAFKA_BROKER):
    """Check if required topics exist"""
    try:
        producer = Producer({'bootstrap.servers': broker})
        metadata = producer.list_topics(timeout=5)
        
        topics = list(metadata.topics.keys())
        if topic in topics:
            print(f"✅ Topic '{topic}' exists")
            return True
        else:
            print(f"❌ Topic '{topic}' does not exist")
            print(f"   Available topics: {topics}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to list topics: {e}")
        return False

def check_kafka_health():
    """Main health check function"""
    print("\n" + "="*50)
    print("KAFKA HEALTH CHECK")
    print("="*50)
    print(f"Environment: {'🐳 Docker' if IN_DOCKER else '💻 Host'}")
    print(f"Target: {KAFKA_BROKER}")
    print("="*50)
    
    # Check connection
    if not check_kafka_connection():
        return 1
    
    # Check topics
    topics_to_check = ['solar-raw']
    all_topics_ok = True
    
    for topic in topics_to_check:
        if not check_topic_exists(topic):
            all_topics_ok = False
    
    print("\n" + "="*50)
    if all_topics_ok:
        print("✅ All Kafka checks passed")
        return 0
    else:
        print("❌ Some Kafka checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(check_kafka_health())