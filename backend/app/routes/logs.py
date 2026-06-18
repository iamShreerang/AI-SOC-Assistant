"""Log ingestion and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.log import LogCreate, LogResponse
from app.services import log_service
from app.utils.security import get_current_active_user

router = APIRouter()
ingest_router = APIRouter(prefix="/ingest")


@router.get("/", response_model=list[LogResponse])
async def get_logs(limit: int = 100, _user=Depends(get_current_active_user)):
    return log_service.get_logs(limit)


@router.get("/{log_id}", response_model=LogResponse)
async def get_log_by_id(log_id: int, _user=Depends(get_current_active_user)):
    log = log_service.get_log_by_id(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@router.post("/", response_model=LogResponse, status_code=201)
async def ingest_log(payload: LogCreate, _user=Depends(get_current_active_user)):
    return log_service.create_log(payload)


@ingest_router.post("/logs", response_model=LogResponse, status_code=201)
async def ingest_log_no_auth(payload: LogCreate):
    return log_service.create_log(payload)
