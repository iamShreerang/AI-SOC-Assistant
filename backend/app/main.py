"""AI SOC Assistant — FastAPI entry point."""

import logging
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.utils.config import settings
from app.utils.elasticsearch_client import create_indices, check_es_connection
from app.database import check_connection, create_tables, SessionLocal
from app.services.db_auth_service import create_default_users

from app.routes import health, auth
from app.routes.logs import router as logs_router, ingest_router as logs_ingest_router
from app.routes.alerts import router as alerts_router, ingest_router as alerts_ingest_router
from app.routes.incidents import router as incidents_router, summaries_router
from app.routes import stats, search, export, audit

logger = logging.getLogger(__name__)

_DESCRIPTION = """
## AI SOC Assistant API

Real-time security log ingestion, anomaly detection, and intelligent incident response.

---

### Authentication Flow

All analyst/admin endpoints require a **Bearer JWT token**.

1. **Register** — `POST /auth/register` with `username`, `password`, optional `role` (`analyst` | `admin`)
2. **Login** — `POST /auth/login` → receive `{"access_token": "...", "token_type": "bearer"}`
3. **Use token** — add header `Authorization: Bearer <access_token>` to every protected request
4. **Inspect identity** — `GET /auth/users/me` returns the caller's username and role

Tokens expire after **15 minutes**. Re-login to obtain a fresh token.

---

### Integration Endpoints (Internal Pipeline — No Auth Required)

These endpoints are called by other modules in the AI SOC pipeline, not by human users.
They accept JSON only and must **not** be exposed to the public internet.

| Caller | Endpoint | Purpose |
|---|---|---|
| **Kafka consumer** (Ayush) | `POST /ingest/logs` | Forward a parsed log from a Kafka topic into the backend store |
| **ML anomaly detector** (Sayog) | `POST /ingest/alerts` | Push a detected anomaly as an alert into the backend store |
| **LLM summariser** (Sayog) | `POST /summaries` | Attach an AI-generated narrative summary to an existing incident |

---

### Roles

| Role | Access |
|---|---|
| `analyst` | Read/write logs, alerts, incidents |
| `admin` | All analyst permissions + user management (future) |
"""

tags_metadata = [
    {
        "name": "Health",
        "description": "Service liveness probe. No authentication required.",
    },
    {
        "name": "Auth",
        "description": (
            "User registration, login, and identity. "
            "Login returns a short-lived JWT bearer token used by all protected endpoints. "
            "Admin users can manage other users via /auth/users endpoints."
        ),
    },
    {
        "name": "Logs",
        "description": (
            "Security log ingestion and retrieval. "
            "Logs are raw or parsed entries from sources such as firewalls, IDS, and SIEM systems. "
            "Supports filtering by severity and source with pagination. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Alerts",
        "description": (
            "Security alert management. "
            "Alerts are raised when a log pattern or ML model signals anomalous behaviour. "
            "Supports status transitions: `open` → `acknowledged` → `resolved`. "
            "Supports filtering by severity, status, and source with pagination. "
            "Includes bulk status update endpoint. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Incidents",
        "description": (
            "Incident lifecycle management. "
            "An incident groups one or more alerts into a tracked investigation case. "
            "Incidents can receive an AI-generated summary from the LLM module. "
            "Supports status transitions: `open` → `in-progress` → `closed`. "
            "Supports filtering by status with pagination. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Ingest",
        "description": (
            "**Internal pipeline endpoints — no authentication required.** "
            "Called exclusively by the Kafka consumer (`/ingest/logs`), "
            "ML anomaly detector (`/ingest/alerts`), and LLM summariser (`/summaries`). "
            "Do not expose these to end users."
        ),
    },
    {
        "name": "Statistics",
        "description": (
            "Dashboard analytics and statistics endpoints. "
            "Provides summary metrics, activity trends, and breakdowns for visualization. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Search",
        "description": (
            "Full-text search across logs, alerts, and incidents. "
            "Search by keywords in messages, titles, descriptions, and summaries. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Export",
        "description": (
            "Data export endpoints for logs, alerts, and incidents. "
            "Supports CSV and JSON formats with optional filtering. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Audit",
        "description": (
            "Audit trail for administrative actions. "
            "Tracks user management operations and system changes. "
            "**Requires admin role.**"
        ),
    },
]

app = FastAPI(
    title="AI SOC Assistant API",
    description=_DESCRIPTION,
    version="0.1.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "Shreerang Kolhe",
        "url": "https://github.com/iamShreerang/AI-SOC-Assistant",
    },
    license_info={
        "name": "AGPL v3",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(status_code=429, content={"detail": "Too many requests, slow down."})
)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])

# Statistics, Search, Export, and Audit endpoints
app.include_router(stats.router, prefix="/stats", tags=["Statistics"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(export.router, prefix="/export", tags=["Export"])
app.include_router(audit.router, prefix="/audit", tags=["Audit"])

# Internal integration endpoints (no auth — pipeline use only)
app.include_router(logs_ingest_router, tags=["Ingest"])
app.include_router(alerts_ingest_router, tags=["Ingest"])
app.include_router(summaries_router, tags=["Ingest"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and Elasticsearch on startup."""
    # Check database connection
    logger.info("Checking database connection...")
    if not check_connection():
        logger.error("Failed to connect to database. Check DATABASE_URL")
        raise Exception("Database connection failed")
    
    logger.info("[OK] Database connected")
    
    # Create tables (development only - use Alembic in production)
    try:
        create_tables()
        logger.info("[OK] Tables initialized")
    except Exception as e:
        logger.warning(f"Tables may already exist: {e}")
    
    # Create default users
    try:
        db = SessionLocal()
        create_default_users(db)
        db.close()
        logger.info("[OK] Default users ready")
    except Exception as e:
        logger.error(f"User init failed: {e}")
    
    # Initialize Elasticsearch
    if settings.elasticsearch_enabled:
        if check_es_connection():
            create_indices()
            logger.info("[OK] Elasticsearch ready")
        else:
            logger.warning("[WARNING] Elasticsearch unavailable")
    else:
        logger.info("[INFO] Elasticsearch disabled")
