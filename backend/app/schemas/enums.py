"""Enums for validation across the application."""

from enum import Enum


class LogSeverity(str, Enum):
    """Log severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status values."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IncidentStatus(str, Enum):
    """Incident status values."""
    OPEN = "open"
    IN_PROGRESS = "in-progress"
    CLOSED = "closed"


class UserRole(str, Enum):
    """User role values."""
    ANALYST = "analyst"
    ADMIN = "admin"
