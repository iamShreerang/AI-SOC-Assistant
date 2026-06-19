"""AI SOC Assistant — FastAPI entry point."""

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.utils.config import settings

from app.routes import health, auth
from app.routes.logs import router as logs_router, ingest_router as logs_ingest_router
from app.routes.alerts import router as alerts_router, ingest_router as alerts_ingest_router
from app.routes.incidents import router as incidents_router, summaries_router

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
            "Login returns a short-lived JWT bearer token used by all protected endpoints."
        ),
    },
    {
        "name": "Logs",
        "description": (
            "Security log ingestion and retrieval. "
            "Logs are raw or parsed entries from sources such as firewalls, IDS, and SIEM systems. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Alerts",
        "description": (
            "Security alert management. "
            "Alerts are raised when a log pattern or ML model signals anomalous behaviour. "
            "Supports status transitions: `open` → `acknowledged` → `resolved`. "
            "**Requires authentication.**"
        ),
    },
    {
        "name": "Incidents",
        "description": (
            "Incident lifecycle management. "
            "An incident groups one or more alerts into a tracked investigation case. "
            "Incidents can receive an AI-generated summary from the LLM module. "
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

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(logs_router, prefix="/logs", tags=["Logs"])
app.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
app.include_router(incidents_router, prefix="/incidents", tags=["Incidents"])

# Internal integration endpoints (no auth — pipeline use only)
app.include_router(logs_ingest_router, tags=["Ingest"])
app.include_router(alerts_ingest_router, tags=["Ingest"])
app.include_router(summaries_router, tags=["Ingest"])
