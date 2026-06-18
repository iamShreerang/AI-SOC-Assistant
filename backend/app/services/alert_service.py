"""Alert service — in-memory stub until DB layer is ready."""

from datetime import datetime, timezone
from typing import Optional

from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate

_store: dict[int, AlertResponse] = {}
_counter = 0


def create_alert(payload: AlertCreate) -> AlertResponse:
    global _counter
    _counter += 1
    entry = AlertResponse(
        **payload.model_dump(),
        id=_counter,
        status="open",
        created_at=datetime.now(timezone.utc),
    )
    _store[_counter] = entry
    return entry


def get_alerts(limit: int = 100) -> list[AlertResponse]:
    return list(_store.values())[-limit:]


def get_alert_by_id(alert_id: int) -> Optional[AlertResponse]:
    return _store.get(alert_id)


def update_alert_status(alert_id: int, payload: AlertUpdate) -> Optional[AlertResponse]:
    alert = _store.get(alert_id)
    if alert is None:
        return None
    _store[alert_id] = alert.model_copy(update={"status": payload.status})
    return _store[alert_id]
