"""Internal pipeline ingest endpoints: heartbeat and metrics."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database import ServiceHeartbeat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest")


class HeartbeatPayload(BaseModel):
    service: str
    status: str = "running"
    timestamp: str = ""


class MetricsPayload(BaseModel):
    total_requests: int = 0
    attack_count: int = 0
    normal_count: int = 0
    requests_per_second: float = 0.0
    requests_per_minute: float = 0.0
    avg_inference_latency_ms: float = 0.0
    unique_src_ips: int = 0
    unique_dst_ips: int = 0
    suspicious_ip_count: int = 0
    total_bytes_transferred: int = 0
    avg_packet_size: float = 0.0
    alerts_critical: int = 0
    alerts_high: int = 0
    alerts_medium: int = 0
    alerts_low: int = 0


@router.post("/heartbeat", status_code=200)
async def receive_heartbeat(
    payload: HeartbeatPayload,
    db: Session = Depends(get_db),
):
    """
    Called by the Spark streaming job to signal it is alive.
    Upserts the last_seen timestamp for the given service.
    """
    try:
        hb = db.query(ServiceHeartbeat).filter(
            ServiceHeartbeat.service == payload.service
        ).first()
        if hb:
            hb.last_seen = datetime.utcnow()
            hb.status = payload.status
        else:
            hb = ServiceHeartbeat(
                service=payload.service,
                status=payload.status,
                last_seen=datetime.utcnow(),
            )
            db.add(hb)
        db.commit()
        logger.debug("Heartbeat received from service '%s'", payload.service)
        return {"detail": "ok"}
    except Exception as e:
        logger.error("Failed to persist heartbeat for '%s': %s", payload.service, e)
        db.rollback()
        return {"detail": "error", "message": str(e)}


@router.post("/metrics", status_code=200)
async def receive_metrics(payload: MetricsPayload):
    """
    Called by the Spark streaming job to publish pipeline metrics.
    Currently logged only; extend to persist in a time-series table if needed.
    """
    logger.info(
        "Pipeline metrics | total=%d attacks=%d normal=%d rps=%.1f latency=%.2fms",
        payload.total_requests,
        payload.attack_count,
        payload.normal_count,
        payload.requests_per_second,
        payload.avg_inference_latency_ms,
    )
    return {"detail": "ok"}
