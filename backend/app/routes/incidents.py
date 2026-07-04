"""Incident management endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.schemas.incident import IncidentCreate, IncidentResponse, LLMSummary, IncidentStatusUpdate
from app.schemas.enums import IncidentStatus
from app.services import llm_service, db_incident_service
from app.database import get_db
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
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Get incidents with optional filtering and pagination."""
    incidents = db_incident_service.get_incidents(db, limit=limit, skip=skip, status=status)
    total = db_incident_service.get_incidents_count(db, status=status)
    return IncidentListResponse(incidents=incidents, total=total, skip=skip, limit=limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    incident = db_incident_service.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    incident = db_incident_service.create_incident(db, payload)
    
    # Auto-generate AI summary (non-blocking - failure won't block incident creation)
    try:
        summary = llm_service.generate_incident_summary(incident.model_dump(mode="json"))
        if summary:
            incident = db_incident_service.attach_summary(db, incident.id, summary)
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
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Update incident status."""
    incident = db_incident_service.update_incident_status(db, incident_id, payload.status)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@summaries_router.post("", response_model=IncidentResponse, status_code=200)
async def receive_summary(payload: LLMSummary, db: Session = Depends(get_db)):
    incident = db_incident_service.attach_summary(db, payload.incident_id, payload.summary)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
