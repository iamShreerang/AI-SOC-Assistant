"""Incident service with PostgreSQL backend."""

from datetime import datetime
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas.incident import IncidentCreate, IncidentResponse
from app.schemas.enums import IncidentStatus
from app.models.database import Incident, IncidentAlert, Alert
from app.utils.config import settings
from app.utils.elasticsearch_client import get_es_client

logger = logging.getLogger(__name__)


def create_incident(db: Session, payload: IncidentCreate) -> IncidentResponse:
    """Create a new incident in the database."""
    db_incident = Incident(
        title=payload.title,
        description=payload.description,
        status=IncidentStatus.OPEN,
        created_at=datetime.utcnow(),
    )
    db.add(db_incident)
    db.flush()  # Flush to get the incident ID
    
    # Link alerts to incident
    if payload.alert_ids:
        for alert_id in payload.alert_ids:
            # Verify alert exists
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                incident_alert = IncidentAlert(
                    incident_id=db_incident.id,
                    alert_id=alert_id,
                )
                db.add(incident_alert)
    
    db.commit()
    db.refresh(db_incident)
    
    # Elasticsearch dual-write
    if settings.elasticsearch_enabled:
        try:
            client = get_es_client()
            if client:
                doc = {
                    "id": db_incident.id,
                    "title": db_incident.title,
                    "status": db_incident.status.value if hasattr(db_incident.status, 'value') else db_incident.status,
                    "description": db_incident.description,
                    "alert_ids": payload.alert_ids,
                    "summary": db_incident.summary,
                    "created_at": db_incident.created_at.isoformat() if db_incident.created_at else None,
                }
                client.index(index="soc-incidents", id=db_incident.id, document=doc)
        except Exception as e:
            logger.warning(f"Failed to index incident in Elasticsearch: {e}")
            
    return IncidentResponse(
        id=db_incident.id,
        title=db_incident.title,
        description=db_incident.description,
        alert_ids=payload.alert_ids,
        status=db_incident.status,
        summary=db_incident.summary,
        created_at=db_incident.created_at,
    )


def get_incidents(
    db: Session,
    limit: int = 100,
    skip: int = 0,
    status: Optional[IncidentStatus] = None,
) -> list[IncidentResponse]:
    """Get incidents with optional filtering and pagination."""
    query = db.query(Incident)
    
    # Apply filter
    if status:
        query = query.filter(Incident.status == status)
    
    # Apply pagination and order by most recent first
    incidents = query.order_by(Incident.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        IncidentResponse(
            id=incident.id,
            title=incident.title,
            description=incident.description,
            alert_ids=[ia.alert_id for ia in db.query(IncidentAlert).filter(IncidentAlert.incident_id == incident.id).all()],
            status=incident.status,
            summary=incident.summary,
            created_at=incident.created_at,
        )
        for incident in incidents
    ]


def get_incident_by_id(db: Session, incident_id: int) -> Optional[IncidentResponse]:
    """Get a single incident by ID."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return None
    
    # Get associated alert IDs
    alert_ids = [
        ia.alert_id 
        for ia in db.query(IncidentAlert).filter(IncidentAlert.incident_id == incident_id).all()
    ]
    
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        alert_ids=alert_ids,
        status=incident.status,
        summary=incident.summary,
        created_at=incident.created_at,
    )


def attach_summary(db: Session, incident_id: int, summary: str) -> Optional[IncidentResponse]:
    """Attach LLM-generated summary to incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return None
    
    incident.summary = summary
    incident.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(incident)
    
    # Elasticsearch dual-write
    if settings.elasticsearch_enabled:
        try:
            client = get_es_client()
            if client:
                client.update(
                    index="soc-incidents",
                    id=incident_id,
                    doc={"summary": summary}
                )
        except Exception as e:
            logger.warning(f"Failed to update incident summary in Elasticsearch: {e}")
            
    # Get associated alert IDs
    alert_ids = [
        ia.alert_id 
        for ia in db.query(IncidentAlert).filter(IncidentAlert.incident_id == incident_id).all()
    ]
    
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        alert_ids=alert_ids,
        status=incident.status,
        summary=incident.summary,
        created_at=incident.created_at,
    )


def update_incident_status(
    db: Session,
    incident_id: int,
    status: IncidentStatus
) -> Optional[IncidentResponse]:
    """Update incident status."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return None
    
    incident.status = status
    incident.updated_at = datetime.utcnow()
    
    # Set resolved_at timestamp if closing incident
    if status == IncidentStatus.CLOSED and not incident.resolved_at:
        incident.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(incident)
    
    # Elasticsearch dual-write
    if settings.elasticsearch_enabled:
        try:
            client = get_es_client()
            if client:
                client.update(
                    index="soc-incidents",
                    id=incident_id,
                    doc={"status": status.value if hasattr(status, 'value') else status}
                )
        except Exception as e:
            logger.warning(f"Failed to update incident status in Elasticsearch: {e}")
            
    # Get associated alert IDs
    alert_ids = [
        ia.alert_id 
        for ia in db.query(IncidentAlert).filter(IncidentAlert.incident_id == incident_id).all()
    ]
    
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        alert_ids=alert_ids,
        status=incident.status,
        summary=incident.summary,
        created_at=incident.created_at,
    )


def get_incidents_count(db: Session, status: Optional[IncidentStatus] = None) -> int:
    """Get total count of incidents matching filters."""
    query = db.query(func.count(Incident.id))
    
    if status:
        query = query.filter(Incident.status == status)
    
    return query.scalar()
