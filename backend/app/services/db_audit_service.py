"""Audit logging service with PostgreSQL backend."""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import AuditLog


class AuditLogEntry:
    """Audit log entry model for API responses."""
    def __init__(self, id: int, timestamp: datetime, username: str, action: str,
                 resource_type: str, resource_id: Optional[str], details: Optional[str],
                 ip_address: Optional[str]):
        self.id = id
        self.timestamp = timestamp
        self.username = username
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = details
        self.ip_address = ip_address


def log_action(
    db: Session,
    username: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AuditLogEntry:
    """Log an administrative action to the database."""
    db_audit = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        timestamp=datetime.utcnow(),
    )
    db.add(db_audit)
    db.commit()
    db.refresh(db_audit)
    
    return AuditLogEntry(
        id=db_audit.id,
        timestamp=db_audit.timestamp,
        username=db_audit.username,
        action=db_audit.action,
        resource_type=db_audit.resource_type,
        resource_id=db_audit.resource_id,
        details=db_audit.details,
        ip_address=db_audit.ip_address,
    )


def get_audit_logs(
    db: Session,
    limit: int = 100,
    skip: int = 0,
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> list[AuditLogEntry]:
    """Get audit logs with optional filtering and pagination."""
    query = db.query(AuditLog)
    
    # Apply filters
    if username:
        query = query.filter(AuditLog.username == username)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    # Order by most recent first and apply pagination
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [
        AuditLogEntry(
            id=log.id,
            timestamp=log.timestamp,
            username=log.username,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
        )
        for log in logs
    ]


def get_audit_logs_count(
    db: Session,
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> int:
    """Get total count of audit logs matching filters."""
    query = db.query(func.count(AuditLog.id))
    
    if username:
        query = query.filter(AuditLog.username == username)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    return query.scalar()
