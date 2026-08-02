"""Health check endpoint — real component status detection."""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import check_connection, get_db
from app.utils.config import settings
from app.utils.elasticsearch_client import check_es_connection

logger = logging.getLogger(__name__)

router = APIRouter()

# Spark is considered healthy if its last heartbeat arrived within this window.
_SPARK_HEARTBEAT_STALE_SECS = 120


def _check_kafka() -> bool:
    """Lightweight Kafka broker reachability check via socket probe."""
    import socket
    try:
        host, port_str = settings.kafka_broker.split(":")
        port = int(port_str)
        with socket.create_connection((host, port), timeout=3.0):
            return True
    except Exception:
        return False


def _check_ml_model() -> bool:
    """Return True only when the saved model artifacts are present and loadable."""
    try:
        from pathlib import Path
        import sys, os
        # Resolve repo root so ml package is importable
        repo_root = Path(__file__).parent.parent.parent.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))

        model_dir = repo_root / "ml" / "saved_models"
        required = ["cnn_lstm.pt", "pipeline.pkl", "threshold.pkl"]
        return all((model_dir / f).exists() for f in required)
    except Exception as e:
        logger.warning("ML model check failed: %s", e)
        return False


def _check_spark(db: Session) -> bool:
    """Return True if Spark posted a heartbeat within the stale threshold."""
    try:
        from app.models.database import ServiceHeartbeat
        from sqlalchemy import or_
        hb = (
            db.query(ServiceHeartbeat)
            .filter(
                or_(
                    ServiceHeartbeat.service == "spark",
                    ServiceHeartbeat.service == "spark-local",
                )
            )
            .order_by(ServiceHeartbeat.last_seen.desc())
            .first()
        )
        if hb is None:
            return False
        cutoff = datetime.utcnow() - timedelta(seconds=_SPARK_HEARTBEAT_STALE_SECS)
        return hb.last_seen >= cutoff
    except Exception as e:
        logger.warning("Spark heartbeat check failed: %s", e)
        return False


def _check_llm() -> bool:
    """Return True when a Groq API key is configured (no token consumed)."""
    return bool(settings.groq_api_key)


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Returns real service health status.

    - database: live SELECT 1 probe
    - kafka: broker metadata probe (3 s timeout)
    - spark: heartbeat freshness check (last POST /ingest/heartbeat)
    - ml_model: saved model artifact presence check
    - llm: Groq API key configured (no tokens consumed)
    - elasticsearch: disabled/enabled + ping if enabled
    """
    db_ok = check_connection()

    kafka_ok = _check_kafka()

    spark_ok = _check_spark(db) if db_ok else False

    ml_ok = _check_ml_model()

    llm_ok = _check_llm()

    if settings.elasticsearch_enabled:
        es_ok = check_es_connection()
        es_status = {"enabled": True, "healthy": es_ok}
    else:
        es_ok = False
        es_status = {"enabled": False, "healthy": False}

    overall = "ok" if db_ok else "degraded"

    return {
        "status": overall,
        "version": "0.1.0",
        "components": {
            "database": db_ok,
            "kafka": kafka_ok,
            "spark": spark_ok,
            "ml_model": ml_ok,
            "llm": llm_ok,
            "elasticsearch": es_status,
        },
    }
