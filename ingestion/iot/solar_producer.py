# ingestion/iot/solar_producer.py
import json
import time
import uuid
import random
from datetime import datetime, timezone
from confluent_kafka import Producer
import sys
import os
from pathlib import Path

# Add project root to path - FIX THIS
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Now import works
from config import userdata_config as cfg

# Kafka configuration - FIXED VERSION
KAFKA_CONF = {
    'bootstrap.servers': 'localhost:9093',  # ONLY localhost
    'enable.idempotence': False,  
}

producer = Producer(KAFKA_CONF)

# Use values from your config
PANEL_IDS = [f"IoT-Data-Panel-{i:03d}" for i in range(1, cfg.PANEL_PARAMS['panels'])] # Name the panel with an ID (i) in range of the panels installed
PANEL_POWER = cfg.PANEL_PARAMS['panel_power_kw']
CITY = "Turin"

def delivery_report(err, msg):
    """Callback for message delivery"""
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def generate_solar_event(panel_id):
    """Generate realistic solar production data using config values"""
    current_hour = datetime.now().hour
    
    # Solar angle factor (peak at noon) - range 0 to 1
    solar_factor = max(0, 1 - abs(current_hour - 12) / 12)
    
    # Base production using your panel parameters from config
    base_production = PANEL_POWER * solar_factor
    
    # Add realistic variations
    cloud_factor = random.uniform(0.7, 1.0)
    temp = random.uniform(15, 30)
    
    # Temperature efficiency loss
    if temp > 25:
        temp_efficiency = 1 - (temp - 25) * cfg.PANEL_PARAMS['temp_loss_coeff']
    else:
        temp_efficiency = 1.0
    
    # System losses
    system_losses = cfg.PANEL_PARAMS.get('system_losses', 0.14)
    
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
        "city": CITY
    }

def main():
    print(" Solar Panel Data Producer Started")
    print(f"   City: {CITY}")
    print(f"   Panel power: {PANEL_POWER} kWp")
    print(f"   System losses: {cfg.PANEL_PARAMS.get('system_losses', 0.14)*100:.0f}%")
    print(f"   Connecting to Kafka at localhost:9092")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        while True:
            for panel_id in PANEL_IDS:
                # Generate event -> each panel have different values
                event = generate_solar_event(panel_id)
                
                # Serialize to JSON
                message = json.dumps(event)
                
                # Produce message (use panel_id as key for partitioning)
                producer.produce(
                    topic='solar-raw',
                    key=panel_id,
                    value=message,
                    callback=delivery_report
                )
                
                # Trigger delivery reports
                producer.poll(0)
                
                print(f"Sent: {panel_id} - {event['production_kw']} kW\n")
                
                # Small delay between messages
                time.sleep(0.1)
            
            # Flush every batch
            producer.flush()
            print("Batch sent, waiting 5 seconds...\n")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nShutting down producer...")
    finally:
        # Flush remaining messages
        producer.flush()

if __name__ == "__main__":
    main()