from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LogCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Firewall block event",
                    "value": {
                        "source": "firewall-01",
                        "severity": "high",
                        "message": "Inbound connection blocked from 198.51.100.42:4444",
                        "timestamp": "2024-06-01T14:32:00Z",
                        "raw": "Jun  1 14:32:00 fw01 kernel: DROP IN=eth0 SRC=198.51.100.42 DST=10.0.0.5 DPT=4444",
                    },
                },
                {
                    "summary": "Minimal log (Kafka consumer)",
                    "value": {
                        "source": "kafka-consumer",
                        "severity": "info",
                        "message": "User login from 10.0.0.12",
                    },
                },
            ]
        }
    )

    source: str = Field(..., description="Originating system (e.g. `firewall-01`, `ids`, `siem`)")
    severity: str = Field(..., description="Log severity: `info` | `warning` | `error` | `critical`")
    message: str = Field(..., description="Human-readable log message")
    timestamp: Optional[datetime] = Field(None, description="Event time (ISO 8601). Defaults to ingestion time if omitted")
    raw: Optional[str] = Field(None, description="Original unparsed log line")


class LogResponse(LogCreate):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "source": "firewall-01",
                    "severity": "high",
                    "message": "Inbound connection blocked from 198.51.100.42:4444",
                    "timestamp": "2024-06-01T14:32:00Z",
                    "raw": "Jun  1 14:32:00 fw01 kernel: DROP IN=eth0 SRC=198.51.100.42",
                    "ingested_at": "2024-06-01T14:32:01.123Z",
                }
            ]
        }
    )

    id: int = Field(..., description="Auto-assigned log ID")
    ingested_at: datetime = Field(..., description="UTC timestamp when the backend received this log")
