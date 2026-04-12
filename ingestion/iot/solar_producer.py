# KAFKA PRODUCER

import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from confluent_kafka import Producer

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import userdata_config as cfg

KAFKA_CONF = {
    'bootstrap.servers': cfg.KAFKA_CONFIG['bootstrap.servers'],
    'enable.idempotence': True,
}

producer = Producer(KAFKA_CONF)

PANEL_IDS = [
    f"IoT-Data-Panel-{i:03d}"
    for i in range(1, cfg.PANEL_PARAMS['panels'] + 1)
]
PANEL_POWER = cfg.PANEL_PARAMS['panel_power_kw']
CITY = "Turin"
TOPIC = cfg.KAFKA_CONFIG['topic']


def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def generate_solar_event(panel_id):
    current_hour = datetime.now().hour
    solar_factor = max(0, 1 - abs(current_hour - 12) / 12)
    base_production = PANEL_POWER * solar_factor

    cloud_factor = random.uniform(0.7, 1.0)
    temp = random.uniform(15, 30)

    if temp > 25:
        temp_efficiency = 1 - (temp - 25) * cfg.PANEL_PARAMS['temp_loss_coeff']
    else:
        temp_efficiency = 1.0

    system_losses = cfg.LOSS_PARAMS.get('system_losses', 0.14)
    actual_production = base_production * cloud_factor * temp_efficiency * (1 - system_losses)

    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "panel_id": panel_id,
        "panel_type": cfg.PANEL_PARAMS.get('panel_type', 'Monocrystalline'),
        "panel_power_kw": PANEL_POWER,
        "production_kw": round(actual_production, 3),
        "temperature_c": round(temp, 1),
        "cloud_factor": round(cloud_factor, 2),
        "temp_efficiency": round(temp_efficiency, 3),
        "status": "active",
        "city": CITY,
    }


def main():
    print(" Solar Panel Data Producer Started")
    print(f"   City: {CITY}")
    print(f"   Panel power: {PANEL_POWER} kWp")
    print(f"   System losses: {cfg.LOSS_PARAMS.get('system_losses', 0.14) * 100:.0f}%")
    print(f"   Connecting to Kafka at {KAFKA_CONF['bootstrap.servers']}")
    print("   Press Ctrl+C to stop\n")

    try:
        while True:
            for panel_id in PANEL_IDS:
                event = generate_solar_event(panel_id)
                message = json.dumps(event)

                producer.produce(
                    topic=TOPIC,
                    key=panel_id,
                    value=message,
                    callback=delivery_report,
                )
                producer.poll(0)

                print(f"Sent: {panel_id} - {event['production_kw']} kW\n")
                time.sleep(0.1)

            producer.flush()
            print("Batch sent, waiting 5 seconds...\n")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutting down producer...")
    finally:
        producer.flush()


if __name__ == "__main__":
    main()
