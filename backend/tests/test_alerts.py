import pytest


# --- POST /alerts/ ---

def test_post_alert_minimal(client, auth_headers):
    resp = client.post(
        "/alerts/",
        json={"title": "Brute force", "severity": "high", "source": "auth-service"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Brute force"
    assert body["status"] == "open"
    assert "id" in body
    assert "created_at" in body


def test_post_alert_with_description(client, auth_headers):
    resp = client.post(
        "/alerts/",
        json={
            "title": "SQL injection",
            "severity": "critical",
            "source": "waf",
            "description": "Detected in /api/login endpoint",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["description"] == "Detected in /api/login endpoint"


def test_post_alert_missing_required_field(client, auth_headers):
    resp = client.post(
        "/alerts/",
        json={"title": "Missing source", "severity": "low"},   # missing source
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_post_alert_unauthenticated(client):
    resp = client.post(
        "/alerts/",
        json={"title": "x", "severity": "low", "source": "y"},
    )
    assert resp.status_code == 401


# --- GET /alerts/ ---

def test_get_alerts_returns_list(client, auth_headers):
    resp = client.get("/alerts/", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "alerts" in body
    assert "total" in body
    assert isinstance(body["alerts"], list)


def test_get_alerts_unauthenticated(client):
    resp = client.get("/alerts/")
    assert resp.status_code == 401


# --- GET /alerts/{id} ---

def test_get_alert_by_id(client, auth_headers):
    create = client.post(
        "/alerts/",
        json={"title": "XSS attempt", "severity": "medium", "source": "proxy"},
        headers=auth_headers,
    )
    alert_id = create.json()["id"]
    resp = client.get(f"/alerts/{alert_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == alert_id


def test_get_alert_not_found(client, auth_headers):
    resp = client.get("/alerts/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_get_alert_by_id_unauthenticated(client, auth_headers):
    create = client.post(
        "/alerts/",
        json={"title": "x", "severity": "low", "source": "y"},
        headers=auth_headers,
    )
    alert_id = create.json()["id"]
    resp = client.get(f"/alerts/{alert_id}")
    assert resp.status_code == 401


# --- PATCH /alerts/{id} ---

def test_patch_alert_to_acknowledged(client, auth_headers):
    create = client.post(
        "/alerts/",
        json={"title": "Lateral movement", "severity": "high", "source": "edr"},
        headers=auth_headers,
    )
    alert_id = create.json()["id"]
    resp = client.patch(f"/alerts/{alert_id}", json={"status": "acknowledged"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "acknowledged"


def test_patch_alert_to_resolved(client, auth_headers):
    create = client.post(
        "/alerts/",
        json={"title": "C2 beacon", "severity": "critical", "source": "ndr"},
        headers=auth_headers,
    )
    alert_id = create.json()["id"]
    resp = client.patch(f"/alerts/{alert_id}", json={"status": "resolved"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"


def test_patch_alert_not_found(client, auth_headers):
    resp = client.patch("/alerts/99999", json={"status": "resolved"}, headers=auth_headers)
    assert resp.status_code == 404


def test_patch_alert_unauthenticated(client, auth_headers):
    create = client.post(
        "/alerts/",
        json={"title": "x", "severity": "low", "source": "y"},
        headers=auth_headers,
    )
    alert_id = create.json()["id"]
    resp = client.patch(f"/alerts/{alert_id}", json={"status": "resolved"})
    assert resp.status_code == 401


# --- POST /ingest/alerts (no auth) ---

def test_ingest_alert_no_auth(client):
    resp = client.post(
        "/ingest/alerts",
        json={"title": "Anomaly spike", "severity": "high", "source": "ml-engine"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "open"


def test_ingest_alert_missing_field(client):
    resp = client.post(
        "/ingest/alerts",
        json={"title": "Missing source", "severity": "high"},
    )
    assert resp.status_code == 422
