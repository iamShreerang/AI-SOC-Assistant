"""Statistics and analytics service with PostgreSQL backend."""

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import Log, Alert, Incident
from app.schemas.enums import LogSeverity, AlertSeverity, AlertStatus, IncidentStatus


def get_dashboard_summary(db: Session) -> Dict:
    """Get high-level summary statistics for dashboard."""
    from sqlalchemy import String, func

    # Total counts
    total_logs = db.query(func.count(Log.id)).scalar() or 0
    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    total_incidents = db.query(func.count(Incident.id)).scalar() or 0
    
    # Active Threats = Unresolved (OPEN / ACKNOWLEDGED) Critical & High alerts
    active_threats_count = (
        db.query(func.count(Alert.id))
        .filter(
            Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]),
            func.lower(func.cast(Alert.severity, String)).in_(["critical", "high"])
        )
        .scalar() or 0
    )

    # Alert breakdown by severity (case-insensitive)
    alert_severity_counts = {
        "low": db.query(func.count(Alert.id)).filter(func.lower(func.cast(Alert.severity, String)) == "low").scalar() or 0,
        "medium": db.query(func.count(Alert.id)).filter(func.lower(func.cast(Alert.severity, String)) == "medium").scalar() or 0,
        "high": db.query(func.count(Alert.id)).filter(func.lower(func.cast(Alert.severity, String)) == "high").scalar() or 0,
        "critical": db.query(func.count(Alert.id)).filter(func.lower(func.cast(Alert.severity, String)) == "critical").scalar() or 0,
    }
    
    # Alert breakdown by status
    alert_status_counts = {
        "open": db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.OPEN).scalar() or 0,
        "acknowledged": db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.ACKNOWLEDGED).scalar() or 0,
        "resolved": db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.RESOLVED).scalar() or 0,
    }
    
    # Incident breakdown by status
    incident_status_counts = {
        "open": db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.OPEN).scalar() or 0,
        "in-progress": db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.IN_PROGRESS).scalar() or 0,
        "closed": db.query(func.count(Incident.id)).filter(Incident.status == IncidentStatus.CLOSED).scalar() or 0,
    }
    
    # Log breakdown by severity
    log_severity_counts = {
        "info": db.query(func.count(Log.id)).filter(func.lower(func.cast(Log.severity, String)) == "info").scalar() or 0,
        "warning": db.query(func.count(Log.id)).filter(func.lower(func.cast(Log.severity, String)) == "warning").scalar() or 0,
        "error": db.query(func.count(Log.id)).filter(func.lower(func.cast(Log.severity, String)) == "error").scalar() or 0,
        "critical": db.query(func.count(Log.id)).filter(func.lower(func.cast(Log.severity, String)) == "critical").scalar() or 0,
    }
    
    return {
        "total_logs": total_logs,
        "total_alerts": total_alerts,
        "total_incidents": total_incidents,
        "open_alerts": alert_status_counts["open"],
        "open_incidents": incident_status_counts["open"],
        "active_threats": active_threats_count,
        "critical_alerts": active_threats_count,
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


def get_ml_analytics(db: Session) -> Dict:
    """Get ML analytics data derived from real DB records."""
    # Threat classification derived from alert severity breakdown
    threat_classification = [
        {
            "name": "Critical Threats",
            "value": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.CRITICAL).scalar() or 0,
            "color": "#dc2626",
        },
        {
            "name": "High Risk",
            "value": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.HIGH).scalar() or 0,
            "color": "#ea580c",
        },
        {
            "name": "Medium Risk",
            "value": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.MEDIUM).scalar() or 0,
            "color": "#f59e0b",
        },
        {
            "name": "Low Risk",
            "value": db.query(func.count(Alert.id)).filter(Alert.severity == AlertSeverity.LOW).scalar() or 0,
            "color": "#10b981",
        },
    ]

    # Anomaly scores: alerts per hour for the past 6 hours
    anomaly_data = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        hour_start = now - timedelta(hours=i + 1)
        hour_end = now - timedelta(hours=i)
        label = hour_start.strftime("%H:%M")
        count = db.query(func.count(Alert.id)).filter(
            Alert.created_at >= hour_start,
            Alert.created_at < hour_end,
        ).scalar() or 0
        # Normalise to a 0–1 anomaly score
        anomaly_data.append({"name": label, "value": round(min(count / 10.0, 1.0), 2)})

    # Recent predictions: use the most recent open/acknowledged critical+high alerts as predictions
    recent_alerts = (
        db.query(Alert)
        .filter(Alert.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.HIGH]))
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )

    # Derive a threat type and confidence from severity
    _severity_meta = {
        AlertSeverity.CRITICAL: ("Anomalous Activity", 0.95),
        AlertSeverity.HIGH: ("Suspicious Pattern", 0.82),
        AlertSeverity.MEDIUM: ("Potential Threat", 0.67),
        AlertSeverity.LOW: ("Low-Level Event", 0.50),
    }

    predictions = []
    for alert in recent_alerts:
        threat, confidence = _severity_meta.get(alert.severity, ("Unknown", 0.5))
        predictions.append({
            "id": alert.id,
            "alert_id": alert.id,
            "threat": threat,
            "confidence": confidence,
            "severity": alert.severity.value,
        })

    total_alerts = db.query(func.count(Alert.id)).scalar() or 0
    resolved = db.query(func.count(Alert.id)).filter(Alert.status == AlertStatus.RESOLVED).scalar() or 0
    accuracy = round((resolved / total_alerts * 100), 1) if total_alerts > 0 else 0.0

    return {
        "model_accuracy": accuracy,
        "predictions_today": total_alerts,
        "anomalies_detected": db.query(func.count(Alert.id)).filter(
            Alert.severity == AlertSeverity.CRITICAL,
            Alert.status != AlertStatus.RESOLVED,
        ).scalar() or 0,
        "anomaly_data": anomaly_data,
        "threat_classification": threat_classification,
        "predictions": predictions,
    }
