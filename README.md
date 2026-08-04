# AI SOC Assistant

> An AI-powered Security Operations Center platform for real-time log ingestion, anomaly detection, and intelligent incident response.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.6-black)](https://kafka.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5-orange)](https://spark.apache.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

---

## Project Overview

The AI SOC Assistant collects, processes, analyzes, and monitors security logs in real time using a CNN-LSTM anomaly detection model and Groq LLMs for intelligent incident summarization.

**Full pipeline:**

```
UNSW-NB15 / JSONL
    ↓
Kafka Producer (streaming/kafka/producer.py)
    ↓
Kafka Topic: unsw-logs
    ↓
Spark Structured Streaming (streaming/spark/streaming_job.py)
    ↓ feature mapping → CNN-LSTM inference → threat rules
    ↓
FastAPI Backend (backend/)
    ↓
Supabase / PostgreSQL
    ↓
React Dashboard (frontend/)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Log Ingestion | Apache Kafka |
| Stream Processing | Apache Spark Structured Streaming |
| Anomaly Detection | CNN-LSTM (PyTorch) + UNSW-NB15 dataset |
| Backend API | FastAPI (Python 3.11) |
| Structured Storage | PostgreSQL (Supabase) |
| Log Indexing | Elasticsearch (optional) |
| Frontend Dashboard | React + Vite + TypeScript |
| LLM Integration | Groq (`llama-3.1-8b-instant`) |

---

## Team Members

| Name | GitHub | Role |
|---|---|---|
| Shreerang Kolhe | [@iamShreerang](https://github.com/iamShreerang) | Backend + Integration + Frontend + Database |
| Ayush Dandge | [@AyushDandge](https://github.com/AyushDandge) | Big Data Pipeline |
| Aryan Dandge | [@aryansdandge-7](https://github.com/aryansdandge-7) | ML |
| Sumiran Bagul | [@sumiran-7](https://github.com/sumiran-7) | ML |

---

## Repository Structure

```
AI-SOC-Assistant/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py       # FastAPI entry point
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── utils/        # Config, security, ES client
│   ├── alembic/          # Database migrations
│   └── tests/            # pytest test suite
├── frontend/             # React + Vite dashboard
│   └── src/
│       ├── pages/        # MLAnalytics, Alerts, Incidents, Dashboard, …
│       └── services/     # api.ts (real GET /stats/ml, no Math.random)
├── streaming/            # Kafka + Spark pipeline
│   ├── kafka/
│   │   └── producer.py   # Reads JSONL → publishes to unsw-logs
│   ├── spark/
│   │   ├── streaming_job.py   # Spark Structured Streaming consumer
│   │   ├── feature_mapper.py  # Raw field normalization for CNN-LSTM
│   │   ├── threat_rules.py    # 5 rule-based detection rules
│   │   └── metrics.py         # In-process streaming metrics
│   ├── backend_client.py # HTTP client for /ingest/* endpoints
│   ├── config.py         # All env-var-based configuration
│   ├── docker-compose.yml
│   └── tests/            # streaming unit + pipeline tests
├── ml/
│   ├── model/            # CNN-LSTM architecture
│   ├── inference/        # Predictor.load() + predict_batch()
│   ├── preprocessing/    # PreprocessingPipeline (MinMaxScaler)
│   └── saved_models/     # cnn_lstm.pt, pipeline.pkl, threshold.pkl
├── docs/                 # Architecture diagrams, SRS
└── deployment/           # Docker, CI/CD configs
```

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| **Git** | 2.x+ | Repository cloning |
| **Python** | 3.11+ | Backend & ML model execution |
| **Node.js** | 20+ | React frontend dashboard |
| **Docker Desktop** | 24+ | Kafka & ZooKeeper containers |
| **Java (JDK)** | 11 or 17 | Required for PySpark stream processing |

---

## Complete Setup Guide (Fresh PC Installation)

### Step 0 — Clone the Repository

```bash
git clone https://github.com/iamShreerang/AI-SOC-Assistant.git
cd AI-SOC-Assistant
```

---

### Step 1 — Configure Environment Files

#### 1. Backend Environment Configuration
Copy `backend/.env.example` to `backend/.env`:

```bash
cp backend/.env.example backend/.env   # Linux/macOS
# or copy manually on Windows
```

Configure your PostgreSQL / Supabase connection in `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/soc_db
SECRET_KEY=your-secret-key-min-32-chars
GROQ_API_KEY=gsk_...            # (Optional) Get free key from console.groq.com
EVALUATION_MODE=false
EVALUATION_PASSWORD_HASH_CHECK=false
```

#### 2. Streaming Environment Configuration
Copy `streaming/.env.example` to `streaming/.env`:

```env
KAFKA_BROKER=localhost:9092
KAFKA_INPUT_TOPIC=unsw-logs
BACKEND_API_URL=http://localhost:8000
```

---

### Step 2 — Backend Setup & Database Migrations

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Apply Database Migrations (Creates all DB tables)
alembic upgrade head

# 4. Launch FastAPI Backend Server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

> **Default Accounts Available**:
> - **Admin**: `username: admin` | `password: admin123`
> - **Analyst**: `username: analyst` | `password: analyst123`

---

### Step 3 — Frontend Dashboard Setup

```bash
cd frontend
npm install
npm run dev
```

Dashboard UI: http://localhost:5173

---

### Step 4 — Infrastructure Setup (Kafka + Docker)

```bash
cd streaming

# Start Zookeeper, Kafka, Kafka UI
docker compose up -d zookeeper kafka kafka-init kafka-ui
```

> **Note:** The `unsw-logs` and `predictions` Kafka topics are created automatically by the `kafka-init` container.

---

### Step 5 — Spark Streaming Pipeline

> **Requires:** Java 11 or 17 (`JAVA_HOME` set)

```powershell
# Run PySpark streaming job (consumes latest Kafka logs & performs ML inference):
backend\venv\Scripts\python.exe streaming/spark/streaming_job.py
```

---

### Step 6 — Log Generator & Kafka Producer

```bash
# Stream UNSW-NB15 mock logs to Kafka at 5 records/sec:
backend\venv\Scripts\python.exe streaming/sample_logs/generate.py --kafka --rate 5

# Custom broker, topic, or delay:
backend\venv\Scripts\python.exe streaming/sample_logs/generate.py --kafka --broker localhost:9092 --topic unsw-logs --delay 0.2
```

---

## Streaming State Reset & Clean Mode

To wipe old micro-batch checkpoint files and reset the streaming state cleanly:

```powershell
backend\venv\Scripts\python.exe streaming/clean_stream.py
```

---

## Local Test Mode (No Kafka / Docker Required)

Run the complete ML pipeline using local JSONL files — no Kafka, no Docker, no Java cluster needed:

```bash
# Pure Python local pipeline simulator:
python streaming/run_local_pipeline.py

# Or Spark local test mode:
python streaming/spark/streaming_job.py --local-test
```

This reads sample logs directly through the same CNN-LSTM + threat rules + backend ingest pipeline as Kafka mode.

To generate more sample data files:

```bash
python streaming/sample_logs/generate.py --batch 200
```

---

## Running Tests

### Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests cover: auth, logs, alerts, incidents, health check, ML analytics endpoint, heartbeat, metrics ingest.

> Requires a live PostgreSQL database configured in `backend/.env`.

### Streaming Unit Tests (No Kafka/Spark required)

```bash
# Threat rules — pure Python, no external dependencies
python streaming/tests/test_threat_rules.py

# Backend client payload + error handling — mocked HTTP
python -m pytest streaming/tests/test_backend_client.py -v

# Full local pipeline: FeatureMapper + Predictor + ThreatRules
# (requires ml/saved_models/ artifacts)
python streaming/tests/test_local_pipeline.py

# All streaming tests via pytest
python -m pytest streaming/tests/ -v
```

---

## Key API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Service health (DB, Kafka, Spark, ML model, LLM, ES) |
| POST | `/auth/login` | No | Get JWT bearer token |
| GET | `/logs` | Bearer | List security logs |
| GET | `/alerts` | Bearer | List alerts |
| GET | `/incidents` | Bearer | List incidents |
| POST | `/incidents` | Bearer | Create incident (auto-generates Groq summary) |
| GET | `/stats/summary` | Bearer | Dashboard summary stats |
| GET | `/stats/ml` | Bearer | ML analytics (real DB data) |
| POST | `/ingest/logs` | No | Internal — Spark → backend log ingest |
| POST | `/ingest/alerts` | No | Internal — Spark → backend alert ingest |
| POST | `/ingest/heartbeat` | No | Internal — Spark liveness signal |
| POST | `/ingest/metrics` | No | Internal — pipeline metrics |
| POST | `/summaries` | No | Internal — attach LLM summary to incident |

---

## Health Check Response

```json
{
  "status": "ok",
  "version": "0.1.0",
  "components": {
    "database": true,
    "kafka": true,
    "spark": true,
    "ml_model": true,
    "llm": true,
    "elasticsearch": { "enabled": true, "healthy": true }
  }
}
```

- **database** — live `SELECT 1` probe
- **kafka** — broker metadata check with 3s timeout
- **spark** — heartbeat freshness (healthy if last heartbeat < 120s ago)
- **ml_model** — saved artifact presence check
- **llm** — Groq API key configured (no tokens consumed)
- **elasticsearch** — disabled/enabled + ping if enabled

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, production-ready code only |
| `backend` | FastAPI development |
| `big-data` | Kafka + Spark pipeline |
| `ai-ml` | Machine learning models |
| `frontend` | React dashboard |

Feature branches: `feature/<module>/<short-task-name>`

---

## License

This project is licensed under the GNU Affero General Public License v3.0 — see [LICENSE](LICENSE) for details.
