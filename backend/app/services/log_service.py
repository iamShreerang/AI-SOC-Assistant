"""Log ingestion service — in-memory stub until DB layer is ready."""

from datetime import datetime, timezone
from typing import Optional

from app.schemas.log import LogCreate, LogResponse

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


def get_logs(limit: int = 100) -> list[LogResponse]:
    return list(_store.values())[-limit:]


def get_log_by_id(log_id: int) -> Optional[LogResponse]:
    return _store.get(log_id)
