"""Incident service — in-memory stub until DB layer is ready."""

from datetime import datetime, timezone
from typing import Optional

from app.schemas.incident import IncidentCreate, IncidentResponse

_store: dict[int, IncidentResponse] = {}
_counter = 0


def create_incident(payload: IncidentCreate) -> IncidentResponse:
    global _counter
    _counter += 1
    entry = IncidentResponse(
        **payload.model_dump(),
        id=_counter,
        status="open",
        summary=None,
        created_at=datetime.now(timezone.utc),
    )
    _store[_counter] = entry
    return entry


def get_incidents(limit: int = 100) -> list[IncidentResponse]:
    return list(_store.values())[-limit:]


def get_incident_by_id(incident_id: int) -> Optional[IncidentResponse]:
    return _store.get(incident_id)


def attach_summary(incident_id: int, summary: str) -> Optional[IncidentResponse]:
    incident = _store.get(incident_id)
    if incident is None:
        return None
    _store[incident_id] = incident.model_copy(update={"summary": summary})
    return _store[incident_id]
