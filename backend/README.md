# Backend API Documentation

> FastAPI-based REST API for the AI SOC Assistant platform with JWT authentication, CRUD operations for logs/alerts/incidents, and integration endpoints for Kafka/ML/LLM pipelines.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-55_passing-success)](tests/)

---

## Table of Contents

- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [JWT Authentication Flow](#jwt-authentication-flow)
- [Integration Payloads](#integration-payloads)
- [Testing](#testing)
- [Project Structure](#project-structure)

---

## Quick Start

### Prerequisites
- Python 3.11+
- pip or uv package manager

### Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server runs at: `http://localhost:8000`

- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## API Endpoints

### Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | ❌ No | Service health check |

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | ❌ No | Register new user |
| POST | `/auth/login` | ❌ No | Login and get JWT token |
| GET | `/auth/users/me` | ✅ Yes | Get current user info |

#### Register User

**Request:**
```json
POST /auth/register
Content-Type: application/json

{
  "username": "analyst_john",
  "password": "SecurePass123!",
  "role": "analyst"  // Optional: "analyst" (default) or "admin"
}
```

**Response (201 Created):**
```json
{
  "username": "analyst_john",
  "role": "analyst",
  "is_active": true
}
```

#### Login

**Request:**
```json
POST /auth/login
Content-Type: application/json

{
  "username": "analyst",
  "password": "analyst123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Pre-seeded Test Users:**
- `analyst` / `analyst123` (role: analyst)
- `admin` / `admin123` (role: admin)

#### Get Current User

**Request:**
```http
GET /auth/users/me
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
{
  "username": "analyst",
  "role": "analyst",
  "is_active": true
}
```

---

### Logs

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/logs/` | ✅ Yes | Create log entry |
| GET | `/logs/` | ✅ Yes | List all logs (with optional limit) |
| GET | `/logs/{log_id}` | ✅ Yes | Get log by ID |

#### Create Log

**Request:**
```json
POST /logs/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "source": "firewall-01",
  "severity": "high",
  "message": "Blocked inbound connection from 198.51.100.42:4444 to 10.0.0.5:22",
  "timestamp": "2024-06-01T14:32:00Z",  // Optional, defaults to now
  "raw": "Jun  1 14:32:00 fw01 kernel: DROP IN=eth0 SRC=198.51.100.42 DST=10.0.0.5 DPT=22"  // Optional
}
```

**Response (201 Created):**
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

#### List Logs

**Request:**
```http
GET /logs/?limit=50
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "source": "firewall-01",
    "severity": "high",
    "message": "Blocked inbound connection...",
    "timestamp": "2024-06-01T14:32:00Z",
    "raw": "...",
    "ingested_at": "2024-06-01T14:32:05.123456Z"
  }
]
```

---

### Alerts

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/alerts/` | ✅ Yes | Create alert |
| GET | `/alerts/` | ✅ Yes | List all alerts (with optional limit) |
| GET | `/alerts/{alert_id}` | ✅ Yes | Get alert by ID |
| PATCH | `/alerts/{alert_id}` | ✅ Yes | Update alert status |

#### Create Alert

**Request:**
```json
POST /alerts/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "title": "SSH Brute Force Attack Detected",
  "severity": "high",
  "source": "auth-service",
  "description": "15 failed SSH login attempts from 198.51.100.42 within 60 seconds"  // Optional
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "SSH Brute Force Attack Detected",
  "severity": "high",
  "source": "auth-service",
  "description": "15 failed SSH login attempts from 198.51.100.42 within 60 seconds",
  "status": "open",
  "created_at": "2024-06-01T14:35:00.123456Z"
}
```

#### Update Alert Status

**Request:**
```json
PATCH /alerts/1
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "status": "acknowledged"  // Options: "open", "acknowledged", "resolved"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "SSH Brute Force Attack Detected",
  "severity": "high",
  "source": "auth-service",
  "description": "15 failed SSH login attempts...",
  "status": "acknowledged",
  "created_at": "2024-06-01T14:35:00.123456Z"
}
```

---

### Incidents

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/incidents/` | ✅ Yes | Create incident |
| GET | `/incidents/` | ✅ Yes | List all incidents (with optional limit) |
| GET | `/incidents/{incident_id}` | ✅ Yes | Get incident by ID |

#### Create Incident

**Request:**
```json
POST /incidents/
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

{
  "title": "Coordinated Brute Force Campaign",
  "description": "Multiple SSH brute-force attempts from different IPs targeting production servers",  // Optional
  "alert_ids": [1, 2, 3]  // Optional: link related alerts
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "title": "Coordinated Brute Force Campaign",
  "description": "Multiple SSH brute-force attempts from different IPs targeting production servers",
  "alert_ids": [1, 2, 3],
  "status": "open",
  "summary": null,
  "created_at": "2024-06-01T14:40:00.123456Z"
}
```

---

## JWT Authentication Flow

### Token Lifecycle

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ 1. POST /auth/login
       │    {username, password}
       ▼
┌─────────────┐
│   Backend   │
└──────┬──────┘
       │
       │ 2. Validate credentials
       │    (bcrypt password hash)
       │
       │ 3. Generate JWT token
       │    - Expiry: 15 minutes
       │    - Algorithm: HS256
       │    - Payload: {sub: username}
       │
       ▼
┌─────────────┐
│   Client    │ ← Returns JWT token
└──────┬──────┘
       │
       │ 4. Store token in memory/localStorage
       │
       │ 5. Include in all protected requests:
       │    Authorization: Bearer <token>
       ▼
┌─────────────┐
│   Backend   │
└──────┬──────┘
       │
       │ 6. Verify token signature
       │ 7. Check expiration
       │ 8. Extract username from payload
       │ 9. Return user data
       ▼
```

### Token Details

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiry**: 15 minutes from issue time
- **Secret**: Configured via `JWT_SECRET_KEY` environment variable
- **Payload Structure**:
  ```json
  {
    "sub": "analyst",           // Subject (username)
    "exp": 1717258920           // Expiration timestamp (Unix)
  }
  ```

### Using JWT in Requests

Include the token in the `Authorization` header with `Bearer` prefix:

```http
GET /logs/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbmFseXN0IiwiZXhwIjoxNzE3MjU4OTIwfQ.signature
```

### Error Responses

**401 Unauthorized - Invalid Token:**
```json
{
  "detail": "Could not validate credentials"
}
```

**401 Unauthorized - Expired Token:**
```json
{
  "detail": "Token has expired"
}
```

**401 Unauthorized - Missing Token:**
```json
{
  "detail": "Not authenticated"
}
```

---

## Integration Payloads

The following endpoints are designed for **internal pipeline integration** and do **NOT require authentication**. They should only be accessible from trusted internal services (Kafka consumers, ML modules, LLM services).

### Kafka → Backend: Ingest Log

**Endpoint:** `POST /ingest/logs`  
**Auth:** ❌ No (internal only)

This endpoint receives processed logs from the Kafka consumer and stores them in the backend.

**Python Example (Kafka Consumer):**

```python
import requests
from kafka import KafkaConsumer
import json

# Kafka consumer setup
consumer = KafkaConsumer(
    'security-logs',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

# Backend API endpoint
BACKEND_URL = "http://localhost:8000/ingest/logs"

for message in consumer:
    log_data = message.value
    
    # Forward log to backend
    response = requests.post(BACKEND_URL, json={
        "source": log_data["source"],
        "severity": log_data["severity"],
        "message": log_data["message"],
        "timestamp": log_data.get("timestamp"),  # Optional
        "raw": log_data.get("raw")  # Optional
    })
    
    if response.status_code == 201:
        print(f"✅ Log ingested: ID {response.json()['id']}")
    else:
        print(f"❌ Failed to ingest log: {response.status_code}")
```

**Request Payload:**

```json
POST /ingest/logs
Content-Type: application/json

{
  "source": "kafka-consumer",
  "severity": "info",
  "message": "User login from 10.0.0.15",
  "timestamp": "2024-06-01T14:50:00Z",  // Optional
  "raw": "2024-06-01 14:50:00 auth: user=admin ip=10.0.0.15 action=login"  // Optional
}
```

**Response (201 Created):**

```json
{
  "id": 42,
  "source": "kafka-consumer",
  "severity": "info",
  "message": "User login from 10.0.0.15",
  "timestamp": "2024-06-01T14:50:00Z",
  "raw": "2024-06-01 14:50:00 auth: user=admin ip=10.0.0.15 action=login",
  "ingested_at": "2024-06-01T14:50:05.123456Z"
}
```

---

### ML → Backend: Ingest Alert

**Endpoint:** `POST /ingest/alerts`  
**Auth:** ❌ No (internal only)

This endpoint receives anomaly alerts from the ML module after detecting suspicious patterns.

**Python Example (ML Anomaly Detector):**

```python
import requests
import numpy as np

# After ML model detects anomaly...
anomaly_score = 0.987  # High anomaly score
source_ip = "198.51.100.42"

if anomaly_score > 0.95:  # Threshold for critical alerts
    alert_payload = {
        "title": "Anomalous Outbound Traffic Spike",
        "severity": "critical",
        "source": "ml-anomaly-detector",
        "description": f"Outbound bytes on eth0 exceeded 3σ threshold. Anomaly score: {anomaly_score}"
    }
    
    # Send alert to backend
    response = requests.post(
        "http://localhost:8000/ingest/alerts",
        json=alert_payload
    )
    
    if response.status_code == 201:
        alert_id = response.json()["id"]
        print(f"✅ Alert created: ID {alert_id}")
    else:
        print(f"❌ Failed to create alert: {response.status_code}")
```

**Request Payload:**

```json
POST /ingest/alerts
Content-Type: application/json

{
  "title": "Anomalous Outbound Traffic Spike",
  "severity": "critical",
  "source": "ml-anomaly-detector",
  "description": "Outbound bytes on eth0 exceeded 3σ threshold. Anomaly score: 0.987"  // Optional
}
```

**Response (201 Created):**

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

---

### LLM → Backend: Attach Incident Summary

**Endpoint:** `POST /summaries`  
**Auth:** ❌ No (internal only)

This endpoint receives AI-generated summaries from the LLM module and attaches them to existing incidents.

**Python Example (LLM Summarization Service):**

```python
import requests
from openai import OpenAI

# Initialize OpenAI client (or any LLM provider)
client = OpenAI(api_key="sk-...")

# Fetch incident details from backend
incident_id = 1
incident_response = requests.get(
    f"http://localhost:8000/incidents/{incident_id}",
    headers={"Authorization": "Bearer <analyst_token>"}
)
incident_data = incident_response.json()

# Generate summary using LLM
prompt = f"""
Analyze this security incident and provide a concise executive summary:
- Title: {incident_data['title']}
- Description: {incident_data['description']}
- Related Alerts: {len(incident_data.get('alert_ids', []))}

Provide:
1. Attack summary (2-3 sentences)
2. Recommended actions
"""

completion = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}]
)

summary = completion.choices[0].message.content

# Attach summary to incident
response = requests.post(
    "http://localhost:8000/summaries",
    json={
        "incident_id": incident_id,
        "summary": summary
    }
)

if response.status_code == 200:
    print(f"✅ Summary attached to incident {incident_id}")
else:
    print(f"❌ Failed to attach summary: {response.status_code}")
```

**Request Payload:**

```json
POST /summaries
Content-Type: application/json

{
  "incident_id": 1,
  "summary": "Attacker(s) conducted a coordinated SSH brute-force campaign from 3 distinct IP addresses. Attack originated from known botnet infrastructure. Recommend immediate firewall rule update to block source IPs and enforce key-based authentication."
}
```

**Response (200 OK):**

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

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Test Suite Coverage

- **55 passing tests** across all modules
- **Test files:**
  - `test_auth.py` (13 tests): Registration, login, /users/me
  - `test_logs.py` (11 tests): CRUD operations + ingest endpoint
  - `test_alerts.py` (15 tests): CRUD operations + status transitions
  - `test_incidents.py` (14 tests): CRUD operations + LLM summary
  - `test_health.py` (1 test): Health check endpoint

### Postman Collection

A comprehensive Postman collection is available at `docs/postman/AI_SOC_Assistant_Postman_Collection.json`.

**Import Instructions:**
1. Open Postman
2. File → Import
3. Select `docs/postman/AI_SOC_Assistant_Postman_Collection.json`
4. Run the "🚀 Complete User Flow" folder in sequence

**Features:**
- ✅ Auto-token capture after login
- ✅ Auto-ID capture for logs/alerts/incidents
- ✅ Test scripts on every request
- ✅ Negative test cases (401, 404, 422)
- ✅ Integration endpoint testing

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app initialization
│   ├── routes/                  # API route handlers
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── logs.py              # Log management endpoints
│   │   ├── alerts.py            # Alert management endpoints
│   │   ├── incidents.py         # Incident management endpoints
│   │   └── health.py            # Health check endpoint
│   ├── schemas/                 # Pydantic models
│   │   ├── auth.py              # User, Token schemas
│   │   ├── log.py               # Log schemas
│   │   ├── alert.py             # Alert schemas
│   │   └── incident.py          # Incident schemas
│   ├── services/                # Business logic
│   │   ├── auth_service.py      # User registration, authentication
│   │   ├── log_service.py       # Log CRUD operations
│   │   ├── alert_service.py     # Alert CRUD operations
│   │   └── incident_service.py  # Incident CRUD operations
│   └── utils/                   # Utilities
│       ├── config.py            # Configuration (Pydantic Settings)
│       └── security.py          # JWT, password hashing
├── tests/                       # Test suite (55 tests)
│   ├── conftest.py              # Pytest fixtures
│   ├── test_auth.py
│   ├── test_logs.py
│   ├── test_alerts.py
│   ├── test_incidents.py
│   └── test_health.py
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker container config
└── pytest.ini                   # Pytest configuration
```

---

## Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Database (future PostgreSQL integration)
DATABASE_URL=postgresql://user:pass@localhost:5432/soc_db

# Kafka (future integration)
KAFKA_BROKER=localhost:9092

# Elasticsearch (future integration)
ELASTICSEARCH_URL=http://localhost:9200
```

**⚠️ Security Note:** Never commit `.env` files to Git. The `.gitignore` is configured to exclude them.

---

## Docker Deployment

```bash
# Build Docker image
docker build -t ai-soc-backend .

# Run container
docker run -d -p 8000:8000 --name soc-backend ai-soc-backend

# View logs
docker logs -f soc-backend

# Stop container
docker stop soc-backend
```

---

## Next Steps

1. ✅ JWT authentication implemented
2. ✅ CRUD operations for logs/alerts/incidents
3. ✅ Integration endpoints for Kafka/ML/LLM
4. ✅ 55 passing tests
5. ✅ Comprehensive API documentation
6. 🔄 Database integration (PostgreSQL) - planned
7. 🔄 Elasticsearch indexing - planned
8. 🔄 Frontend integration - in progress

---

## Team

| Name | GitHub | Responsibility |
|------|--------|----------------|
| Shreerang Kolhe | [@iamShreerang](https://github.com/iamShreerang) | Backend + Integration |

---

## License

This project is licensed under the GNU Affero General Public License v3.0 — see [LICENSE](../LICENSE) for details.
