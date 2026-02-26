# consumers/test_consumer.py
from confluent_kafka import Consumer, KafkaError
import json
import sys
import os

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
import userdata_config as cfg

consumer = Consumer({
    'bootstrap.servers': 'localhost:9093',
    'group.id': 'test-group',
    'auto.offset.reset': 'earliest' # Get all the historical data from the producer
})

consumer.subscribe(['solar-raw'])

print("    Listening to solar-raw... (Ctrl+C to stop)")
print(f"   Using panel config: {cfg.PANEL_PARAMS['panel_power_kw']} kWp\n")

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() != KafkaError._PARTITION_EOF:
                print(f"Error: {msg.error()}")
            continue
        
        data = json.loads(msg.value().decode('utf-8'))
        print(f"   Received: {data['panel_id']} - {data['production_kw']} kW")
        print(f"   Time: {data['timestamp']}")
        print(f"   Temp: {data['temperature_c']}°C")
        print("-" * 40)
        
except KeyboardInterrupt:
    print("\nStopped")
finally:
    consumer.close()