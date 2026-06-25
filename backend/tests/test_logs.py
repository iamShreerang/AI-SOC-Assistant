import pytest


# --- POST /logs/ ---

def test_post_log_minimal(client, auth_headers):
    resp = client.post(
        "/logs/",
        json={"source": "firewall", "severity": "critical", "message": "Port scan detected"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["source"] == "firewall"
    assert body["severity"] == "critical"
    assert body["message"] == "Port scan detected"
    assert "id" in body
    assert "ingested_at" in body


def test_post_log_with_optional_fields(client, auth_headers):
    resp = client.post(
        "/logs/",
        json={
            "source": "ids",
            "severity": "critical",
            "message": "Intrusion attempt",
            "raw": "RAW_PAYLOAD_STRING",
            "timestamp": "2024-01-01T00:00:00Z",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["raw"] == "RAW_PAYLOAD_STRING"
    assert body["timestamp"] is not None


def test_post_log_missing_required_field(client, auth_headers):
    resp = client.post(
        "/logs/",
        json={"source": "firewall", "severity": "error"},   # missing message
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_post_log_unauthenticated(client):
    resp = client.post(
        "/logs/",
        json={"source": "x", "severity": "info", "message": "test"},
    )
    assert resp.status_code == 401


# --- GET /logs/ ---

def test_get_logs_returns_list(client, auth_headers):
    resp = client.get("/logs/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "logs" in body
    assert "total" in body
    assert isinstance(body["logs"], list)


def test_get_logs_limit_param(client, auth_headers, reset_stores):
    for i in range(5):
        client.post(
            "/logs/",
            json={"source": "src", "severity": "info", "message": f"log {i}"},
            headers=auth_headers,
        )
    resp = client.get("/logs/?limit=3", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["logs"]) == 3
    assert body["total"] == 5


def test_get_logs_unauthenticated(client):
    resp = client.get("/logs/")
    assert resp.status_code == 401


# --- GET /logs/{id} ---

def test_get_log_by_id(client, auth_headers):
    create = client.post(
        "/logs/",
        json={"source": "siem", "severity": "warning", "message": "Anomaly"},
        headers=auth_headers,
    )
    log_id = create.json()["id"]
    resp = client.get(f"/logs/{log_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == log_id


def test_get_log_not_found(client, auth_headers):
    resp = client.get("/logs/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_get_log_by_id_unauthenticated(client, auth_headers):
    create = client.post(
        "/logs/",
        json={"source": "x", "severity": "info", "message": "y"},
        headers=auth_headers,
    )
    log_id = create.json()["id"]
    resp = client.get(f"/logs/{log_id}")
    assert resp.status_code == 401


# --- POST /ingest/logs (no auth) ---

def test_ingest_log_no_auth(client):
    resp = client.post(
        "/ingest/logs",
        json={"source": "kafka-consumer", "severity": "info", "message": "streamed log"},
    )
    assert resp.status_code == 201
    assert resp.json()["source"] == "kafka-consumer"


def test_ingest_log_missing_field(client):
    resp = client.post(
        "/ingest/logs",
        json={"source": "kafka-consumer", "severity": "info"},   # missing message
    )
    assert resp.status_code == 422
