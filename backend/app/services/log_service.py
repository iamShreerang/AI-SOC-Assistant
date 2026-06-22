"""Log ingestion service — in-memory stub until DB layer is ready."""

from datetime import datetime, timezone
from typing import Optional

from app.schemas.log import LogCreate, LogResponse
from app.schemas.enums import LogSeverity

_store: dict[int, LogResponse] = {}
_counter = 0


def create_log(payload: LogCreate) -> LogResponse:
    global _counter
    _counter += 1
    entry = LogResponse(
        **payload.model_dump(),
        id=_counter,
        ingested_at=datetime.now(timezone.utc),
    )
    _store[_counter] = entry
    return entry


def get_logs(
    limit: int = 100,
    skip: int = 0,
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
) -> list[LogResponse]:
    """Get logs with optional filtering."""
    logs = list(_store.values())
    
    # Apply filters
    if severity:
        logs = [log for log in logs if log.severity == severity]
    if source:
        logs = [log for log in logs if source.lower() in log.source.lower()]
    
    # Apply pagination
    return logs[skip : skip + limit]


def get_log_by_id(log_id: int) -> Optional[LogResponse]:
    return _store.get(log_id)


def get_logs_count(
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
) -> int:
    """Get total count of logs matching filters."""
    logs = list(_store.values())
    
    if severity:
        logs = [log for log in logs if log.severity == severity]
    if source:
        logs = [log for log in logs if source.lower() in log.source.lower()]
    
    return len(logs)
