"""AI SOC Assistant — FastAPI entry point."""

from fastapi import FastAPI
from app.routes import health, logs, alerts, incidents

app = FastAPI(
    title="AI SOC Assistant API",
    description="Real-time security log ingestion, anomaly detection and incident response.",
    version="0.1.0",
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(logs.router,   prefix="/logs",      tags=["Logs"])
app.include_router(alerts.router, prefix="/alerts",    tags=["Alerts"])
app.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
