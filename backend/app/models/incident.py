"""Pydantic models for incidents."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class Incident(BaseModel):
    title: str
    description: Optional[str] = None
    alert_ids: List[int] = []


class IncidentResponse(Incident):
    id: int
    status: str
    summary: Optional[str] = None
    created_at: datetime
