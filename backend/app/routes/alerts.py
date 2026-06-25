"""Alert management endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.schemas.enums import AlertSeverity, AlertStatus
from app.database import get_db
from app.services import db_alert_service
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
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Get alerts with optional filtering and pagination."""
    alerts = db_alert_service.get_alerts(
        db, limit=limit, skip=skip, severity=severity, status=status, source=source
    )
    total = db_alert_service.get_alerts_count(db, severity=severity, status=status, source=source)
    return AlertListResponse(alerts=alerts, total=total, skip=skip, limit=limit)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert_by_id(
    alert_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    alert = db_alert_service.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    return db_alert_service.create_alert(db, payload)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    alert = db_alert_service.update_alert_status(db, alert_id, payload)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/bulk/status", response_model=list[AlertResponse])
async def bulk_update_alerts(
    payload: BulkAlertUpdate,
    db: Session = Depends(get_db),
    _user=Depends(require_role("admin")),
):
    """Bulk update alert statuses (admin only)."""
    updated = db_alert_service.bulk_update_alert_status(db, payload.alert_ids, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="No alerts found with provided IDs")
    return updated


@ingest_router.post("/alerts", response_model=AlertResponse, status_code=201)
async def ingest_alert_no_auth(payload: AlertCreate, db: Session = Depends(get_db)):
    return db_alert_service.create_alert(db, payload)
