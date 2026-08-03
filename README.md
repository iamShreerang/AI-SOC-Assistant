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

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| Docker + Docker Compose | 24+ |
| Java (for Spark local mode) | 11 or 17 |

---

## Environment Setup

### Backend `.env`

Copy `backend/.env.example.new` → `backend/.env` and fill in:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/soc_db
SECRET_KEY=your-secret-key
GROQ_API_KEY=gsk_...            # Get from console.groq.com
ELASTICSEARCH_ENABLED=false     # Set true only if Elasticsearch is running
KAFKA_BROKER=localhost:9092
AUTO_INCIDENT_SUMMARY=true      # Auto-generate Groq summary on incident creation
```

### Streaming `.env`

Copy `streaming/.env.example` → `streaming/.env`:

```env
KAFKA_BROKER=localhost:9092
KAFKA_INPUT_TOPIC=unsw-logs
BACKEND_API_URL=http://localhost:8000
MODEL_DIR=../ml/saved_models
```

---

## Running the Project

### Step 1 — Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API: http://localhost:8000  
Swagger docs: http://localhost:8000/docs

---

### Step 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

---

### Step 3 — Kafka + Docker (for full streaming pipeline)

```bash
cd streaming

# Start Zookeeper, Kafka, Kafka UI, and optionally Postgres + backend
docker compose up -d zookeeper kafka kafka-init kafka-ui

# Verify Kafka is ready (Kafka UI at http://localhost:8080)
```

> **Note:** The `unsw-logs` and `predictions` topics are created automatically by the `kafka-init` container.

---

### Step 4 — Spark Streaming Consumer

> **Requires:** Java 11 or 17, PySpark (`pip install pyspark==3.5.1`)

```powershell
# Windows PowerShell launcher (auto-configures project JDK 17 & Hadoop winutils):
.\scripts\start_spark.ps1

# Or run directly via Python:
python streaming/spark/streaming_job.py
```

The job will:
- Connect to Kafka `unsw-logs` topic
- Run CNN-LSTM inference on each batch
- Apply 5 threat detection rules
- POST logs + alerts to the FastAPI backend
- POST a heartbeat to `/ingest/heartbeat` every 30 seconds

---

### Step 5 — Kafka Producer

```bash
# From repo root — publishes sample JSONL to Kafka once
python streaming/kafka/producer.py

# Loop continuously (for sustained demo traffic)
python streaming/kafka/producer.py --continuous

# Custom broker or topic
python streaming/kafka/producer.py --broker localhost:9092 --topic unsw-logs --delay 0.2
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

This reads `streaming/sample_logs/logs_real_unsw_sample.jsonl` directly through the same CNN-LSTM + threat rules + backend ingest pipeline as Kafka mode.

To generate more sample data:

```bash
python streaming/sample_logs/generate.py
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
