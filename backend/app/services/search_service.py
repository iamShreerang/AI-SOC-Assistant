"""Search service for full-text search across entities.

Priority:
  1. Elasticsearch (if ELASTICSEARCH_ENABLED=true and responsive)
  2. PostgreSQL ilike fallback (always available)
"""

from typing import List, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String

from app.schemas.log import LogResponse
from app.schemas.alert import AlertResponse
from app.schemas.incident import IncidentResponse
from app.models.database import Log, Alert, Incident, IncidentAlert
from app.utils.config import settings

logger = logging.getLogger(__name__)

# ── PostgreSQL ilike fallback ──────────────────────────────────────────────

def search_logs_db(query: str, limit: int = 50, db: Optional[Session] = None) -> List[LogResponse]:
    """Full-text search logs via PostgreSQL ILIKE."""
    if db is None:
        return []
    pattern = f"%{query}%"
    logs = (
        db.query(Log)
        .filter(
            or_(
                cast(Log.id, String).ilike(pattern),
                Log.message.ilike(pattern),
                Log.source.ilike(pattern),
                Log.raw.ilike(pattern),
            )
        )
        .order_by(Log.ingested_at.desc())
        .limit(limit)
        .all()
    )
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


def search_alerts_db(query: str, limit: int = 50, db: Optional[Session] = None) -> List[AlertResponse]:
    """Full-text search alerts via PostgreSQL ILIKE."""
    if db is None:
        return []
    pattern = f"%{query}%"
    alerts = (
        db.query(Alert)
        .filter(
            or_(
                cast(Alert.id, String).ilike(pattern),
                Alert.title.ilike(pattern),
                Alert.description.ilike(pattern),
                Alert.source.ilike(pattern),
            )
        )
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .all()
    )
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


def search_incidents_db(query: str, limit: int = 50, db: Optional[Session] = None) -> List[IncidentResponse]:
    """Full-text search incidents via PostgreSQL ILIKE."""
    if db is None:
        return []
    pattern = f"%{query}%"
    incidents = (
        db.query(Incident)
        .filter(
            or_(
                cast(Incident.id, String).ilike(pattern),
                Incident.title.ilike(pattern),
                Incident.description.ilike(pattern),
                Incident.summary.ilike(pattern),
            )
        )
        .order_by(Incident.created_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for incident in incidents:
        alert_ids = [
            ia.alert_id
            for ia in db.query(IncidentAlert)
            .filter(IncidentAlert.incident_id == incident.id)
            .all()
        ]
        results.append(
            IncidentResponse(
                id=incident.id,
                title=incident.title,
                description=incident.description,
                alert_ids=alert_ids,
                status=incident.status,
                summary=incident.summary,
                created_at=incident.created_at,
            )
        )
    return results


# ── Active Search Interface with Fallback ──────────────────────────────────

def search_logs(query: str, limit: int = 50, db: Optional[Session] = None) -> List[LogResponse]:
    """Search logs with Elasticsearch, falling back to PostgreSQL if unavailable or empty."""
    if settings.elasticsearch_enabled:
        try:
            from app.utils.elasticsearch_client import check_es_connection
            if check_es_connection():
                from app.services import es_log_service
                results = es_log_service.search_logs_direct(query, limit)
                if results:
                    return results
        except Exception as e:
            logger.warning(f"Elasticsearch log search failed, falling back to SQL: {e}")
            
    return search_logs_db(query, limit, db)


def search_alerts(query: str, limit: int = 50, db: Optional[Session] = None) -> List[AlertResponse]:
    """Search alerts with Elasticsearch, falling back to PostgreSQL if unavailable or empty."""
    if settings.elasticsearch_enabled:
        try:
            from app.utils.elasticsearch_client import check_es_connection
            if check_es_connection():
                from app.services import es_alert_service
                results = es_alert_service.search_alerts_direct(query, limit)
                if results:
                    return results
        except Exception as e:
            logger.warning(f"Elasticsearch alert search failed, falling back to SQL: {e}")
            
    return search_alerts_db(query, limit, db)


def search_incidents(query: str, limit: int = 50, db: Optional[Session] = None) -> List[IncidentResponse]:
    """Search incidents with Elasticsearch, falling back to PostgreSQL if unavailable or empty."""
    if settings.elasticsearch_enabled:
        try:
            from app.utils.elasticsearch_client import check_es_connection
            if check_es_connection():
                from app.services import es_incident_service
                results = es_incident_service.search_incidents_direct(query, limit)
                if results:
                    return results
        except Exception as e:
            logger.warning(f"Elasticsearch incident search failed, falling back to SQL: {e}")
            
    return search_incidents_db(query, limit, db)


def global_search(query: str, db: Optional[Session] = None) -> dict:
    """Search across all entities."""
    return {
        "query": query,
        "logs": search_logs(query, limit=10, db=db),
        "alerts": search_alerts(query, limit=10, db=db),
        "incidents": search_incidents(query, limit=10, db=db),
    }
