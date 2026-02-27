#!/bin/bash

TOPICS=(
    "solar-raw:3:1"           # topic:partitions:replicas
    "solar-processed:3:1"
    "solar-anomalies:2:1"
    "solar-aggregates:3:1"
    "weather-raw:1:1"
)

for topic_config in "${TOPICS[@]}"; do
    IFS=':' read -r topic partitions replicas <<< "$topic_config"
    
    echo "Creating topic: $topic (partitions: $partitions, replicas: $replicas)"
    
    docker exec kafka /opt/kafka/bin/kafka-topics.sh \
        --create \
        --topic "$topic" \
        --bootstrap-server localhost:9092 \
        --partitions "$partitions" \
        --replication-factor "$replicas" \
        --if-not-exists
done

echo "INFO: All topics created!"