"""Alert management endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.schemas.enums import AlertSeverity, AlertStatus
from app.utils.config import settings

# Use Elasticsearch service if enabled, otherwise use in-memory
if settings.elasticsearch_enabled:
    from app.services import es_alert_service as alert_service
else:
    from app.services import alert_service

from app.utils.security import get_current_active_user, require_role

router = APIRouter()
ingest_router = APIRouter(prefix="/ingest")


class AlertListResponse(BaseModel):
    """Paginated alert list response."""
    alerts: list[AlertResponse]
    total: int
    skip: int
    limit: int


class BulkAlertUpdate(BaseModel):
    """Bulk alert status update."""
    alert_ids: list[int] = Field(..., description="List of alert IDs to update")
    status: AlertStatus = Field(..., description="New status for all alerts")


@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    limit: int = 100,
    skip: int = 0,
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
    _user=Depends(get_current_active_user),
):
    """Get alerts with optional filtering and pagination."""
    alerts = alert_service.get_alerts(
        limit=limit, skip=skip, severity=severity, status=status, source=source
    )
    total = alert_service.get_alerts_count(severity=severity, status=status, source=source)
    return AlertListResponse(alerts=alerts, total=total, skip=skip, limit=limit)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_by_id(alert_id: int, _user=Depends(get_current_active_user)):
    alert = alert_service.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(payload: AlertCreate, _user=Depends(get_current_active_user)):
    return alert_service.create_alert(payload)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: int, payload: AlertUpdate, _user=Depends(get_current_active_user)):
    alert = alert_service.update_alert_status(alert_id, payload)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/bulk/status", response_model=list[AlertResponse])
async def bulk_update_alerts(
    payload: BulkAlertUpdate,
    _user=Depends(require_role("admin")),
):
    """Bulk update alert statuses (admin only)."""
    updated = alert_service.bulk_update_alert_status(payload.alert_ids, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="No alerts found with provided IDs")
    return updated


@ingest_router.post("/alerts", response_model=AlertResponse, status_code=201)
async def ingest_alert_no_auth(payload: AlertCreate):
    return alert_service.create_alert(payload)
