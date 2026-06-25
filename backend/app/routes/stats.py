"""Statistics and analytics endpoints."""

from fastapi import APIRouter, Depends
from typing import Dict, List
from sqlalchemy.orm import Session

from app.services import db_stats_service
from app.database import get_db
from app.utils.security import get_current_active_user

router = APIRouter()


@router.get(
    "/summary",
    response_model=Dict,
    summary="Get dashboard summary statistics",
    description="Returns high-level summary statistics including total counts and breakdowns by severity/status.",
)
async def get_summary(db: Session = Depends(get_db), _user=Depends(get_current_active_user)):
    """Get dashboard summary with all key metrics."""
    return db_stats_service.get_dashboard_summary(db)


@router.get(
    "/activity",
    response_model=Dict,
    summary="Get recent activity statistics",
    description="Returns activity statistics for the last N hours (default: 24).",
)
async def get_activity(
    hours: int = 24,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user)
):
    """Get recent activity for specified time window."""
    return db_stats_service.get_recent_activity(db, hours=hours)


@router.get(
    "/alerts/trends",
    response_model=Dict,
    summary="Get alert trends and patterns",
    description="Returns alert trends including top sources, resolution rate, and patterns.",
)
async def get_alert_trends(db: Session = Depends(get_db), _user=Depends(get_current_active_user)):
    """Get alert trends and analytics."""
    return db_stats_service.get_alert_trends(db)


@router.get(
    "/logs/sources",
    response_model=List[Dict],
    summary="Get log source breakdown",
    description="Returns breakdown of logs by source with counts.",
)
async def get_log_sources(db: Session = Depends(get_db), _user=Depends(get_current_active_user)):
    """Get breakdown of log sources."""
    return db_stats_service.get_log_sources(db)
