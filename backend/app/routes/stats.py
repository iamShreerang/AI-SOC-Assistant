"""Statistics and analytics endpoints."""

from fastapi import APIRouter, Depends
from typing import Dict, List
from app.services import stats_service
from app.utils.security import get_current_active_user

router = APIRouter()


@router.get(
    "/summary",
    response_model=Dict,
    summary="Get dashboard summary statistics",
    description="Returns high-level summary statistics including total counts and breakdowns by severity/status.",
)
async def get_summary(_user=Depends(get_current_active_user)):
    """Get dashboard summary with all key metrics."""
    return stats_service.get_dashboard_summary()


@router.get(
    "/activity",
    response_model=Dict,
    summary="Get recent activity statistics",
    description="Returns activity statistics for the last N hours (default: 24).",
)
async def get_activity(hours: int = 24, _user=Depends(get_current_active_user)):
    """Get recent activity for specified time window."""
    return stats_service.get_recent_activity(hours=hours)


@router.get(
    "/alerts/trends",
    response_model=Dict,
    summary="Get alert trends and patterns",
    description="Returns alert trends including top sources, resolution rate, and patterns.",
)
async def get_alert_trends(_user=Depends(get_current_active_user)):
    """Get alert trends and analytics."""
    return stats_service.get_alert_trends()


@router.get(
    "/logs/sources",
    response_model=List[Dict],
    summary="Get log source breakdown",
    description="Returns breakdown of logs by source with counts.",
)
async def get_log_sources(_user=Depends(get_current_active_user)):
    """Get breakdown of log sources."""
    return stats_service.get_log_sources()
