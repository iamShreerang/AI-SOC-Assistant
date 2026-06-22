"""Log ingestion and retrieval endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.schemas.log import LogCreate, LogResponse
from app.schemas.enums import LogSeverity
from app.utils.config import settings

# Use Elasticsearch service if enabled, otherwise use in-memory
if settings.elasticsearch_enabled:
    from app.services import es_log_service as log_service
else:
    from app.services import log_service

from app.utils.security import get_current_active_user

router = APIRouter()
ingest_router = APIRouter(prefix="/ingest")


class LogListResponse(BaseModel):
    """Paginated log list response."""
    logs: list[LogResponse]
    total: int
    skip: int
    limit: int


@router.get("/", response_model=LogListResponse)
async def get_logs(
    limit: int = 100,
    skip: int = 0,
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
    _user=Depends(get_current_active_user),
):
    """Get logs with optional filtering and pagination."""
    logs = log_service.get_logs(limit=limit, skip=skip, severity=severity, source=source)
    total = log_service.get_logs_count(severity=severity, source=source)
    return LogListResponse(logs=logs, total=total, skip=skip, limit=limit)


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
