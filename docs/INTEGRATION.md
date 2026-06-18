# Backend Integration Guide

> API integration documentation for Kafka, ML, and LLM pipeline modules.

---

## Overview

This guide provides detailed specifications for integrating with the AI SOC Assistant backend API. All integration endpoints are **internal-only** and do **NOT require JWT authentication**.

**⚠️ Security Note:** These endpoints should only be accessible from trusted internal services within your infrastructure. Consider network-level access controls (firewall rules, VPCs, service mesh policies).

---

## Table of Contents

- [Kafka Integration](#kafka-integration)
- [ML Module Integration](#ml-module-integration)
- [LLM Module Integration](#llm-module-integration)
- [Error Handling](#error-handling)
- [Example Implementations](#example-implementations)

---

## Kafka Integration

### Overview

The Kafka consumer processes security logs from various sources and forwards them to the backend for storage and further analysis.

### Endpoint

```
POST /ingest/logs
```

**Base URL:** `http://backend-service:8000` (adjust based on your deployment)

### Request Schema

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `source` | string | ✅ Yes | Log source identifier | `"firewall-01"`, `"nginx-lb"` |
| `severity` | string | ✅ Yes | Log severity level | `"info"`, `"warning"`, `"high"`, `"critical"` |
| `message` | string | ✅ Yes | Human-readable log message | `"Blocked connection from 203.0.113.5"` |
| `timestamp` | string (ISO 8601) | ❌ No | Event timestamp (defaults to ingestion time) | `"2024-06-01T14:32:00Z"` |
| `raw` | string | ❌ No | Original raw log line | `"Jun 1 14:32:00 fw01 kernel: DROP..."` |

### Example Request

```bash
curl -X POST http://localhost:8000/ingest/logs \
  -H "Content-Type: application/json" \
  -d '{
    "source": "firewall-01",
    "severity": "high",
    "message": "Blocked inbound connection from 198.51.100.42:4444 to 10.0.0.5:22",
    "timestamp": "2024-06-01T14:32:00Z",
    "raw": "Jun  1 14:32:00 fw01 kernel: DROP IN=eth0 SRC=198.51.100.42 DST=10.0.0.5 DPT=22"
  }'
```

### Response

**Success (201 Created):**

```json
{
  "id": 1,
  "source": "firewall-01",
  "severity": "high",
  "message": "Blocked inbound connection from 198.51.100.42:4444 to 10.0.0.5:22",
  "timestamp": "2024-06-01T14:32:00Z",
  "raw": "Jun  1 14:32:00 fw01 kernel: DROP IN=eth0 SRC=198.51.100.42 DST=10.0.0.5 DPT=22",
  "ingested_at": "2024-06-01T14:32:05.123456Z"
}
```

**Error (422 Unprocessable Entity):**

```json
{
  "detail": [
    {
      "loc": ["body", "severity"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Python Implementation Example

```python
import requests
from kafka import KafkaConsumer
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_TOPIC = 'security-logs'
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
BACKEND_API_URL = 'http://localhost:8000/ingest/logs'

# Initialize Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='soc-backend-consumer'
)

logger.info(f"Kafka consumer started. Listening to topic: {KAFKA_TOPIC}")

# Process messages
for message in consumer:
    try:
        log_data = message.value
        
        # Prepare payload for backend
        payload = {
            "source": log_data.get("source", "unknown"),
            "severity": log_data.get("severity", "info"),
            "message": log_data.get("message", ""),
            "timestamp": log_data.get("timestamp"),  # Optional
            "raw": log_data.get("raw")  # Optional
        }
        
        # Forward to backend
        response = requests.post(BACKEND_API_URL, json=payload, timeout=5)
        response.raise_for_status()
        
        log_id = response.json()["id"]
        logger.info(f"✅ Log ingested successfully: ID={log_id}, source={payload['source']}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to ingest log: {e}")
        # Implement retry logic or dead-letter queue here
    except Exception as e:
        logger.error(f"❌ Unexpected error processing message: {e}")
```

### Severity Levels

Use consistent severity levels across your log sources:

| Level | Use Case |
|-------|----------|
| `info` | Normal operations (logins, configuration changes) |
| `warning` | Potential issues (high resource usage, failed retries) |
| `high` | Security events (blocked connections, failed authentications) |
| `critical` | Severe security incidents (successful breaches, system compromise) |

---

## ML Module Integration

### Overview

The ML anomaly detection module analyzes logs/network traffic and generates alerts when suspicious patterns are detected.

### Endpoint

```
POST /ingest/alerts
```

**Base URL:** `http://backend-service:8000`

### Request Schema

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `title` | string | ✅ Yes | Alert title (max 200 chars) | `"Anomalous Outbound Traffic Spike"` |
| `severity` | string | ✅ Yes | Alert severity | `"info"`, `"warning"`, `"high"`, `"critical"` |
| `source` | string | ✅ Yes | Detection source identifier | `"ml-anomaly-detector"`, `"spark-streaming"` |
| `description` | string | ❌ No | Detailed alert description | `"Outbound bytes exceeded 3σ threshold..."` |

### Example Request

```bash
curl -X POST http://localhost:8000/ingest/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Anomalous Outbound Traffic Spike",
    "severity": "critical",
    "source": "ml-anomaly-detector",
    "description": "Outbound bytes on eth0 exceeded 3σ threshold. Anomaly score: 0.987"
  }'
```

### Response

**Success (201 Created):**

```json
{
  "id": 15,
  "title": "Anomalous Outbound Traffic Spike",
  "severity": "critical",
  "source": "ml-anomaly-detector",
  "description": "Outbound bytes on eth0 exceeded 3σ threshold. Anomaly score: 0.987",
  "status": "open",
  "created_at": "2024-06-01T15:00:00.123456Z"
}
```

**Alert Statuses:**
- `open` (default): New alert, requires investigation
- `acknowledged`: Analyst is investigating
- `resolved`: Issue resolved

### Python Implementation Example

```python
import requests
import numpy as np
from sklearn.ensemble import IsolationForest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_API_URL = 'http://localhost:8000/ingest/alerts'
ANOMALY_THRESHOLD = 0.95

# ML model (simplified example)
model = IsolationForest(contamination=0.05, random_state=42)

def analyze_network_traffic(traffic_data):
    """
    Analyze network traffic and detect anomalies.
    
    Args:
        traffic_data: numpy array of network metrics (bytes, packets, etc.)
    
    Returns:
        tuple: (is_anomaly, anomaly_score)
    """
    # Fit model and predict
    predictions = model.fit_predict(traffic_data.reshape(-1, 1))
    scores = model.score_samples(traffic_data.reshape(-1, 1))
    
    # Normalize scores to [0, 1]
    anomaly_score = 1 - (scores[-1] - scores.min()) / (scores.max() - scores.min())
    is_anomaly = predictions[-1] == -1
    
    return is_anomaly, anomaly_score

def send_alert_to_backend(title, severity, description):
    """Send alert to backend API."""
    payload = {
        "title": title,
        "severity": severity,
        "source": "ml-anomaly-detector",
        "description": description
    }
    
    try:
        response = requests.post(BACKEND_API_URL, json=payload, timeout=5)
        response.raise_for_status()
        
        alert_id = response.json()["id"]
        logger.info(f"✅ Alert created: ID={alert_id}, severity={severity}")
        return alert_id
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to create alert: {e}")
        return None

# Example usage
outbound_bytes = np.array([1024, 2048, 1536, 1024, 15728640])  # Last value is anomalous

is_anomaly, score = analyze_network_traffic(outbound_bytes)

if is_anomaly and score > ANOMALY_THRESHOLD:
    send_alert_to_backend(
        title="Anomalous Outbound Traffic Spike",
        severity="critical",
        description=f"Outbound bytes exceeded 3σ threshold. Anomaly score: {score:.3f}"
    )
```

### Alert Title Guidelines

Use clear, actionable titles:

✅ **Good:**
- "SSH Brute Force Attack Detected"
- "Anomalous Outbound Traffic Spike"
- "Unauthorized Access Attempt from Known Malicious IP"

❌ **Bad:**
- "Alert 12345"
- "Anomaly"
- "Something happened"

---

## LLM Module Integration

### Overview

The LLM module generates AI-powered summaries for security incidents, providing analysts with actionable insights and recommended responses.

### Endpoint

```
POST /summaries
```

**Base URL:** `http://backend-service:8000`

### Request Schema

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `incident_id` | integer | ✅ Yes | Target incident ID | `1` |
| `summary` | string | ✅ Yes | AI-generated incident summary | `"Attacker conducted coordinated attack..."` |

### Example Request

```bash
curl -X POST http://localhost:8000/summaries \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": 1,
    "summary": "Attacker(s) conducted a coordinated SSH brute-force campaign from 3 distinct IP addresses. Attack originated from known botnet infrastructure. Recommend immediate firewall rule update to block source IPs and enforce key-based authentication."
  }'
```

### Response

**Success (200 OK):**

```json
{
  "id": 1,
  "title": "Coordinated Brute Force Campaign",
  "description": "Multiple SSH brute-force attempts from different IPs targeting production servers",
  "alert_ids": [1, 2, 3],
  "status": "open",
  "summary": "Attacker(s) conducted a coordinated SSH brute-force campaign from 3 distinct IP addresses. Attack originated from known botnet infrastructure. Recommend immediate firewall rule update to block source IPs and enforce key-based authentication.",
  "created_at": "2024-06-01T14:40:00.123456Z"
}
```

**Error (404 Not Found):**

```json
{
  "detail": "Incident with ID 999 not found"
}
```

### Python Implementation Example (OpenAI GPT-4)

```python
import requests
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BACKEND_API_URL = 'http://localhost:8000'
OPENAI_API_KEY = 'sk-...'  # Use environment variable in production

client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_incident_details(incident_id, analyst_token):
    """Fetch incident details from backend."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    response = requests.get(
        f"{BACKEND_API_URL}/incidents/{incident_id}",
        headers=headers,
        timeout=5
    )
    response.raise_for_status()
    return response.json()

def generate_incident_summary(incident_data):
    """Generate AI summary using OpenAI GPT-4."""
    prompt = f"""
You are a cybersecurity analyst assistant. Analyze the following security incident and provide:

1. **Executive Summary** (2-3 sentences): High-level overview of the incident
2. **Attack Analysis**: Key findings, attacker behavior, affected systems
3. **Recommended Actions**: Specific, actionable steps to mitigate the threat

Incident Details:
- Title: {incident_data['title']}
- Description: {incident_data.get('description', 'N/A')}
- Related Alerts: {len(incident_data.get('alert_ids', []))}
- Status: {incident_data['status']}

Be concise but thorough. Focus on actionable intelligence.
"""
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior cybersecurity analyst with expertise in threat intelligence and incident response."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=500
        )
        
        summary = completion.choices[0].message.content
        logger.info(f"✅ Generated summary ({len(summary)} chars)")
        return summary
    
    except Exception as e:
        logger.error(f"❌ Failed to generate summary: {e}")
        return None

def attach_summary_to_incident(incident_id, summary):
    """Attach generated summary to incident via backend API."""
    payload = {
        "incident_id": incident_id,
        "summary": summary
    }
    
    try:
        response = requests.post(
            f"{BACKEND_API_URL}/summaries",
            json=payload,
            timeout=5
        )
        response.raise_for_status()
        
        logger.info(f"✅ Summary attached to incident {incident_id}")
        return response.json()
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to attach summary: {e}")
        return None

# Example workflow
def process_incident(incident_id, analyst_token):
    """Complete workflow: fetch incident → generate summary → attach to backend."""
    logger.info(f"Processing incident {incident_id}...")
    
    # Step 1: Fetch incident details
    incident_data = fetch_incident_details(incident_id, analyst_token)
    
    # Step 2: Generate AI summary
    summary = generate_incident_summary(incident_data)
    
    if summary:
        # Step 3: Attach summary to incident
        updated_incident = attach_summary_to_incident(incident_id, summary)
        return updated_incident
    else:
        logger.error("Failed to generate summary")
        return None

# Run
if __name__ == "__main__":
    ANALYST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Replace with real token
    process_incident(incident_id=1, analyst_token=ANALYST_TOKEN)
```

### Summary Format Guidelines

Structure your LLM summaries to include:

1. **Executive Summary**: 2-3 sentence overview
2. **Attack Details**: Specific indicators (IPs, usernames, timestamps)
3. **Impact Assessment**: What systems/data were affected
4. **Recommended Actions**: Prioritized list of mitigation steps

**Example:**

```
Executive Summary:
Attacker(s) conducted a coordinated SSH brute-force campaign targeting production servers from 3 distinct IP addresses over a 2-hour period.

Attack Details:
- Source IPs: 198.51.100.42, 203.0.113.15, 192.0.2.88
- Target: prod-web-01.example.com (10.0.0.5)
- Time Window: 2024-06-01 14:30:00 - 16:30:00 UTC
- Failed Attempts: 1,247 total

Impact Assessment:
No successful authentication detected. All attempts blocked by fail2ban rules. No data exfiltration observed.

Recommended Actions:
1. URGENT: Add source IPs to firewall blocklist immediately
2. HIGH: Enforce key-based SSH authentication, disable password auth
3. MEDIUM: Review fail2ban logs for other potential targets
4. LOW: Submit IPs to threat intelligence feeds
```

---

## Error Handling

### HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| `200 OK` | Request successful (GET, PATCH, POST /summaries) | Continue normal operation |
| `201 Created` | Resource created (POST /ingest/logs, /ingest/alerts) | Continue normal operation |
| `404 Not Found` | Resource doesn't exist (e.g., invalid incident_id) | Verify ID exists before retrying |
| `422 Unprocessable Entity` | Validation error (missing fields) | Fix payload and retry |
| `500 Internal Server Error` | Backend error | Implement retry with exponential backoff |
| `503 Service Unavailable` | Backend overloaded/down | Retry after delay, use circuit breaker pattern |

### Retry Strategy

Implement exponential backoff for transient failures:

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session_with_retries():
    """Create requests session with automatic retries."""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,  # Max retries
        backoff_factor=1,  # Wait 1s, 2s, 4s between retries
        status_forcelist=[429, 500, 502, 503, 504],  # Retry on these statuses
        allowed_methods=["POST"]  # Retry POST requests
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Usage
session = create_session_with_retries()
response = session.post(
    "http://localhost:8000/ingest/logs",
    json={"source": "test", "severity": "info", "message": "test"},
    timeout=5
)
```

### Circuit Breaker Pattern

Prevent cascading failures by stopping requests after repeated failures:

```python
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

# Usage
breaker = CircuitBreaker(failure_threshold=5, timeout=60)

def send_log(data):
    response = requests.post("http://localhost:8000/ingest/logs", json=data)
    response.raise_for_status()
    return response.json()

try:
    result = breaker.call(send_log, {"source": "test", "severity": "info", "message": "test"})
except Exception as e:
    print(f"Circuit breaker prevented request: {e}")
```

---

## Example Implementations

### 1. Kafka Consumer (Complete)

See [Kafka Integration](#kafka-integration) for full implementation.

### 2. Spark Streaming ML Pipeline

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, window, count
import requests

spark = SparkSession.builder.appName("SOC-ML-Detector").getOrCreate()

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "network-traffic") \
    .load()

# Detect anomalies (simplified: count connections per IP per minute)
anomalies = df \
    .selectExpr("CAST(value AS STRING) as json") \
    .selectExpr("get_json_object(json, '$.src_ip') as src_ip") \
    .groupBy(window(col("timestamp"), "1 minute"), "src_ip") \
    .count() \
    .filter(col("count") > 100)  # Threshold: >100 connections/min

def send_alert(batch_df, batch_id):
    """Send alerts for each anomalous IP."""
    for row in batch_df.collect():
        requests.post(
            "http://localhost:8000/ingest/alerts",
            json={
                "title": f"High Connection Rate from {row.src_ip}",
                "severity": "high",
                "source": "spark-streaming-ml",
                "description": f"Detected {row['count']} connections in 1 minute from {row.src_ip}"
            }
        )

# Stream processing
query = anomalies.writeStream \
    .foreachBatch(send_alert) \
    .start()

query.awaitTermination()
```

### 3. LangChain Integration (Alternative to OpenAI)

```python
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import requests

# Initialize LangChain
llm = ChatOpenAI(model="gpt-4", temperature=0.3)

def generate_summary_langchain(incident_data):
    """Generate incident summary using LangChain."""
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="You are a senior cybersecurity analyst."),
        HumanMessage(content=f"""
Analyze this incident and provide a concise summary with recommended actions:

Title: {incident_data['title']}
Description: {incident_data.get('description', 'N/A')}
Related Alerts: {len(incident_data.get('alert_ids', []))}
        """)
    ])
    
    response = llm.invoke(prompt.format_messages())
    return response.content

# Use in workflow
incident_id = 1
incident = requests.get(f"http://localhost:8000/incidents/{incident_id}").json()
summary = generate_summary_langchain(incident)
requests.post("http://localhost:8000/summaries", json={"incident_id": incident_id, "summary": summary})
```

---

## Testing Integration

Test endpoints using curl or Postman:

```bash
# Test log ingestion
curl -X POST http://localhost:8000/ingest/logs \
  -H "Content-Type: application/json" \
  -d '{"source":"test","severity":"info","message":"Test log"}'

# Test alert ingestion
curl -X POST http://localhost:8000/ingest/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Alert","severity":"high","source":"test"}'

# Test summary attachment (requires existing incident)
curl -X POST http://localhost:8000/summaries \
  -H "Content-Type: application/json" \
  -d '{"incident_id":1,"summary":"Test summary"}'
```

---

## Support

For integration issues, contact the backend team:
- **GitHub**: [@iamShreerang](https://github.com/iamShreerang)
- **Project**: [AI-SOC-Assistant](https://github.com/iamShreerang/AI-SOC-Assistant)

---

**Last Updated:** June 2024  
**API Version:** 1.0.0
