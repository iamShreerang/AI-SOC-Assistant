"""Incident service — in-memory stub until DB layer is ready."""

from datetime import datetime, timezone
from typing import Optional

from app.schemas.incident import IncidentCreate, IncidentResponse
from app.schemas.enums import IncidentStatus

_store: dict[int, IncidentResponse] = {}
_counter = 0


def create_incident(payload: IncidentCreate) -> IncidentResponse:
    global _counter
    _counter += 1
    entry = IncidentResponse(
        **payload.model_dump(),
        id=_counter,
        status=IncidentStatus.OPEN,
        summary=None,
        created_at=datetime.now(timezone.utc),
    )
    _store[_counter] = entry
    return entry


def get_incidents(
    limit: int = 100,
    skip: int = 0,
    status: Optional[IncidentStatus] = None,
) -> list[IncidentResponse]:
    """Get incidents with optional filtering."""
    incidents = list(_store.values())
    
    # Apply filter
    if status:
        incidents = [inc for inc in incidents if inc.status == status]
    
    # Apply pagination
    return incidents[skip : skip + limit]


def get_incident_by_id(incident_id: int) -> Optional[IncidentResponse]:
    return _store.get(incident_id)


def attach_summary(incident_id: int, summary: str) -> Optional[IncidentResponse]:
    incident = _store.get(incident_id)
    if incident is None:
        return None
    _store[incident_id] = incident.model_copy(update={"summary": summary})
    return _store[incident_id]


def update_incident_status(incident_id: int, status: IncidentStatus) -> Optional[IncidentResponse]:
    """Update incident status."""
    incident = _store.get(incident_id)
    if incident is None:
        return None
    _store[incident_id] = incident.model_copy(update={"status": status})
    return _store[incident_id]


def get_incidents_count(status: Optional[IncidentStatus] = None) -> int:
    """Get total count of incidents matching filters."""
    incidents = list(_store.values())
    
    if status:
        incidents = [inc for inc in incidents if inc.status == status]
    
    return len(incidents)
