"""Incident management endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.incident import IncidentCreate, IncidentResponse, LLMSummary
from app.services import incident_service
from app.utils.security import get_current_active_user

router = APIRouter()
summaries_router = APIRouter(prefix="/summaries")


@router.get("/", response_model=list[IncidentResponse])
async def get_incidents(limit: int = 100, _user=Depends(get_current_active_user)):
    return incident_service.get_incidents(limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: int, _user=Depends(get_current_active_user)):
    incident = incident_service.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/", response_model=IncidentResponse, status_code=201)
async def create_incident(payload: IncidentCreate, _user=Depends(get_current_active_user)):
    return incident_service.create_incident(payload)


@summaries_router.post("", response_model=IncidentResponse, status_code=200)
async def receive_summary(payload: LLMSummary):
    incident = incident_service.attach_summary(payload.incident_id, payload.summary)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
