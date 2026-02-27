# ingestion/iot/iot_to_postgres.py
from confluent_kafka import Consumer, KafkaError
import psycopg2
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import userdata_config as cfg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# KAFKA CONFIGURATION - FIXED VERSION
# ============================================
KAFKA_CONF = {
    'bootstrap.servers': 'localhost:9093',
    'group.id': 'solar-iot-consumer',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'session.timeout.ms': 30000,
    'heartbeat.interval.ms': 10000,
    'max.poll.interval.ms': 300000
}

# ============================================
# DATABASE CONFIGURATION
# ============================================
DB_CONFIG = cfg.POSTGRES_CONFIG

class IoTConsumer:
    def __init__(self):
        """Initialize the Kafka consumer"""
        self.consumer = Consumer(KAFKA_CONF)
        self.consumer.subscribe(['solar-raw'])
        self.message_count = 0
        self.error_count = 0
        self.batch_size = 100
        self.current_batch = []
        
        logger.info("=" * 60)
        logger.info("IOT KAFKA CONSUMER INITIALIZED")
        logger.info("=" * 60)
        logger.info(f"Kafka brokers: {KAFKA_CONF['bootstrap.servers']}")
        logger.info(f"Consumer group: {KAFKA_CONF['group.id']}")
        logger.info(f"Subscribed to topic: solar-raw")
        logger.info(f"Writing to table: solar_panel_readings")
        
    def process_message(self, msg):
        """Process a single Kafka message"""
        try:
            # Parse JSON
            data = json.loads(msg.value().decode('utf-8'))
            
            # Validate required fields
            required_fields = ['event_id', 'timestamp', 'panel_id', 'production_kw']
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    self.error_count += 1
                    return False
            
            # Add to batch
            self.current_batch.append(data)
            
            # Process batch if size reached
            if len(self.current_batch) >= self.batch_size:
                self.flush_batch()
            
            self.message_count += 1
            if self.message_count % 10 == 0:
                logger.info(f"Processed {self.message_count} messages, Errors: {self.error_count}")
                
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            self.error_count += 1
            return False
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.error_count += 1
            return False
    
    def flush_batch(self):
        """Insert batch of messages into PostgreSQL"""
        if not self.current_batch:
            return
        
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            # Prepare batch insert
            insert_query = """
                INSERT INTO solar_panel_readings (
                    event_id, timestamp, panel_id, panel_type,
                    panel_power_kw, production_kw, temperature_c,
                    cloud_factor, temp_efficiency, status, city
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
            """
            
            batch_data = []
            for data in self.current_batch:
                batch_data.append((
                    data.get('event_id'),
                    data.get('timestamp'),
                    data.get('panel_id'),
                    data.get('panel_type'),
                    data.get('panel_power_kw'),
                    data.get('production_kw'),
                    data.get('temperature_c'),
                    data.get('cloud_factor'),
                    data.get('temp_efficiency'),
                    data.get('status', 'active'),
                    data.get('city', 'Turin')
                ))
            
            # Execute batch insert
            cur.executemany(insert_query, batch_data)
            conn.commit()
            
            logger.info(f"Batch inserted: {len(self.current_batch)} records")
            self.current_batch = []
            
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error inserting batch: {e}")
            # Don't clear batch on error - could retry later
            if conn:
                conn.rollback()
                conn.close()
    
    def run(self):
        """Main consumer loop"""
        logger.info("=" * 60)
        logger.info("IOT KAFKA CONSUMER STARTED")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Poll for messages (timeout 1 second)
                msg = self.consumer.poll(1.0)
                
                if msg is None:
                    # No message received, continue polling
                    continue
                    
                if msg.error():
                    # Handle errors
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition, normal behavior
                        continue
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        self.error_count += 1
                        continue
                
                # Process message
                self.process_message(msg)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("SHUTTING DOWN CONSUMER")
            logger.info("=" * 60)
            
        finally:
            # Flush any remaining messages
            if self.current_batch:
                logger.info(f"Flushing final batch of {len(self.current_batch)} messages...")
                self.flush_batch()
            
            # Close consumer
            self.consumer.close()
            
            # Final statistics
            logger.info("=" * 60)
            logger.info("FINAL STATISTICS")
            logger.info("=" * 60)
            logger.info(f"Total messages processed: {self.message_count}")
            logger.info(f"Total errors: {self.error_count}")
            if self.message_count > 0:
                success_rate = (self.message_count - self.error_count) / self.message_count * 100
                logger.info(f"Success rate: {success_rate:.1f}%")
            logger.info("=" * 60)

def main():
    """Main entry point"""
    consumer = IoTConsumer()
    consumer.run()

if __name__ == "__main__":
    main()