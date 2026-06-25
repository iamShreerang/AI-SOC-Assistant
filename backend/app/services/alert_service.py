"""Alert service — in-memory stub until DB layer is ready."""

from datetime import datetime, timezone
from typing import Optional

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.schemas.enums import AlertSeverity, AlertStatus

_store: dict[int, AlertResponse] = {}
_counter = 0


def create_alert(payload: AlertCreate) -> AlertResponse:
    global _counter
    _counter += 1
    entry = AlertResponse(
        **payload.model_dump(),
        id=_counter,
        status=AlertStatus.OPEN,
        created_at=datetime.now(timezone.utc),
    )
    _store[_counter] = entry
    return entry


def get_alerts(
    limit: int = 100,
    skip: int = 0,
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
) -> list[AlertResponse]:
    """Get alerts with optional filtering."""
    alerts = list(_store.values())
    
    # Apply filters
    if severity:
        alerts = [alert for alert in alerts if alert.severity == severity]
    if status:
        alerts = [alert for alert in alerts if alert.status == status]
    if source:
        alerts = [alert for alert in alerts if source.lower() in alert.source.lower()]
    
    # Apply pagination
    return alerts[skip : skip + limit]


def get_alert_by_id(alert_id: int) -> Optional[AlertResponse]:
    return _store.get(alert_id)


def update_alert_status(alert_id: int, payload: AlertUpdate) -> Optional[AlertResponse]:
    alert = _store.get(alert_id)
    if alert is None:
        return None
    _store[alert_id] = alert.model_copy(update={"status": payload.status})
    return _store[alert_id]


def bulk_update_alert_status(alert_ids: list[int], status: AlertStatus) -> list[AlertResponse]:
    """Bulk update alert statuses."""
    updated = []
    for alert_id in alert_ids:
        alert = _store.get(alert_id)
        if alert:
            _store[alert_id] = alert.model_copy(update={"status": status})
            updated.append(_store[alert_id])
    return updated


def get_alerts_count(
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    source: Optional[str] = None,
) -> int:
    """Get total count of alerts matching filters."""
    alerts = list(_store.values())
    
    if severity:
        alerts = [alert for alert in alerts if alert.severity == severity]
    if status:
        alerts = [alert for alert in alerts if alert.status == status]
    if source:
        alerts = [alert for alert in alerts if source.lower() in alert.source.lower()]
    
    return len(alerts)
