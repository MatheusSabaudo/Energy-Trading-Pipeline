# FETCH DATA FROM THE IOT DEVICES AND SEND TO THE POSTGRES DB

import json
import logging
import sys
from pathlib import Path

import psycopg2
from confluent_kafka import Consumer, KafkaError
from psycopg2.extras import execute_batch

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import userdata_config as cfg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

KAFKA_CONF = {
    'bootstrap.servers': cfg.KAFKA_CONFIG['bootstrap.servers'],
    'group.id': 'solar-iot-consumer',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': False,
    'session.timeout.ms': 30000,
    'heartbeat.interval.ms': 10000,
    'max.poll.interval.ms': 300000,
}

DB_CONFIG = cfg.POSTGRES_CONFIG


class IoTConsumer:
    def __init__(self):
        self.consumer = Consumer(KAFKA_CONF)
        self.topic = cfg.KAFKA_CONFIG['topic']
        self.consumer.subscribe([self.topic])
        self.message_count = 0
        self.error_count = 0
        self.batch_size = 100
        self.current_batch = []

        logger.info("=" * 60)
        logger.info("IOT KAFKA CONSUMER INITIALIZED")
        logger.info("=" * 60)
        logger.info("Kafka brokers: %s", KAFKA_CONF['bootstrap.servers'])
        logger.info("Consumer group: %s", KAFKA_CONF['group.id'])
        logger.info("Subscribed to topic: %s", self.topic)
        logger.info("Writing to table: solar_panel_readings")

    def process_message(self, msg):
        try:
            data = json.loads(msg.value().decode('utf-8'))
            required_fields = ['event_id', 'timestamp', 'panel_id', 'production_kw']
            for field in required_fields:
                if field not in data:
                    logger.error("Missing required field: %s", field)
                    self.error_count += 1
                    return False

            self.current_batch.append(data)
            if len(self.current_batch) >= self.batch_size:
                self.flush_batch()

            self.message_count += 1
            if self.message_count % 10 == 0:
                logger.info("Processed %s messages, Errors: %s", self.message_count, self.error_count)

            return True

        except json.JSONDecodeError as exc:
            logger.error("JSON decode error: %s", exc)
            self.error_count += 1
            return False
        except Exception as exc:
            logger.error("Error processing message: %s", exc)
            self.error_count += 1
            return False

    def flush_batch(self):
        if not self.current_batch:
            return

        conn = None
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            insert_query = """
                INSERT INTO solar_panel_readings (
                    event_id, timestamp, panel_id, panel_type,
                    panel_power_kw, production_kw, temperature_c,
                    cloud_factor, temp_efficiency, status, city
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
            """

            batch_data = [
                (
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
                    data.get('city', 'Turin'),
                )
                for data in self.current_batch
            ]

            execute_batch(cur, insert_query, batch_data, page_size=min(len(batch_data), self.batch_size))
            conn.commit()
            self.consumer.commit(asynchronous=False)

            logger.info("Batch inserted: %s records", len(self.current_batch))
            self.current_batch = []
            cur.close()
            conn.close()

        except Exception as exc:
            logger.error("Error inserting batch: %s", exc)
            if conn is not None:
                conn.rollback()
                conn.close()

    def run(self):
        logger.info("=" * 60)
        logger.info("IOT KAFKA CONSUMER STARTED")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop\n")

        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    if self.current_batch:
                        self.flush_batch()
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error("Kafka error: %s", msg.error())
                    self.error_count += 1
                    continue

                self.process_message(msg)

        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("SHUTTING DOWN CONSUMER")
            logger.info("=" * 60)

        finally:
            if self.current_batch:
                logger.info("Flushing final batch of %s messages...", len(self.current_batch))
                self.flush_batch()

            self.consumer.close()
            logger.info("=" * 60)
            logger.info("FINAL STATISTICS")
            logger.info("=" * 60)
            logger.info("Total messages processed: %s", self.message_count)
            logger.info("Total errors: %s", self.error_count)
            if self.message_count > 0:
                success_rate = (self.message_count - self.error_count) / self.message_count * 100
                logger.info("Success rate: %.1f%%", success_rate)
            logger.info("=" * 60)


def main():
    consumer = IoTConsumer()
    consumer.run()


if __name__ == "__main__":
    main()
