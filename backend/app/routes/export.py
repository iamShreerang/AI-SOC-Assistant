"""Export endpoints for data export in various formats."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from typing import Optional
from app.schemas.enums import LogSeverity, AlertSeverity, AlertStatus, IncidentStatus
from app.services import log_service, alert_service, incident_service, export_service
from app.utils.security import get_current_active_user

router = APIRouter()


@router.get(
    "/logs",
    summary="Export logs",
    description="Export logs in CSV or JSON format with optional filtering.",
)
async def export_logs(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format: csv or json"),
    severity: Optional[LogSeverity] = None,
    source: Optional[str] = None,
    limit: int = Query(1000, description="Maximum records to export"),
    _user=Depends(get_current_active_user),
):
    """Export logs with filtering."""
    logs = log_service.get_logs(limit=limit, severity=severity, source=source)
    
    if format == "csv":
        content = export_service.export_logs_csv(logs)
        media_type = "text/csv"
        filename = "logs.csv"
    else:
        content = export_service.export_logs_json(logs)
        media_type = "application/json"
        filename = "logs.json"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/alerts",
    summary="Export alerts",
    description="Export alerts in CSV or JSON format with optional filtering.",
)
async def export_alerts(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format: csv or json"),
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
    limit: int = Query(1000, description="Maximum records to export"),
    _user=Depends(get_current_active_user),
):
    """Export alerts with filtering."""
    alerts = alert_service.get_alerts(limit=limit, severity=severity, status=status, source=source)
    
    if format == "csv":
        content = export_service.export_alerts_csv(alerts)
        media_type = "text/csv"
        filename = "alerts.csv"
    else:
        content = export_service.export_alerts_json(alerts)
        media_type = "application/json"
        filename = "alerts.json"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/incidents",
    summary="Export incidents",
    description="Export incidents in CSV or JSON format with optional filtering.",
)
async def export_incidents(
    format: str = Query("csv", pattern="^(csv|json)$", description="Export format: csv or json"),
    status: Optional[IncidentStatus] = None,
    limit: int = Query(1000, description="Maximum records to export"),
    _user=Depends(get_current_active_user),
):
    """Export incidents with filtering."""
    incidents = incident_service.get_incidents(limit=limit, status=status)
    
    if format == "csv":
        content = export_service.export_incidents_csv(incidents)
        media_type = "text/csv"
        filename = "incidents.csv"
    else:
        content = export_service.export_incidents_json(incidents)
        media_type = "application/json"
        filename = "incidents.json"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
