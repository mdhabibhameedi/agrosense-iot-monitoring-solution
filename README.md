# AgroSense — Network and IoT Solution (Modular Assignment 5)

**Cloud Computing | Amity University Online | October 2026**  
**AWS Region:** `eu-north-1` (Stockholm)

A working three-farm smart-agriculture **simulation** that securely publishes soil-moisture, temperature and humidity readings through **AWS IoT Core MQTT**, persists them to **Amazon DynamoDB**, and shows **live MQTT telemetry in Grafana**. **Power BI** provides supplementary analysis of exported CSV/JSON data (not a live AWS connection).

## Architecture

![AgroSense AWS IoT Architecture](docs/AgroSense%20AWS%20IoT%20Architecture%20Diagram.png)

**Implemented data paths**

1. One Python simulator / logical gateway publishes data representing **three farms**. It uses one simulator AWS IoT identity; the farms are *not* three separately registered physical devices.
2. **MQTT over TLS (port 8883), X.509 certificate** → AWS IoT Core managed MQTT broker. Topics: `agrosense/farm1/telemetry`, `agrosense/farm2/telemetry`, `agrosense/farm3/telemetry`.
3. IoT Rule `AgroSense_Sensor_Data_Rule` matches `agrosense/+/telemetry` and writes to `AgroSense-SensorReadings` via **DynamoDBv2** and a dedicated IAM role.
4. **Grafana** uses its **own X.509 certificate** and read-only IoT policy to subscribe to `agrosense/+/telemetry`, showing messages *as they arrive* (not historical replay).
5. **Power BI Desktop** visualizes the exported `sensor_readings.csv` and `monitoring_logs.json` datasets; it is **not connected live to DynamoDB**.

## Repository contents

| Location | Contents |
|---|---|
| `src/simulate_sensors.py` | MQTT-over-TLS simulator; 15 readings, 5 per farm, and two generated datasets |
| `data/` | Sensor CSV and publish-ack monitoring JSON (15 records each) |
| `config/` | IoT policy **examples** with `ACCOUNT_ID` placeholder, rule SQL, DynamoDB schema |
| `docs/` | Architecture and assignment report |
| `docs/screenshots/` | Numbered AWS, Power BI, Grafana and scalability evidence |
| `AgroSense-IoT-Monitoring-Dashboard.pbix` | Power BI Desktop project |

## Reproduce the sensor simulator

**Prerequisites:** Python 3.10+, AWS CloudShell or another authenticated AWS environment, AWS IoT Core Thing and active simulator certificate/private key **stored outside this repository**, IoT policies, DynamoDB table and IoT Rule. IAM permissions for `iot:DescribeEndpoint` are needed to discover the endpoint.

```bash
python3 -m pip install -r requirements.txt
```

The script expects the **original simulator** certificate/key in `~/agrosense-iot/certs/`. To use other filenames, set:

```bash
export AGROSENSE_CERT="$HOME/agrosense-iot/certs/YOUR_SIMULATOR_CERT.pem.crt"
export AGROSENSE_KEY="$HOME/agrosense-iot/certs/YOUR_SIMULATOR_PRIVATE.pem.key"
python3 src/simulate_sensors.py
```

**Never commit certificate/key contents, IAM credentials, or secrets.** The `certs/` directory and private-key extensions are ignored in `.gitignore`. The source uses explicit certificate paths to prevent accidentally choosing the separate Grafana identity.

The simulator publishes 15 JSON MQTT readings (QoS 1) across three farm topics, records MQTT publish acknowledgement latency, and writes `~/agrosense-iot/data/sensor_readings.csv` and `monitoring_logs.json`. The acknowledgement latency is **not** an end-to-end DynamoDB latency measurement.

## Verified results

| Test | Evidence / outcome |
|---|---|
| X.509 + TLS MQTT publish | Successful Python simulator output |
| Cloud ingestion | AWS IoT Core rule routed readings into DynamoDB |
| Three-farm data | 15 readings per simulator run (5 per farm) |
| Live Grafana | Incoming telemetry observed without browser refresh |
| Independent identities | Dedicated Grafana subscribe-only certificate and simulator publish-only policy |
| Load test | 100 AWS IoT Data Plane API publishes in **1.17 s** (approx. **85.5 publishes/s**) |
| Database verification | **100/100** load-test items found in DynamoDB (`ScannedCount=227`) |

**Scope:** The load test uses the AWS IoT Data Plane API from CloudShell, **not** the simulator's MQTT-over-TLS client, and does not establish maximum throughput or end-to-end ingestion latency. The 100 test items had distinct `device_id` values.

## Evidence screenshots

| # | Screenshot |
|---|---|
| 01 | [AWS IoT Thing registration](docs/screenshots/01-IoT-Device-Registration.png) |
| 02 | [IoT certificate and security policy](docs/screenshots/02-IoT-Certificate-and-Security-Policy.png) |
| 03 | [MQTT message received](docs/screenshots/03-MQTT-Message-Received.png) |
| 04 | [DynamoDB ingested data](docs/screenshots/04-DynamoDB-Ingested-Sensor-Data.png) |
| 05 | [Python MQTT simulator](docs/screenshots/05-Python-MQTT-Simulation.png) |
| 06 | [Three-farm DynamoDB data](docs/screenshots/06-Multi-Farm-DynamoDB.png) |
| 07–09 | [Dashboard overview](docs/screenshots/07-Dashboard-Overview.png), [trends](docs/screenshots/08-Dashboard-Trends-and-Data.png), [monitoring logs](docs/screenshots/09-IoT-Monitoring-Logs.png) — local data previews |
| 10–11 | [Power BI full dashboard](docs/screenshots/10-PowerBI-Dashboard-Full.png), [cropped dashboard](docs/screenshots/11-PowerBI-Dashboard-Cropped.png) |
| 12 | [Live Grafana MQTT monitoring](docs/screenshots/12-Grafana-Live-MQTT-Monitoring.png) |
| 13 | [100-message DynamoDB verification](docs/screenshots/13-Scalability-Test-100-Messages.png) |
| 14 | [Grafana receiving load-test telemetry](docs/screenshots/14-Grafana-Scalability-Live-Monitoring.png) |

## Security, scalability and cost

- **In transit:** MQTT/TLS with X.509 mutual authentication; separate simulator and Grafana certificates and least-privilege IoT policies.
- **Access:** IoT Rule assumes an IAM role to write DynamoDB records. The policy files are illustrative; replace `ACCOUNT_ID` before applying and verify permissions in the deployed account.
- **At rest:** DynamoDB supports encryption at rest; confirm the table's current encryption settings in AWS Console when documenting production controls.
- **Scaling:** Managed AWS IoT Core, wildcard farm topic routing, and DynamoDB allow additional farm streams without provisioning a broker. This prototype verified 100 stored load-test messages, not a sustained high-volume benchmark.
- **Cost:** Pay-per-use AWS services; remove unused IoT certificates, rules, and DynamoDB table **only after final submission and evidence collection**. Review billing separately.

## Known limitations

This is a **simulation**, not a deployment of physical sensors or on-farm hardware. Grafana receives live MQTT messages but does not replay historical messages from DynamoDB. Power BI is based on exported datasets. The simulator has one device identity representing three farms. No separate Lambda preprocessing service or standalone Mosquitto gateway was deployed; AWS IoT Core acts as the managed MQTT broker.

## Documentation

- [Modular Assignment 5 report](docs/Network%20and%20IoT%20Solution-M5-Report.docx)
- [Architecture diagram](docs/AgroSense%20AWS%20IoT%20Architecture%20Diagram.png)

**University assignment:** AgroSense Ltd. — Network and IoT Solution, Modular Assignment 5.
