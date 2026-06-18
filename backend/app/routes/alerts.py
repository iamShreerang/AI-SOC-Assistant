"""Alert management endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.services import alert_service
from app.utils.security import get_current_active_user

router = APIRouter()
ingest_router = APIRouter(prefix="/ingest")


@router.get("/", response_model=list[AlertResponse])
async def get_alerts(limit: int = 100, _user=Depends(get_current_active_user)):
    return alert_service.get_alerts(limit)


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


@ingest_router.post("/alerts", response_model=AlertResponse, status_code=201)
async def ingest_alert_no_auth(payload: AlertCreate):
    return alert_service.create_alert(payload)
