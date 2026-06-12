# AI SOC Assistant

> An AI-powered Security Operations Center platform for real-time log ingestion, anomaly detection, and intelligent incident response.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)
[![Apache Kafka](https://img.shields.io/badge/Apache_Kafka-3.6-black)](https://kafka.apache.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-3.5-orange)](https://spark.apache.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

---

## Project Overview

The AI SOC Assistant collects, processes, analyzes, and monitors security logs in real time. It uses machine learning for anomaly detection and LLMs for intelligent incident summarization, giving security analysts faster and more actionable insights.

## Tech Stack

| Layer | Technology |
|---|---|
| Log Ingestion | Apache Kafka |
| Stream Processing | Apache Spark Streaming |
| Anomaly Detection | Scikit-learn / PyTorch |
| Backend API | FastAPI (Python) |
| Structured Storage | PostgreSQL |
| Log Indexing | Elasticsearch |
| Frontend Dashboard | React |
| LLM Integration | OpenAI / LangChain |

## Team Members

| Name | GitHub | Role |
|---|---|---|
| Shreerang Kolhe | [@iamShreerang](https://github.com/iamShreerang) | Backend + Integration |
| Team Member 2 | — | Big Data Pipeline |
| Team Member 3 | — | AI / ML |
| Team Member 4 | — | Frontend |

## Repository Structure

```
AI-SOC-Assistant/
├── backend/          # FastAPI application
├── frontend/         # React dashboard
├── kafka/            # Kafka producers, consumers, configs
├── spark/            # Spark streaming jobs
├── ml/               # ML models and training scripts
├── database/         # Schema, migrations, seed data
├── docs/             # Architecture diagrams, SRS, reports
└── deployment/       # Docker, docker-compose, CI/CD configs
```

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, production-ready code only |
| `backend` | FastAPI development |
| `big-data` | Kafka + Spark pipeline |
| `ai-ml` | Machine learning models |
| `frontend` | React dashboard |
| `database` | Schema and migrations |

Feature branches follow the pattern: `feature/<module>/<short-task-name>`
Example: `feature/backend/log-ingestion-api`

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker + Docker Compose
- Apache Kafka 3.6
- Apache Spark 3.5

### Setup

```bash
# Clone the repository
git clone https://github.com/iamShreerang/AI-SOC-Assistant.git
cd AI-SOC-Assistant

# Backend
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full Git workflow.

## License

This project is licensed under the GNU Affero General Public License v3.0 — see [LICENSE](LICENSE) for details.
