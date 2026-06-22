"""Export service for data export in various formats."""

import csv
import json
from io import StringIO
from typing import List
from app.schemas.log import LogResponse
from app.schemas.alert import AlertResponse
from app.schemas.incident import IncidentResponse


def export_logs_csv(logs: List[LogResponse]) -> str:
    """Export logs to CSV format."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Source", "Severity", "Message", "Timestamp", "Ingested At"])
    
    # Data
    for log in logs:
        writer.writerow([
            log.id,
            log.source,
            log.severity.value,
            log.message,
            log.timestamp.isoformat() if log.timestamp else "",
            log.ingested_at.isoformat(),
        ])
    
    return output.getvalue()


def export_alerts_csv(alerts: List[AlertResponse]) -> str:
    """Export alerts to CSV format."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Title", "Severity", "Status", "Source", "Description", "Created At"])
    
    # Data
    for alert in alerts:
        writer.writerow([
            alert.id,
            alert.title,
            alert.severity.value,
            alert.status.value,
            alert.source,
            alert.description or "",
            alert.created_at.isoformat(),
        ])
    
    return output.getvalue()


def export_incidents_csv(incidents: List[IncidentResponse]) -> str:
    """Export incidents to CSV format."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "Title", "Status", "Description", "Alert IDs", "Summary", "Created At"])
    
    # Data
    for incident in incidents:
        writer.writerow([
            incident.id,
            incident.title,
            incident.status.value,
            incident.description or "",
            ",".join(map(str, incident.alert_ids)),
            incident.summary or "",
            incident.created_at.isoformat(),
        ])
    
    return output.getvalue()


def export_logs_json(logs: List[LogResponse]) -> str:
    """Export logs to JSON format."""
    return json.dumps([log.model_dump(mode="json") for log in logs], indent=2, default=str)


def export_alerts_json(alerts: List[AlertResponse]) -> str:
    """Export alerts to JSON format."""
    return json.dumps([alert.model_dump(mode="json") for alert in alerts], indent=2, default=str)


def export_incidents_json(incidents: List[IncidentResponse]) -> str:
    """Export incidents to JSON format."""
    return json.dumps([incident.model_dump(mode="json") for incident in incidents], indent=2, default=str)
