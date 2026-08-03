"""Search endpoints for full-text search."""

from fastapi import APIRouter, Depends, Query
from typing import List, Dict
from sqlalchemy.orm import Session

from app.schemas.log import LogResponse
from app.schemas.alert import AlertResponse
from app.schemas.incident import IncidentResponse
from app.services import search_service
from app.database import get_db
from app.utils.security import get_current_active_user

router = APIRouter()


@router.get(
    "/logs",
    response_model=List[LogResponse],
    summary="Search logs",
    description="Full-text search across log messages, raw content, and source.",
)
async def search_logs(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(50, description="Maximum results to return"),
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Search logs by query string."""
    return search_service.search_logs(q, limit=limit, db=db)


@router.get(
    "/alerts",
    response_model=List[AlertResponse],
    summary="Search alerts",
    description="Full-text search across alert titles, descriptions, and source.",
)
async def search_alerts(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(50, description="Maximum results to return"),
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Search alerts by query string."""
    return search_service.search_alerts(q, limit=limit, db=db)


@router.get(
    "/incidents",
    response_model=List[IncidentResponse],
    summary="Search incidents",
    description="Full-text search across incident titles, descriptions, and summaries.",
)
async def search_incidents(
    q: str = Query(..., description="Search query", min_length=1),
    limit: int = Query(50, description="Maximum results to return"),
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Search incidents by query string."""
    return search_service.search_incidents(q, limit=limit, db=db)


@router.get(
    "",
    response_model=Dict,
    summary="Global search root",
    description="Search across all entities (logs, alerts, incidents) at once.",
)
@router.get(
    "/",
    response_model=Dict,
    summary="Global search root trailing slash",
    description="Search across all entities (logs, alerts, incidents) at once.",
)
@router.get(
    "/all",
    response_model=Dict,
    summary="Global search",
    description="Search across all entities (logs, alerts, incidents) at once.",
)
async def global_search(
    q: str = Query(..., description="Search query", min_length=1),
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
):
    """Search across all entities."""
    return search_service.global_search(q, db=db)
