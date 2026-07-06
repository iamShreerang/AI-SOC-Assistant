"""Alert service with PostgreSQL backend."""

from datetime import datetime
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.schemas.enums import AlertSeverity, AlertStatus
from app.models.database import Alert
from app.utils.config import settings
from app.utils.elasticsearch_client import get_es_client

logger = logging.getLogger(__name__)


def create_alert(db: Session, payload: AlertCreate) -> AlertResponse:
    """Create a new alert in the database."""
    db_alert = Alert(
        title=payload.title,
        severity=payload.severity,
        source=payload.source,
        description=payload.description,
        status=AlertStatus.OPEN,
        created_at=datetime.utcnow(),
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    
    # Elasticsearch dual-write
    if settings.elasticsearch_enabled:
        try:
            client = get_es_client()
            if client:
                doc = {
                    "id": db_alert.id,
                    "title": db_alert.title,
                    "severity": db_alert.severity.value if hasattr(db_alert.severity, 'value') else db_alert.severity,
                    "status": db_alert.status.value if hasattr(db_alert.status, 'value') else db_alert.status,
                    "source": db_alert.source,
                    "description": db_alert.description,
                    "created_at": db_alert.created_at.isoformat() if db_alert.created_at else None,
                }
                client.index(index="soc-alerts", id=db_alert.id, document=doc)
        except Exception as e:
            logger.warning(f"Failed to index alert in Elasticsearch: {e}")
            
    return AlertResponse(
        id=db_alert.id,
        title=db_alert.title,
        severity=db_alert.severity,
        source=db_alert.source,
        description=db_alert.description,
        status=db_alert.status,
        created_at=db_alert.created_at,
    )


def get_alerts(
    db: Session,
    limit: int = 100,
    skip: int = 0,
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
) -> list[AlertResponse]:
    """Get alerts with optional filtering and pagination."""
    query = db.query(Alert)
    
    # Apply filters
    if severity:
        query = query.filter(Alert.severity == severity)
    if status:
        query = query.filter(Alert.status == status)
    if source:
        query = query.filter(Alert.source.ilike(f"%{source}%"))
    
    # Apply pagination and order by most recent first
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        AlertResponse(
            id=alert.id,
            title=alert.title,
            severity=alert.severity,
            source=alert.source,
            description=alert.description,
            status=alert.status,
            created_at=alert.created_at,
        )
        for alert in alerts
    ]


def get_alert_by_id(db: Session, alert_id: int) -> Optional[AlertResponse]:
    """Get a single alert by ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    
    return AlertResponse(
        id=alert.id,
        title=alert.title,
        severity=alert.severity,
        source=alert.source,
        description=alert.description,
        status=alert.status,
        created_at=alert.created_at,
    )


def update_alert_status(
    db: Session,
    alert_id: int,
    payload: AlertUpdate
) -> Optional[AlertResponse]:
    """Update alert status."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return None
    
    alert.status = payload.status
    alert.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    
    # Elasticsearch dual-write
    if settings.elasticsearch_enabled:
        try:
            client = get_es_client()
            if client:
                client.update(
                    index="soc-alerts",
                    id=alert_id,
                    doc={"status": payload.status.value if hasattr(payload.status, 'value') else payload.status}
                )
        except Exception as e:
            logger.warning(f"Failed to update alert in Elasticsearch: {e}")
            
    return AlertResponse(
        id=alert.id,
        title=alert.title,
        severity=alert.severity,
        source=alert.source,
        description=alert.description,
        status=alert.status,
        created_at=alert.created_at,
    )


def bulk_update_alert_status(
    db: Session,
    alert_ids: list[int],
    status: AlertStatus
) -> list[AlertResponse]:
    """Bulk update alert statuses."""
    alerts = db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
    updated = []
    
    for alert in alerts:
        alert.status = status
        alert.updated_at = datetime.utcnow()
        updated.append(AlertResponse(
            id=alert.id,
            title=alert.title,
            severity=alert.severity,
            source=alert.source,
            description=alert.description,
            status=alert.status,
            created_at=alert.created_at,
        ))
    
    db.commit()
    
    # Elasticsearch dual-write
    if settings.elasticsearch_enabled:
        try:
            client = get_es_client()
            if client:
                for alert in alerts:
                    client.update(
                        index="soc-alerts",
                        id=alert.id,
                        doc={"status": status.value if hasattr(status, 'value') else status}
                    )
        except Exception as e:
            logger.warning(f"Failed to bulk update alerts in Elasticsearch: {e}")
            
    return updated


def get_alerts_count(
    db: Session,
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
) -> int:
    """Get total count of alerts matching filters."""
    query = db.query(func.count(Alert.id))
    
    if severity:
        query = query.filter(Alert.severity == severity)
    if status:
        query = query.filter(Alert.status == status)
    if source:
        query = query.filter(Alert.source.ilike(f"%{source}%"))
    
    return query.scalar()
