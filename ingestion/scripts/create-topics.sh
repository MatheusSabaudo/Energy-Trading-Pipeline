#!/bin/bash
# ingestion/scripts/create-topics.sh

echo "Creating Kafka topics..."

# Create solar-raw topic
docker exec kafka /opt/kafka/bin/kafka-topics.sh \
    --create \
    --topic solar-raw \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1 \
    --if-not-exists

# List topics to verify
docker exec kafka /opt/kafka/bin/kafka-topics.sh \
    --list \
    --bootstrap-server localhost:9092

echo "Topic creation complete"