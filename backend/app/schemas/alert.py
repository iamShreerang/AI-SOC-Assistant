from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Brute-force alert (manual)",
                    "value": {
                        "title": "SSH Brute Force Detected",
                        "severity": "high",
                        "source": "auth-service",
                        "description": "15 failed login attempts from 198.51.100.42 in 60 seconds",
                    },
                },
                {
                    "summary": "ML anomaly alert (from /ingest/alerts)",
                    "value": {
                        "title": "Anomalous outbound traffic spike",
                        "severity": "critical",
                        "source": "ml-anomaly-detector",
                        "description": "Outbound bytes exceeded 3σ threshold on interface eth0",
                    },
                },
            ]
        }
    )

    title: str = Field(..., description="Short alert title")
    severity: str = Field(..., description="Alert severity: `low` | `medium` | `high` | `critical`")
    source: str = Field(..., description="Component that raised this alert (e.g. `waf`, `ids`, `ml-anomaly-detector`)")
    description: Optional[str] = Field(None, description="Extended description of the alert condition")


class AlertUpdate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"summary": "Acknowledge", "value": {"status": "acknowledged"}},
                {"summary": "Resolve", "value": {"status": "resolved"}},
            ]
        }
    )

    status: str = Field(..., description="New status: `open` | `acknowledged` | `resolved`")


class AlertResponse(AlertCreate):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 7,
                    "title": "SSH Brute Force Detected",
                    "severity": "high",
                    "source": "auth-service",
                    "description": "15 failed login attempts from 198.51.100.42 in 60 seconds",
                    "status": "open",
                    "created_at": "2024-06-01T14:35:00Z",
                }
            ]
        }
    )

    id: int = Field(..., description="Auto-assigned alert ID")
    status: str = Field(..., description="Current alert status: `open` | `acknowledged` | `resolved`")
    created_at: datetime = Field(..., description="UTC timestamp when the alert was created")
