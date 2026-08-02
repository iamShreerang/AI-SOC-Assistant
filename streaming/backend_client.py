"""
HTTP client for pushing streaming pipeline results into the FastAPI backend.

Talks to the no-auth internal "ingest" endpoints:
  POST /ingest/logs
  POST /ingest/alerts
  POST /ingest/metrics
  POST /ingest/heartbeat

All calls are best-effort: a backend outage must never crash the Spark job.
Failures are logged with enough detail to diagnose schema mismatches.
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from streaming.config import BACKEND_API_TIMEOUT_SECS, BACKEND_API_URL

logger = logging.getLogger(__name__)


def _build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_session = _build_session()


def _post(path: str, payload: dict[str, Any]) -> bool:
    url = f"{BACKEND_API_URL.rstrip('/')}{path}"
    try:
        resp = _session.post(url, json=payload, timeout=BACKEND_API_TIMEOUT_SECS)
        if resp.status_code == 422:
            # Schema mismatch — log the detail so it can be fixed
            logger.error(
                "POST %s validation error (422): %s | payload keys: %s",
                url, resp.text[:300], list(payload.keys()),
            )
            return False
        resp.raise_for_status()
        return True
    except requests.ConnectionError:
        logger.warning("POST %s — backend unreachable (connection refused)", url)
        return False
    except requests.Timeout:
        logger.warning("POST %s — timed out after %.1fs", url, BACKEND_API_TIMEOUT_SECS)
        return False
    except requests.RequestException as e:
        logger.warning("POST %s failed: %s", url, e)
        return False


def post_log(
    *,
    source: str,
    severity: str,
    message: str,
    timestamp: str | None = None,
    raw: str | None = None,
) -> bool:
    """POST /ingest/logs — persist a processed record."""
    payload: dict[str, Any] = {
        "source": source,
        "severity": severity,
        "message": message,
    }
    if timestamp:
        payload["timestamp"] = timestamp
    if raw:
        payload["raw"] = raw
    return _post("/ingest/logs", payload)


def post_alert(
    *,
    title: str,
    severity: str,
    source: str,
    description: str | None = None,
) -> bool:
    """POST /ingest/alerts — raise a security alert."""
    payload: dict[str, Any] = {
        "title": title,
        "severity": severity,
        "source": source,
    }
    if description:
        payload["description"] = description
    return _post("/ingest/alerts", payload)


def post_metrics(snapshot: dict[str, Any]) -> bool:
    """POST /ingest/metrics — publish a streaming metrics window snapshot."""
    return _post("/ingest/metrics", snapshot)


def post_heartbeat(*, service: str, status: str = "running") -> bool:
    """POST /ingest/heartbeat — signal that the streaming job is alive."""
    from datetime import datetime, timezone
    payload: dict[str, Any] = {
        "service": service,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return _post("/ingest/heartbeat", payload)
