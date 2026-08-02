"""
Unit tests for streaming/backend_client.py.
Mocks HTTP so no live backend or Kafka is required.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from streaming import backend_client


# ── Helpers ──────────────────────────────────────────────────────────────────

def _ok_response(status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


def _error_response(status_code: int, body: str = "") -> MagicMock:
    import requests
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = body
    resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


# ── post_log payload ──────────────────────────────────────────────────────────

def test_post_log_sends_required_fields():
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        result = backend_client.post_log(
            source="spark-streaming",
            severity="critical",
            message="Test attack",
        )
    assert result is True
    _, kwargs = mock_post.call_args
    payload = kwargs["json"]
    assert payload["source"] == "spark-streaming"
    assert payload["severity"] == "critical"
    assert payload["message"] == "Test attack"


def test_post_log_includes_optional_fields():
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        backend_client.post_log(
            source="spark-streaming",
            severity="warning",
            message="Test",
            timestamp="2024-01-01T00:00:00Z",
            raw='{"srcip": "1.2.3.4"}',
        )
    payload = mock_post.call_args[1]["json"]
    assert "timestamp" in payload
    assert "raw" in payload


def test_post_log_omits_none_optional_fields():
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        backend_client.post_log(
            source="spark-streaming",
            severity="info",
            message="Normal traffic",
        )
    payload = mock_post.call_args[1]["json"]
    assert "timestamp" not in payload
    assert "raw" not in payload


def test_post_log_no_credentials_in_payload():
    """Ensure JWT tokens or secrets are never included in ingest payloads."""
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        backend_client.post_log(
            source="test",
            severity="info",
            message="Check payload",
        )
    payload = mock_post.call_args[1]["json"]
    sensitive_keys = {"password", "token", "api_key", "secret", "authorization"}
    assert not sensitive_keys.intersection(set(payload.keys())), \
        f"Sensitive keys found in payload: {sensitive_keys.intersection(payload.keys())}"


# ── post_alert payload ────────────────────────────────────────────────────────

def test_post_alert_sends_required_fields():
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        result = backend_client.post_alert(
            title="Port scan detected",
            severity="medium",
            source="spark-threat-rules",
        )
    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert payload["title"] == "Port scan detected"
    assert payload["severity"] == "medium"
    assert payload["source"] == "spark-threat-rules"


def test_post_alert_with_description():
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        backend_client.post_alert(
            title="Repeat attack",
            severity="critical",
            source="spark-ml-detector",
            description="3 attacks from 1.2.3.4 within 60s",
        )
    payload = mock_post.call_args[1]["json"]
    assert "description" in payload
    assert "60s" in payload["description"]


def test_post_alert_no_srcip_in_payload():
    """srcip is metadata for internal use; it must NOT be posted to /ingest/alerts."""
    # AlertCreate schema does NOT have srcip. If it were included, the backend
    # would return 422 Unprocessable Entity.
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        backend_client.post_alert(
            title="Test",
            severity="low",
            source="test",
        )
    payload = mock_post.call_args[1]["json"]
    assert "srcip" not in payload


# ── post_heartbeat payload ────────────────────────────────────────────────────

def test_post_heartbeat_sends_service_and_status():
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        result = backend_client.post_heartbeat(service="spark", status="running")
    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert payload["service"] == "spark"
    assert payload["status"] == "running"
    assert "timestamp" in payload


def test_post_heartbeat_timestamp_is_iso():
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        backend_client.post_heartbeat(service="spark")
    payload = mock_post.call_args[1]["json"]
    # Should be parseable as ISO 8601
    from datetime import datetime
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))


# ── Error handling ────────────────────────────────────────────────────────────

def test_returns_false_on_connection_error():
    import requests
    with patch.object(
        backend_client._session, "post",
        side_effect=requests.ConnectionError("refused"),
    ):
        result = backend_client.post_log(source="s", severity="info", message="m")
    assert result is False


def test_returns_false_on_422_schema_mismatch():
    resp = MagicMock()
    resp.status_code = 422
    resp.text = '{"detail": [{"msg": "field required"}]}'
    with patch.object(backend_client._session, "post", return_value=resp):
        result = backend_client.post_log(source="s", severity="info", message="m")
    assert result is False


def test_returns_false_on_timeout():
    import requests
    with patch.object(
        backend_client._session, "post",
        side_effect=requests.Timeout("timeout"),
    ):
        result = backend_client.post_alert(title="t", severity="low", source="s")
    assert result is False


# ── post_metrics ──────────────────────────────────────────────────────────────

def test_post_metrics_forwards_snapshot():
    snapshot = {
        "total_requests": 50,
        "attack_count": 5,
        "normal_count": 45,
        "requests_per_second": 1.5,
        "requests_per_minute": 90.0,
        "avg_inference_latency_ms": 8.2,
        "unique_src_ips": 3,
        "unique_dst_ips": 2,
        "suspicious_ip_count": 1,
        "total_bytes_transferred": 100000,
        "avg_packet_size": 2000.0,
        "alerts_critical": 1,
        "alerts_high": 2,
        "alerts_medium": 1,
        "alerts_low": 1,
    }
    with patch.object(backend_client._session, "post", return_value=_ok_response()) as mock_post:
        result = backend_client.post_metrics(snapshot)
    assert result is True
    assert mock_post.call_args[1]["json"] == snapshot


if __name__ == "__main__":
    import inspect, sys as _sys
    tests = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
        except Exception as e:
            failures += 1
            print(f"[FAIL] {t.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    _sys.exit(1 if failures else 0)
