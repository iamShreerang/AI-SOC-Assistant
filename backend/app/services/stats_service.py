"""Statistics and analytics service."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List
from app.services import log_service, alert_service, incident_service


def get_dashboard_summary() -> Dict:
    """Get high-level summary statistics for dashboard."""
    all_logs = log_service.get_logs(limit=10000)
    all_alerts = alert_service.get_alerts(limit=10000)
    all_incidents = incident_service.get_incidents(limit=10000)
    
    # Alert breakdown by severity
    alert_severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for alert in all_alerts:
        alert_severity_counts[alert.severity.value] += 1
    
    # Alert breakdown by status
    alert_status_counts = {"open": 0, "acknowledged": 0, "resolved": 0}
    for alert in all_alerts:
        alert_status_counts[alert.status.value] += 1
    
    # Incident breakdown by status
    incident_status_counts = {"open": 0, "in-progress": 0, "closed": 0}
    for incident in all_incidents:
        incident_status_counts[incident.status.value] += 1
    
    # Log breakdown by severity
    log_severity_counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
    for log in all_logs:
        log_severity_counts[log.severity.value] += 1
    
    return {
        "total_logs": len(all_logs),
        "total_alerts": len(all_alerts),
        "total_incidents": len(all_incidents),
        "open_alerts": alert_status_counts["open"],
        "open_incidents": incident_status_counts["open"],
        "critical_alerts": alert_severity_counts["critical"],
        "alerts_by_severity": alert_severity_counts,
        "alerts_by_status": alert_status_counts,
        "incidents_by_status": incident_status_counts,
        "logs_by_severity": log_severity_counts,
    }


def get_recent_activity(hours: int = 24) -> Dict:
    """Get activity statistics for the last N hours."""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    all_logs = log_service.get_logs(limit=10000)
    all_alerts = alert_service.get_alerts(limit=10000)
    all_incidents = incident_service.get_incidents(limit=10000)
    
    # Count recent items
    recent_logs = [log for log in all_logs if log.ingested_at >= cutoff_time]
    recent_alerts = [alert for alert in all_alerts if alert.created_at >= cutoff_time]
    recent_incidents = [incident for incident in all_incidents if incident.created_at >= cutoff_time]
    
    return {
        "time_window_hours": hours,
        "logs_count": len(recent_logs),
        "alerts_count": len(recent_alerts),
        "incidents_count": len(recent_incidents),
        "critical_alerts_count": len([a for a in recent_alerts if a.severity.value == "critical"]),
    }


def get_alert_trends() -> Dict:
    """Get alert trends and patterns."""
    all_alerts = alert_service.get_alerts(limit=10000)
    
    # Top sources
    source_counts = {}
    for alert in all_alerts:
        source_counts[alert.source] = source_counts.get(alert.source, 0) + 1
    
    top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Resolution rate
    total = len(all_alerts)
    resolved = len([a for a in all_alerts if a.status.value == "resolved"])
    resolution_rate = (resolved / total * 100) if total > 0 else 0
    
    return {
        "total_alerts": total,
        "resolved_alerts": resolved,
        "resolution_rate_percent": round(resolution_rate, 2),
        "top_sources": [{"source": s, "count": c} for s, c in top_sources],
    }


def get_log_sources() -> List[Dict]:
    """Get breakdown of log sources."""
    all_logs = log_service.get_logs(limit=10000)
    
    source_counts = {}
    for log in all_logs:
        source_counts[log.source] = source_counts.get(log.source, 0) + 1
    
    return [
        {"source": source, "count": count}
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
    ]
