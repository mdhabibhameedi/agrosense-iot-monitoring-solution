# DynamoDB table schema

- **Table:** `AgroSense-SensorReadings`
- **Partition key:** `device_id` (String)
- **Sort key:** `timestamp` (Number, added by AWS IoT Rule)
- **Ingestion:** AWS IoT Core Rule `AgroSense_Sensor_Data_Rule` → DynamoDBv2 action using IAM role `AgroSense-IoT-DynamoDB-Role`.

The IoT Rule's `timestamp()` is an ingestion timestamp; the JSON monitoring log timestamp is a separate simulator-side event timestamp.
