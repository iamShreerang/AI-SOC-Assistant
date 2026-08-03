# ⚙️ AI SOC Assistant — Backend Connections & Important Code Files Guide

---

## 🔌 1. Complete Map of Backend Connections & Integrations

The backend server is built using **FastAPI (Python 3.11)**. It acts as the central intelligence hub connecting the database, machine learning pipeline, message queues, AI LLM services, and the React frontend.

```
                            ┌───────────────────────────────────────┐
                            │           REACT FRONTEND              │
                            │      http://localhost:3001            │
                            └───────────────────┬───────────────────┘
                                                │ (REST API via Axios / api.ts)
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FASTAPI BACKEND SERVER                                  │
│                                 http://127.0.0.1:8000                                   │
│  app/main.py                                                                            │
│                                                                                         │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────┐  │
│  │   Auth & Security     │   │   Ingestion Routes    │   │   Stats & Analytics       │  │
│  │   app/routes/auth.py  │   │   app/routes/ingest.py│   │   app/routes/stats.py     │  │
│  └───────────┬───────────┘   └───────────┬───────────┘   └─────────────┬─────────────┘  │
└──────────────┼───────────────────────────┼─────────────────────────────┼────────────────┘
               │                           │                             │
               ▼                           ▼                             ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐ ┌──────────────────────────┐
│     SUPABASE POSTGRESQL      │ │    SPARK & KAFKA INGESTION   │ │      GROQ LLM API        │
│ app/database.py              │ │ streaming/backend_client.py │ │ app/services/llm_service │
│ PostgreSQL via SQLAlchemy    │ │ POST /ingest/logs & alerts  │ │ Groq LLaMA 3.1 8B Instant│
└──────────────────────────────┘ └─────────────────────────────┘ └──────────────────────────┘
```

---

### A. Database Connection (Supabase PostgreSQL)
- **File**: `backend/app/database.py`
- **Driver & Protocol**: `postgresql+psycopg2://` (or `postgresql://`)
- **Config Variable**: `DATABASE_URL` stored in `.env`
- **Key Code Logic**:
  ```python
  engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  ```
- **Connection Management (`get_db`)**:
  Per-request database session dependency using `yield`. Ensures sessions are cleanly closed (`db.close()`) after every request, preventing connection leaks:
  ```python
  def get_db():
      db = SessionLocal()
      try:
          yield db
      finally:
          db.close()
  ```

---

### B. Streaming Pipeline Ingestion Connection
- **Files**: `streaming/backend_client.py` (Client) → `backend/app/routes/ingest.py` (Server)
- **Protocol**: Synchronous HTTP/1.1 via `requests` / `httpx`
- **Endpoints**:
  - `POST http://127.0.0.1:8000/ingest/logs` — Saves flow logs into the `logs` table.
  - `POST http://127.0.0.1:8000/ingest/alerts` — Saves Spark ML & Threat Rule alerts into the `alerts` table.
  - `POST http://127.0.0.1:8000/ingest/heartbeat` — Updates PySpark operational health status in `service_heartbeats`.
- **Key Code Logic (`backend_client.py`)**:
  ```python
  def post_log(source: str, severity: str, message: str, ...):
      res = requests.post(f"{BACKEND_URL}/ingest/logs", json=payload, timeout=2.0)
      return res.status_code == 200
  ```

---

### C. Generative AI Connection (Groq Cloud LLM API)
- **File**: `backend/app/services/llm_service.py`
- **Client**: `groq.Groq(api_key=settings.groq_api_key)`
- **Model**: `llama-3.1-8b-instant`
- **Trigger**: Called automatically by `db_alert_service.py` when `High` or `Critical` severity alerts are created, or manually via `POST /incidents/{id}/generate-summary`.
- **Key Code Logic**:
  ```python
  client = Groq(api_key=settings.groq_api_key)
  chat_completion = client.chat.completions.create(
      messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
      model="llama-3.1-8b-instant",
      temperature=0.3,
  )
  ```

---

### D. Optional Elasticsearch Dual-Write Connection
- **File**: `backend/app/utils/elasticsearch_client.py`
- **Client**: `elasticsearch.Elasticsearch(settings.elasticsearch_url, request_timeout=2)`
- **Function**: Performs dual-write log indexing alongside PostgreSQL for ultra-fast full-text log search.

---

### E. Frontend to Backend Connection
- **File**: `frontend/src/services/api.ts`
- **Client**: Axios instance configured with `baseURL = 'http://localhost:8000'`
- **Authentication**: Includes JWT Bearer Token in HTTP headers: `Authorization: Bearer <token>`.

---

## 📁 2. File-by-File Technical Directory & Purpose

### 1. Core Server Entry & Configuration
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`backend/app/main.py`** | **FastAPI Application Entry Point**. Configures CORS middleware (`CORSMiddleware`), registers API routers, sets up root `/health` probe, and initializes database tables on startup (`Base.metadata.create_all`). |
| **`backend/app/database.py`** | **Database Engine & Session Factory**. Defines SQLAlchemy `engine`, `SessionLocal`, and `get_db()` dependency for dependency injection into FastAPI routes. |
| **`backend/app/utils/config.py`** | **Central Application Settings**. Uses `pydantic_settings.BaseSettings` to load and validate environment variables from `.env` (`DATABASE_URL`, `SECRET_KEY`, `GROQ_API_KEY`, `ELASTICSEARCH_URL`). |

---

### 2. Database Models (SQLAlchemy ORM)
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`backend/app/models/database.py`** | **Database Schema Definitions**. Contains SQLAlchemy ORM classes: <br>• `User`: User accounts, hashed passwords, roles (`admin`, `analyst`).<br>• `Log`: Security log entries (`source`, `severity`, `message`, `raw`, `timestamp`).<br>• `Alert`: Threat detections (`title`, `severity`, `source`, `description`, `status`).<br>• `Incident`: High-level security cases (`title`, `description`, `status`, `summary`).<br>• `IncidentAlert`: Many-to-many join table linking `Alert` records to `Incident` records.<br>• `ServiceHeartbeat`: Pipeline component status monitoring (`service`, `status`, `last_seen`).<br>• `AuditLog`: System security audit trail. |

---

### 3. Business Logic Services (`app/services/`)
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`backend/app/services/db_auth_service.py`** | **Authentication Logic**. Handles user login validation, password hashing via `passlib.context.CryptContext` (bcrypt), and JWT access token creation. |
| **`backend/app/services/db_log_service.py`** | **Log Ingestion & Retrieval**. Manages database insertions for flow logs, pagination (`limit`/`offset`), and severity filtering. |
| **`backend/app/services/db_alert_service.py`** | **Alert Processing & Real-Time Incident Automation**. Inserts alerts into DB. **Auto-creates Incidents** when `High` or `Critical` alerts fire and triggers `llm_service` for Groq summary generation. |
| **`backend/app/services/db_incident_service.py`** | **Incident Lifecycle Management**. Handles creation, status updates (`open`, `in-progress`, `closed`), and attaching AI summaries to incidents. |
| **`backend/app/services/db_stats_service.py`** | **Analytics & Aggregations**. Executes SQL aggregation queries (`COUNT`, `GROUP BY`) for dashboard summary counts, severity distributions, ML accuracy rates, and 6-hour anomaly activity trends. |
| **`backend/app/services/llm_service.py`** | **Groq LLaMA 3.1 Integration**. Formats prompt with alert telemetry, invokes Groq API, and parses structured Executive Summaries and Action Playbooks. |

---

### 4. API Routes (`app/routes/`)
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`backend/app/routes/auth.py`** | `POST /auth/login`, `POST /auth/register`, `GET /auth/me`. Authenticates users and issues JWT Bearer tokens. |
| **`backend/app/routes/ingest.py`** | `POST /ingest/logs`, `POST /ingest/alerts`, `POST /ingest/heartbeat`. Unauthenticated internal ingestion routes used by Spark and Kafka. |
| **`backend/app/routes/logs.py`** | `GET /logs/`, `GET /logs/{id}`. Fetches paginated logs for the Log Explorer and Real-Time Monitoring frontend pages. |
| **`backend/app/routes/alerts.py`** | `GET /alerts/`, `PATCH /alerts/{id}/status`. Fetches and updates security alerts. |
| **`backend/app/routes/incidents.py`** | `GET /incidents/`, `POST /incidents/`, `POST /incidents/{id}/generate-summary`. Incident management and on-demand LLM summary trigger. |
| **`backend/app/routes/stats.py`** | `GET /stats/summary`, `GET /stats/ml`, `GET /stats/activity`. Provides real-time metrics for Dashboard and ML Analytics. |
| **`backend/app/routes/health.py`** | `GET /health`. Probes DB, Kafka, Spark heartbeats, ML model files, and Groq API status. |

---

### 5. Security & Schemas
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`backend/app/utils/security.py`** | Contains `get_password_hash()`, `verify_password()`, `create_access_token()`, and `get_current_active_user()` FastAPI security dependencies for JWT decoding and verification. |
| **`backend/app/schemas/`** | Pydantic models (`log.py`, `alert.py`, `incident.py`, `auth.py`, `enums.py`) defining strict payload validation schemas and serialization formatters. |

---

## 💻 3. Frontend Architecture & Important UI Files (`frontend/src/`)

Your role includes **Frontend Development**. Here is every key frontend file, its exact location, and why it is important:

### A. Services, Hooks & Utilities
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`frontend/src/services/api.ts`** | **Frontend API Service Layer**. Centralized Axios client calling backend REST endpoints (`/stats/summary`, `/logs`, `/alerts`, `/incidents`, `/stats/ml`, `/incidents/{id}/generate-summary`). Automatically attaches JWT Bearer token. |
| **`frontend/src/hooks/index.ts`** | **Custom React Hooks**. Contains `usePolling()`, which runs an initial fetch with loading spinner, then establishes a silent background `setInterval` loop (every 3s) to refresh UI data without screen flicker. |
| **`frontend/src/utils/helpers.ts`** | **Formatting & Timezone Utilities**. Contains `ensureUtcDate()` which appends `Z` to naive UTC ISO timestamp strings from Python, ensuring date-fns `formatRelativeTime()` correctly displays *"less than a minute ago"* in local time instead of 5.5 hour offset errors. |
| **`frontend/src/store/index.ts`** | **Global State Management**. Zustand store managing global UI notification popups and toast messages. |

### B. Dashboard & Page Components (`frontend/src/pages/`)
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`frontend/src/pages/Dashboard.tsx`** | **Main SOC Security Dashboard**. Displays Total Events, Active Threats, Open Alerts, Open Incidents stat cards, Donut Charts for alert severity distributions, and real-time System Health monitors. |
| **`frontend/src/pages/Monitoring.tsx`** | **Real-Time Event Stream**. Renders live scrolling stream of network traffic and flagged events with live activity pulsing badges. |
| **`frontend/src/pages/LogExplorer.tsx`** | **Log Repository Explorer**. Searchable and filterable table listing all ingested flow logs with severity badges and raw payload details. |
| **`frontend/src/pages/Alerts.tsx`** | **Security Alerts Page**. Renders security alerts, allowing analysts to filter by severity (`Critical`, `High`, `Medium`, `Low`) and update alert statuses (`open`, `acknowledged`, `resolved`). |
| **`frontend/src/pages/Incidents.tsx`** | **Security Incidents Page & Creation Modal**. Renders active security incidents and includes an interactive modal (`+ Create Incident`) to manually package alerts into investigation cases. |
| **`frontend/src/pages/IncidentDetail.tsx`** | **Incident Detail & AI Summary Page**. Displays detailed incident telemetry and features the **`✨ Generate AI Summary`** button that triggers Groq LLaMA 3.1 LLM response playbooks. |
| **`frontend/src/pages/MLAnalytics.tsx`** | **Machine Learning Insights Page**. Renders ML Resolution Rate %, total predictions, 6-hour anomaly score trend chart, alert severity donut chart, and top 10 high-risk alerts with confidence progress bars. |

### C. Data Visualizations (`frontend/src/components/charts/`)
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`frontend/src/components/charts/index.tsx`** | **Recharts Components**. Implements customized, responsive charts (`DonutChart`, `BarChartComponent`, `LineChartComponent`) tuned for dark-mode SOC aesthetics with bottom legend positioning to prevent label collision. |

---

## ❓ 4. Top Viva Questions Across Your Entire Role

### Q1: How does FastAPI handle database connection pooling and session cleanup?
**Answer:** In `database.py`, we use SQLAlchemy's `create_engine` with `pool_size=10`, `max_overflow=20`, and `pool_pre_ping=True` (which tests connections before issuing queries to prevent stale connection errors). Each route receives a database session via the `get_db()` generator dependency. The `try...finally` block in `get_db()` guarantees `db.close()` runs after every request, returning the connection safely back to the pool.

### Q2: How does authentication and route protection work in your backend?
**Answer:** Users authenticate at `POST /auth/login`. Upon verifying credentials with `bcrypt`, `security.py` generates an OAuth2-compliant JWT token signed with `HS256` and our `SECRET_KEY`. Protected routes include `Depends(get_current_active_user)`, which extracts the HTTP `Authorization: Bearer <token>` header, decodes the JWT, and verifies the user is active before executing the route logic.

### Q3: How did you implement real-time UI updates on the frontend without WebSockets?
**Answer:** We created a custom React `usePolling` hook in `frontend/src/hooks/index.ts`. On component mount, it triggers an initial fetch with a loading spinner. Afterward, it sets a silent background `setInterval` polling loop (every 3 seconds). When `usePolling` re-fetches data from `/stats/summary` or `/monitoring`, it updates React component state silently without setting `loading = true`, eliminating UI flickering while keeping all numbers perfectly in sync with the database.

### Q4: How does the backend trigger Groq LLM summaries automatically?
**Answer:** When an alert is ingested via `db_alert_service.py`, if its severity is `High` or `Critical`, the service automatically calls `create_incident()` in `db_incident_service.py`. It then invokes `generate_incident_summary()` in `llm_service.py`, which formats a structured prompt and calls Groq's LLaMA 3.1 API. The resulting response playbook is saved to the `summary` column of the incident record in PostgreSQL.

### Q5: How did you fix the timezone offset bug between Python backend timestamps and JavaScript frontend rendering?
**Answer:** Python FastAPI returns timestamps formatted as naive UTC ISO strings (e.g. `2026-08-03T09:55:22`). Without a trailing `Z` suffix, browser JavaScript interpreted the string as local time instead of UTC, causing `date-fns` to subtract 5.5 hours and display *"about 6 hours ago"*. We created `ensureUtcDate()` in `frontend/src/utils/helpers.ts` which detects missing timezone offsets and appends `Z`, ensuring JavaScript accurately converts the UTC timestamp into the user's local timezone.

