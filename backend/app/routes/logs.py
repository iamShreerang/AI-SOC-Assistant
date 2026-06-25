"""Log ingestion and retrieval endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.schemas.log import LogCreate, LogResponse
from app.schemas.enums import LogSeverity
from app.services import db_log_service
from app.database import get_db
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
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Get logs with optional filtering and pagination."""
    logs = db_log_service.get_logs(db, limit=limit, skip=skip, severity=severity, source=source)
    total = db_log_service.get_logs_count(db, severity=severity, source=source)
    return LogListResponse(logs=logs, total=total, skip=skip, limit=limit)


@router.get("/{log_id}", response_model=LogResponse)
async def get_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    log = db_log_service.get_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log


@router.post("/", response_model=LogResponse, status_code=201)
async def ingest_log(
    payload: LogCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    return db_log_service.create_log(db, payload)


@ingest_router.post("/logs", response_model=LogResponse, status_code=201)
async def ingest_log_no_auth(payload: LogCreate, db: Session = Depends(get_db)):
    return db_log_service.create_log(db, payload)
