"""Audit log endpoints for tracking administrative actions."""

from fastapi import APIRouter, Depends
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.db_audit_service import AuditLogEntry, get_audit_logs, get_audit_logs_count
from app.database import get_db
from app.utils.security import require_role

router = APIRouter()


class AuditLogListResponse(BaseModel):
    """Paginated audit log response."""
    logs: List[AuditLogEntry]
    total: int
    skip: int
    limit: int


@router.get(
    "/",
    response_model=AuditLogListResponse,
    summary="Get audit logs (admin only)",
    description="Retrieve audit logs with optional filtering by username, action, or resource type.",
)
async def get_audit_trail(
    limit: int = 100,
    skip: int = 0,
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """Get audit logs with filtering."""
    logs = get_audit_logs(
        db,
        limit=limit,
        skip=skip,
        username=username,
        action=action,
        resource_type=resource_type,
    )
    total = get_audit_logs_count(db, username=username, action=action, resource_type=resource_type)
    
    return AuditLogListResponse(logs=logs, total=total, skip=skip, limit=limit)
