"""Alert management endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_alerts():
    """
    Retrieve active security alerts.

    TODO:
        - Filter by severity, status, time range
        - Paginate results
        - Pull from PostgreSQL alerts table
    """
    pass


@router.patch("/{alert_id}")
async def update_alert(alert_id: int):
    """
    Update alert status (acknowledge, resolve, escalate).

    Args:
        alert_id: Primary key of the alert to update

    TODO:
        - Validate status transition
        - Write audit log entry
    """
    pass
