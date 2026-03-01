# FETCH THE DATA FROM THE API AND SEND TO THE POSTGRES DB

from confluent_kafka import Consumer, KafkaError  #Consumer Setup
import psycopg2
import json
import logging
import sys
import os

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..', 'config'))
import userdata_config as cfg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_CONF = {
    'bootstrap.servers': 'localhost:9093',
    'group.id': 'solar-api-consumer',
    'auto.offset.reset': 'earliest'
}

# PostgreSQL configuration
PG_CONFIG = {
    'dbname': 'solar_data',
    'user': 'airflow',
    'password': 'airflow',
    'host': 'localhost',
    'port': '5432'
}

consumer = Consumer(KAFKA_CONF)
consumer.subscribe(['solar-raw'])

def save_to_postgres(event):
    """Save event to PostgreSQL"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO solar_panel_readings 
            (event_id, timestamp, panel_id, panel_type, panel_power_kw, 
             production_kw, temperature_c, cloud_factor, temp_efficiency, status, city)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
        """, (
            event['event_id'], event['timestamp'], event['panel_id'],
            event.get('panel_type'), event.get('panel_power_kw'),
            event['production_kw'], event['temperature_c'],
            event.get('cloud_factor'), event.get('temp_efficiency'),
            event.get('status'), event.get('city', 'Turin')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Saved IoT data from: {event['panel_id']} to PostgreSQL")
    except Exception as e:
        logger.error(f"Error saving to PostgreSQL: {e}")

try:
    while True:
        msg = consumer.poll(1.0)
        
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            logger.error(f"Kafka error: {msg.error()}")
            break
        
        # Process message
        event = json.loads(msg.value().decode('utf-8'))
        save_to_postgres(event)

except KeyboardInterrupt:
    logger.info("Shutting down consumer...")
finally:
    consumer.close()