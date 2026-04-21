# KAFKA PRODUCER

import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from confluent_kafka import Producer

project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import userdata_config as cfg
from solar_analysis_data.turin_model import TurinSimulationConfig, build_live_panel_event

KAFKA_CONF = {
    'bootstrap.servers': cfg.KAFKA_CONFIG['bootstrap.servers'],
    'enable.idempotence': True,
}

producer = None

PANEL_IDS = [
    f"IoT-Data-Panel-{i:03d}"
    for i in range(1, cfg.PANEL_PARAMS['panels'] + 1)
]
PANEL_POWER = cfg.PANEL_PARAMS['panel_power_kw']
CITY = "Turin"
TOPIC = cfg.KAFKA_CONFIG['topic']
SIM_CONFIG = TurinSimulationConfig(system_size_kw=PANEL_POWER)


def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def get_producer():
    global producer
    if producer is None:
        producer = Producer(KAFKA_CONF)
    return producer


def generate_solar_event(panel_id):
    simulated = build_live_panel_event(panel_id=panel_id, config=SIM_CONFIG)

    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "panel_id": simulated["panel_id"],
        "panel_type": cfg.PANEL_PARAMS.get('panel_type', 'Monocrystalline'),
        "panel_power_kw": simulated["panel_power_kw"],
        "production_kw": simulated["production_kw"],
        "temperature_c": simulated["temperature_c"],
        "cloud_factor": simulated["cloud_factor"],
        "temp_efficiency": simulated["temp_efficiency"],
        "status": simulated["status"],
        "city": simulated["city"],
    }


def main():
    print(" Solar Panel Data Producer Started")
    print(f"   City: {CITY}")
    print(f"   Panel power: {PANEL_POWER} kWp")
    print(f"   System losses: {cfg.LOSS_PARAMS.get('system_losses', 0.14) * 100:.0f}%")
    print(f"   Connecting to Kafka at {KAFKA_CONF['bootstrap.servers']}")
    print("   Press Ctrl+C to stop\n")

    try:
        active_producer = get_producer()
        while True:
            for panel_id in PANEL_IDS:
                event = generate_solar_event(panel_id)
                message = json.dumps(event)

                active_producer.produce(
                    topic=TOPIC,
                    key=panel_id,
                    value=message,
                    callback=delivery_report,
                )
                active_producer.poll(0)

                print(f"Sent: {panel_id} - {event['production_kw']} kW\n")
                time.sleep(0.1)

            active_producer.flush()
            print("Batch sent, waiting 5 seconds...\n")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutting down producer...")
    finally:
        if producer is not None:
            producer.flush()


if __name__ == "__main__":
    main()
