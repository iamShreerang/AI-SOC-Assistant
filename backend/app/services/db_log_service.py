"""Log service with PostgreSQL backend."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas.log import LogCreate, LogResponse
from app.schemas.enums import LogSeverity
from app.models.database import Log


def create_log(db: Session, payload: LogCreate) -> LogResponse:
    """Create a new log entry in the database."""
    db_log = Log(
        source=payload.source,
        severity=payload.severity,
        message=payload.message,
        timestamp=payload.timestamp,
        raw=payload.raw,
        ingested_at=datetime.utcnow(),
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return LogResponse(
        id=db_log.id,
        source=db_log.source,
        severity=db_log.severity,
        message=db_log.message,
        timestamp=db_log.timestamp,
        raw=db_log.raw,
        ingested_at=db_log.ingested_at,
    )


def get_logs(
    db: Session,
    limit: int = 100,
    skip: int = 0,
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
) -> list[LogResponse]:
    """Get logs with optional filtering and pagination."""
    query = db.query(Log)
    
    # Apply filters
    if severity:
        query = query.filter(Log.severity == severity)
    if source:
        query = query.filter(Log.source.ilike(f"%{source}%"))
    
    # Apply pagination and order by most recent first
    logs = query.order_by(Log.ingested_at.desc()).offset(skip).limit(limit).all()
    
    return [
        LogResponse(
            id=log.id,
            source=log.source,
            severity=log.severity,
            message=log.message,
            timestamp=log.timestamp,
            raw=log.raw,
            ingested_at=log.ingested_at,
        )
        for log in logs
    ]


def get_log_by_id(db: Session, log_id: int) -> Optional[LogResponse]:
    """Get a single log by ID."""
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        return None
    
    return LogResponse(
        id=log.id,
        source=log.source,
        severity=log.severity,
        message=log.message,
        timestamp=log.timestamp,
        raw=log.raw,
        ingested_at=log.ingested_at,
    )


def get_logs_count(
    db: Session,
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
) -> int:
    """Get total count of logs matching filters."""
    query = db.query(func.count(Log.id))
    
    if severity:
        query = query.filter(Log.severity == severity)
    if source:
        query = query.filter(Log.source.ilike(f"%{source}%"))
    
    return query.scalar()
