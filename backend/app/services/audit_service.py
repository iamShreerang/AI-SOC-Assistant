"""Audit logging service for tracking administrative actions."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: int
    timestamp: datetime
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]


# In-memory audit log storage
_audit_log: List[AuditLogEntry] = []
_counter = 0


def log_action(
    username: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLogEntry:
    """Log an administrative action."""
    global _counter
    _counter += 1
    
    entry = AuditLogEntry(
        id=_counter,
        timestamp=datetime.now(timezone.utc),
        username=username,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    
    _audit_log.append(entry)
    return entry


def get_audit_logs(
    limit: int = 100,
    skip: int = 0,
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> List[AuditLogEntry]:
    """Get audit logs with optional filtering."""
    logs = _audit_log.copy()
    
    # Apply filters
    if username:
        logs = [log for log in logs if log.username == username]
    if action:
        logs = [log for log in logs if action.lower() in log.action.lower()]
    if resource_type:
        logs = [log for log in logs if log.resource_type == resource_type]
    
    # Sort by timestamp descending (newest first)
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply pagination
    return logs[skip : skip + limit]


def get_audit_logs_count(
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> int:
    """Get total count of audit logs matching filters."""
    logs = _audit_log.copy()
    
    if username:
        logs = [log for log in logs if log.username == username]
    if action:
        logs = [log for log in logs if action.lower() in log.action.lower()]
    if resource_type:
        logs = [log for log in logs if log.resource_type == resource_type]
    
    return len(logs)
