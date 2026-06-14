"""Pydantic models for log entries."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LogEntry(BaseModel):
    """Represents a single inbound security log."""

    source: str
    severity: str           # info | warning | error | critical
    message: str
    timestamp: Optional[datetime] = None
    raw: Optional[str] = None  # original raw log string


class LogResponse(LogEntry):
    """Log entry as returned by the API (includes DB id)."""

    id: int
    ingested_at: datetime
