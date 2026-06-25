"""Pydantic models for alerts."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Alert(BaseModel):
    """Represents a detected security alert."""

    title: str
    severity: str           # low | medium | high | critical
    source: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class AlertResponse(Alert):
    """Alert as returned by the API."""

    id: int
    status: str             # open | acknowledged | resolved
