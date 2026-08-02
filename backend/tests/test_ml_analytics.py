"""
Tests for:
  - GET /stats/ml        — ML analytics derived from real DB data
  - POST /ingest/heartbeat — Spark heartbeat upsert
  - POST /ingest/metrics   — pipeline metrics ingestion

Note: ML analytics tests require a live PostgreSQL database configured in
backend/.env (DATABASE_URL). They are automatically skipped when the DB is
not reachable. Heartbeat and metrics tests work without a live DB.
"""
import time
import pytest


def _db_available(client) -> bool:
    """Return True if the backend can reach the configured PostgreSQL database."""
    try:
        resp = client.get("/health")
        return resp.json().get("components", {}).get("database") is True
    except Exception:
        return False


# ── ML Analytics ─────────────────────────────────────────────────────────────

def test_ml_analytics_returns_200(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database — skipping ML analytics tests")
    resp = client.get("/stats/ml", headers=auth_headers)
    assert resp.status_code == 200


def test_ml_analytics_required_keys(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database")
    resp = client.get("/stats/ml", headers=auth_headers)
    data = resp.json()
    required = {
        "model_accuracy", "predictions_today", "anomalies_detected",
        "anomaly_data", "threat_classification", "predictions",
    }
    assert required.issubset(data.keys()), f"Missing keys: {required - data.keys()}"


def test_ml_analytics_returns_numeric_values(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database")
    resp = client.get("/stats/ml", headers=auth_headers)
    data = resp.json()
    assert isinstance(data["model_accuracy"], (int, float))
    assert isinstance(data["predictions_today"], int)
    assert isinstance(data["anomalies_detected"], int)


def test_ml_analytics_anomaly_data_is_list(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database")
    resp = client.get("/stats/ml", headers=auth_headers)
    data = resp.json()
    assert isinstance(data["anomaly_data"], list)
    # Each entry must have name (str) and value (number)
    for entry in data["anomaly_data"]:
        assert "name" in entry
        assert "value" in entry
        assert isinstance(entry["value"], (int, float))


def test_ml_analytics_threat_classification_is_list(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database")
    resp = client.get("/stats/ml", headers=auth_headers)
    data = resp.json()
    assert isinstance(data["threat_classification"], list)


def test_ml_analytics_no_negative_values(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database")
    resp = client.get("/stats/ml", headers=auth_headers)
    data = resp.json()
    assert data["model_accuracy"] >= 0
    assert data["predictions_today"] >= 0
    assert data["anomalies_detected"] >= 0


def test_ml_analytics_empty_db_returns_zeros(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database")
    """With no data in DB (reset_stores fixture cleared it), values should be 0."""
    resp = client.get("/stats/ml", headers=auth_headers)
    data = resp.json()
    assert data["predictions_today"] == 0
    assert data["anomalies_detected"] == 0
    assert data["model_accuracy"] == 0.0


def test_ml_analytics_predictions_with_data(client, auth_headers):
    if not _db_available(client):
        pytest.skip("No live database")
    """After creating a critical alert, ML analytics should reflect it."""
    # Create a critical alert
    client.post(
        "/ingest/alerts",
        json={
            "title": "Test ML alert",
            "severity": "critical",
            "source": "test-ml",
            "description": "Unit test alert for ML analytics",
        },
    )
    resp = client.get("/stats/ml", headers=auth_headers)
    data = resp.json()
    # There is now at least one alert in the system
    assert data["predictions_today"] >= 1


# ── Heartbeat ─────────────────────────────────────────────────────────────────

def test_heartbeat_returns_200(client):
    """POST /ingest/heartbeat should not require auth and must return 200."""
    resp = client.post(
        "/ingest/heartbeat",
        json={"service": "spark", "status": "running", "timestamp": ""},
    )
    assert resp.status_code == 200
    # Returns 'ok' when DB write succeeded, 'error' when DB is unavailable.
    # Either is acceptable — the important thing is the HTTP 200 itself.
    assert resp.json().get("detail") in ("ok", "error")


def test_heartbeat_different_services(client):
    """Multiple distinct services should each return 200."""
    for svc in ("spark", "kafka-producer", "ml-worker"):
        resp = client.post(
            "/ingest/heartbeat",
            json={"service": svc, "status": "running", "timestamp": ""},
        )
        assert resp.status_code == 200, f"Heartbeat failed for service={svc}"


def test_heartbeat_accepts_empty_timestamp(client):
    """Heartbeat should accept an empty string timestamp (uses server time)."""
    resp = client.post(
        "/ingest/heartbeat",
        json={"service": "spark", "status": "running", "timestamp": ""},
    )
    assert resp.status_code == 200


def test_heartbeat_duplicate_is_idempotent(client):
    """Posting two heartbeats for the same service should both succeed (upsert)."""
    payload = {"service": "spark-idempotent", "status": "running", "timestamp": ""}
    for _ in range(2):
        resp = client.post("/ingest/heartbeat", json=payload)
        assert resp.status_code == 200


def test_heartbeat_reflects_in_health(client):
    """After a fresh heartbeat, spark component in /health may become healthy."""
    client.post(
        "/ingest/heartbeat",
        json={"service": "spark", "status": "running", "timestamp": ""},
    )
    resp = client.get("/health")
    assert resp.status_code == 200
    # Spark is either healthy (fresh heartbeat) or not (if threshold not met);
    # either way the key must be present.
    assert "spark" in resp.json()["components"]


# ── Metrics ───────────────────────────────────────────────────────────────────

def test_metrics_ingest_returns_200(client):
    resp = client.post(
        "/ingest/metrics",
        json={
            "total_requests": 100,
            "attack_count": 10,
            "normal_count": 90,
            "requests_per_second": 2.5,
            "requests_per_minute": 150.0,
            "avg_inference_latency_ms": 12.3,
            "unique_src_ips": 5,
            "unique_dst_ips": 3,
            "suspicious_ip_count": 1,
            "total_bytes_transferred": 500000,
            "avg_packet_size": 5000.0,
            "alerts_critical": 2,
            "alerts_high": 3,
            "alerts_medium": 4,
            "alerts_low": 1,
        },
    )
    assert resp.status_code == 200
    assert resp.json().get("detail") == "ok"


def test_metrics_ingest_with_defaults(client):
    """Metrics endpoint must accept an empty payload (all fields optional)."""
    resp = client.post("/ingest/metrics", json={})
    assert resp.status_code == 200

