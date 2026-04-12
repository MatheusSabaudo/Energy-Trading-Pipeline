#!/usr/bin/env python3
"""
Kafka Health Check Script
Checks if Kafka is running and required topics exist.
Compatible both inside Docker containers and on host machine.
"""

import os
import socket
import sys
from confluent_kafka import Producer

# -----------------------------
# Detect Docker environment
# -----------------------------
def is_running_in_docker():
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        return 'DOCKER_CONTAINER' in os.environ

IN_DOCKER = is_running_in_docker()
KAFKA_BROKER = 'kafka:9092' if IN_DOCKER else 'localhost:9093'

# -----------------------------
# Check Kafka broker connection
# -----------------------------
def check_kafka_connection(broker=KAFKA_BROKER, timeout=5):
    """Check if Kafka broker is reachable"""
    try:
        host, port = broker.split(':')
        port = int(port)
        # socket test
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        if result != 0:
            print(f"❌ Cannot connect to Kafka at {broker}")
            return False
        
        # Test producer metadata
        producer = Producer({'bootstrap.servers': broker})
        _ = producer.list_topics(timeout=timeout)
        print(f"✅ Kafka broker at {broker} is reachable")
        return True
    except Exception as e:
        print(f"❌ Kafka connection failed: {e}")
        return False

# -----------------------------
# Check required topics exist
# -----------------------------
def check_topic_exists(topic, broker=KAFKA_BROKER):
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

# -----------------------------
# Main Kafka health check
# -----------------------------
def check_kafka_health():
    print("\n" + "="*50)
    print("KAFKA HEALTH CHECK")
    print("="*50)
    print(f"Environment: {'Docker' if IN_DOCKER else 'Host'}")
    print(f"Target broker: {KAFKA_BROKER}")
    print("="*50)

    if not check_kafka_connection():
        print("\n❌ Kafka broker unreachable")
        return 1

    topics_to_check = ['solar-raw']
    all_ok = True
    for topic in topics_to_check:
        if not check_topic_exists(topic):
            all_ok = False

    print("\n" + "="*50)
    if all_ok:
        print("✅ All Kafka checks passed")
        return 0
    else:
        print("❌ Kafka health check failed")
        return 1

# -----------------------------
# Run as script
# -----------------------------
if __name__ == "__main__":
    sys.exit(check_kafka_health())