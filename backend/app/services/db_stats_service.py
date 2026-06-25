"""Statistics and analytics service with PostgreSQL backend."""

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import Log, Alert, Incident
from app.schemas.enums import LogSeverity, AlertSeverity, AlertStatus, IncidentStatus


def get_dashboard_summary(db: Session) -> Dict:
    """Get high-level summary statistics for dashboard."""
    # Total counts
    total_logs = db.query(func.count(Log.id)).scalar()
    total_alerts = db.query(func.count(Alert.id)).scalar()
    total_incidents = db.query(func.count(Incident.id)).scalar()
    
    # Alert breakdown by severity
    alert_severity_counts = {
        "low": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.LOW).scalar(),
        "medium": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.MEDIUM).scalar(),
        "high": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.HIGH).scalar(),
        "critical": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.CRITICAL).scalar(),
    }
    
    # Alert breakdown by status
    alert_status_counts = {
        "open": db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.OPEN).scalar(),
        "acknowledged": db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.ACKNOWLEDGED).scalar(),
        "resolved": db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.RESOLVED).scalar(),
    }
    
    # Incident breakdown by status
    incident_status_counts = {
        "open": db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.OPEN).scalar(),
        "in-progress": db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.IN_PROGRESS).scalar(),
        "closed": db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.CLOSED).scalar(),
    }
    
    # Log breakdown by severity
    log_severity_counts = {
        "info": db.query(func.count(Log.id)).filter(Log.severity == LogSeverity.INFO).scalar(),
        "warning": db.query(func.count(Log.id)).filter(Log.severity == LogSeverity.WARNING).scalar(),
        "error": db.query(func.count(Log.id)).filter(Log.severity == LogSeverity.ERROR).scalar(),
        "critical": db.query(func.count(Log.id)).filter(Log.severity == LogSeverity.CRITICAL).scalar(),
    }
    
    return {
        "total_logs": total_logs,
        "total_alerts": total_alerts,
        "total_incidents": total_incidents,
        "open_alerts": alert_status_counts["open"],
        "open_incidents": incident_status_counts["open"],
        "critical_alerts": alert_severity_counts["critical"],
        "alerts_by_severity": alert_severity_counts,
        "alerts_by_status": alert_status_counts,
        "incidents_by_status": incident_status_counts,
        "logs_by_severity": log_severity_counts,
    }


def get_recent_activity(db: Session, hours: int = 24) -> Dict:
    """Get activity statistics for the last N hours."""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Count recent items
    recent_logs = db.query(func.count(Log.id)).filter(Log.ingested_at >= cutoff_time).scalar()
    recent_alerts = db.query(func.count(Alert.id)).filter(Alert.created_at >= cutoff_time).scalar()
    recent_incidents = db.query(func.count(Incident.id)).filter(Incident.created_at >= cutoff_time).scalar()
    critical_alerts = db.query(func.count(Alert.id)).filter(
        Alert.created_at >= cutoff_time,
        Alert.severity == AlertSeverity.CRITICAL
    ).scalar()
    
    return {
        "time_window_hours": hours,
        "logs_count": recent_logs,
        "alerts_count": recent_alerts,
        "incidents_count": recent_incidents,
        "critical_alerts_count": critical_alerts,
    }


def get_alert_trends(db: Session) -> Dict:
    """Get alert trends and patterns."""
    total = db.query(func.count(Alert.id)).scalar()
    resolved = db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.RESOLVED).scalar()
    resolution_rate = (resolved / total * 100) if total > 0 else 0
    
    # Top sources - group by source and count
    top_sources_query = db.query(
        Alert.source,
        func.count(Alert.id).label('count')
    ).group_by(Alert.source).order_by(func.count(Alert.id).desc()).limit(5).all()
    
    top_sources = [{"source": source, "count": count} for source, count in top_sources_query]
    
    return {
        "total_alerts": total,
        "resolved_alerts": resolved,
        "resolution_rate_percent": round(resolution_rate, 2),
        "top_sources": top_sources,
    }


def get_log_sources(db: Session) -> List[Dict]:
    """Get breakdown of log sources."""
    sources_query = db.query(
        Log.source,
        func.count(Log.id).label('count')
    ).group_by(Log.source).order_by(func.count(Log.id).desc()).all()
    
    return [{"source": source, "count": count} for source, count in sources_query]
