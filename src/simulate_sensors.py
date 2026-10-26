import json
import csv
import random
import time
from pathlib import Path
from datetime import datetime, timezone
from awscrt import mqtt
from awsiot import mqtt_connection_builder
import boto3
import os

BASE = Path.home() / "agrosense-iot"
CERTS = BASE / "certs"
DATA = BASE / "data"
DATA.mkdir(parents=True, exist_ok=True)

iot = boto3.client("iot", region_name="eu-north-1")
endpoint = iot.describe_endpoint(
    endpointType="iot:Data-ATS"
)["endpointAddress"]

# Select the simulator identity explicitly. Never use the Grafana certificate here.
# Defaults match the original CloudShell certificate filenames; override with
# environment variables if the filenames differ.
certificate = Path(os.environ.get("AGROSENSE_CERT", str(CERTS / "certificate.pem.crt")))
private_key = Path(os.environ.get("AGROSENSE_KEY", str(CERTS / "private.pem.key")))
if not certificate.is_file() or not private_key.is_file():
    raise FileNotFoundError(
        "Simulator certificate/key missing. Set AGROSENSE_CERT and "
        "AGROSENSE_KEY to the original simulator identity files."
    )

connection = mqtt_connection_builder.mtls_from_path(
    endpoint=endpoint,
    cert_filepath=str(certificate),
    pri_key_filepath=str(private_key),
    client_id="AgroSense-Farm1-Sensor01",
    clean_session=True,
    keep_alive_secs=30
)

print("Connecting securely to AWS IoT Core...")
connection.connect().result()
print("MQTT connection successful!")

readings = []
logs = []

for farm in range(1, 4):
    for sample in range(1, 6):
        now = datetime.now(timezone.utc).isoformat()

        reading = {
            "device_id": "AgroSense-Farm1-Sensor01",
            "farm_id": f"farm{farm}",
            "sample_id": sample,
            "temperature": round(random.uniform(20, 38), 2),
            "humidity": round(random.uniform(35, 85), 2),
            "soil_moisture": round(random.uniform(20, 75), 2),
            "status": "connected"
        }

        start = time.perf_counter()
        connection.publish(
            topic=f"agrosense/farm{farm}/telemetry",
            payload=json.dumps(reading),
            qos=mqtt.QoS.AT_LEAST_ONCE
        )[0].result()
        latency = round((time.perf_counter() - start) * 1000, 2)

        readings.append(reading)
        logs.append({
            "farm_id": reading["farm_id"],
            "timestamp": now,
            "status": "published",
            "publish_ack_latency_ms": latency
        })

        print(f"Published farm{farm} sample {sample}")
        time.sleep(0.5)

with open(DATA / "sensor_readings.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=readings[0].keys())
    writer.writeheader()
    writer.writerows(readings)

with open(DATA / "monitoring_logs.json", "w") as f:
    json.dump(logs, f, indent=2)

connection.disconnect().result()

print("SUCCESS: 15 MQTT messages published")
print("SUCCESS: Both datasets created")
