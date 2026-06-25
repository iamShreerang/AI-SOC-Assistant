"""Incident management endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.schemas.incident import IncidentCreate, IncidentResponse, LLMSummary, IncidentStatusUpdate
from app.schemas.enums import IncidentStatus
from app.services import llm_service
from app.utils.config import settings

# Use Elasticsearch service if enabled, otherwise use in-memory
if settings.elasticsearch_enabled:
    from app.services import es_incident_service as incident_service
else:
    from app.services import incident_service

from app.utils.security import get_current_active_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter()
summaries_router = APIRouter(prefix="/summaries")


class IncidentListResponse(BaseModel):
    """Paginated incident list response."""
    incidents: list[IncidentResponse]
    total: int
    skip: int
    limit: int


@router.get("/", response_model=IncidentListResponse)
async def get_incidents(
    limit: int = 100,
    skip: int = 0,
    status: Optional[IncidentStatus] = None,
    _user=Depends(get_current_active_user),
):
    """Get incidents with optional filtering and pagination."""
    incidents = incident_service.get_incidents(limit=limit, skip=skip, status=status)
    total = incident_service.get_incidents_count(status=status)
    return IncidentListResponse(incidents=incidents, total=total, skip=skip, limit=limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, _user=Depends(get_current_active_user)):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/", response_model=IncidentResponse, status_code=201)
async def create_incident(payload: IncidentCreate, _user=Depends(get_current_active_user)):
    incident = incident_service.create_incident(payload)
    
    # Auto-generate AI summary (non-blocking - failure won't block incident creation)
    try:
        summary = llm_service.generate_incident_summary(incident.model_dump())
        if summary:
            incident = incident_service.attach_summary(incident.id, summary)
            logger.info(f"Auto-generated summary for incident {incident.id}")
        else:
            logger.info(f"Summary generation skipped for incident {incident.id}")
    except Exception as e:
        logger.warning(f"Summary generation failed for incident {incident.id}: {e}")
    
    return incident


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdate,
    _user=Depends(get_current_active_user),
):
    """Update incident status."""
    incident = incident_service.update_incident_status(incident_id, payload.status)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@summaries_router.post("", response_model=IncidentResponse, status_code=200)
async def receive_summary(payload: LLMSummary):
    incident = incident_service.attach_summary(payload.incident_id, payload.summary)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
