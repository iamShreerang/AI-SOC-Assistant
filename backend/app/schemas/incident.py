from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.enums import IncidentStatus


class IncidentCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Ransomware incident",
                    "value": {
                        "title": "Ransomware Outbreak — Host cluster A",
                        "description": "Three hosts encrypted within 10 minutes; lateral movement detected",
                        "alert_ids": [12, 13, 15],
                    },
                },
                {
                    "summary": "Minimal incident",
                    "value": {"title": "Suspicious login from unknown country"},
                },
            ]
        }
    )

    title: str = Field(..., description="Short incident title")
    description: Optional[str] = Field(None, description="Detailed description of what happened")
    alert_ids: List[int] = Field([], description="IDs of alerts linked to this incident")


class IncidentResponse(IncidentCreate):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 3,
                    "title": "Ransomware Outbreak — Host cluster A",
                    "description": "Three hosts encrypted within 10 minutes; lateral movement detected",
                    "alert_ids": [12, 13, 15],
                    "status": "open",
                    "summary": "Attacker gained initial access via phishing email, deployed Lockbit 3.0 ransomware across three hosts in cluster A. Lateral movement used SMB relay. Recommend immediate network isolation.",
                    "created_at": "2024-06-01T15:00:00Z",
                }
            ]
        }
    )

    id: int = Field(..., description="Auto-assigned incident ID")
    status: IncidentStatus = Field(..., description="Incident status: `open` | `in-progress` | `closed`")
    summary: Optional[str] = Field(None, description="AI-generated narrative summary (populated by LLM module via `POST /summaries`)")
    created_at: datetime = Field(..., description="UTC timestamp when the incident was opened")


class LLMSummary(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "LLM summary payload",
                    "value": {
                        "incident_id": 3,
                        "summary": "Attacker gained initial access via phishing email, deployed Lockbit 3.0 ransomware across three hosts in cluster A. Lateral movement used SMB relay. Recommend immediate network isolation.",
                    },
                }
            ]
        }
    )

    incident_id: int = Field(..., description="ID of the incident to attach this summary to")
    summary: str = Field(..., description="LLM-generated narrative summary of the incident")


class IncidentStatusUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"summary": "Mark in progress", "value": {"status": "in-progress"}},
                {"summary": "Close incident", "value": {"status": "closed"}},
            ]
        }
    )

    status: IncidentStatus = Field(..., description="New incident status: `open` | `in-progress` | `closed`")
