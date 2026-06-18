import pytest


# --- POST /incidents/ ---

def test_post_incident_minimal(client, auth_headers):
    resp = client.post(
        "/incidents/",
        json={"title": "Ransomware detected"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Ransomware detected"
    assert body["status"] == "open"
    assert body["summary"] is None
    assert "id" in body
    assert "created_at" in body


def test_post_incident_with_description_and_alerts(client, auth_headers):
    resp = client.post(
        "/incidents/",
        json={
            "title": "Data exfiltration",
            "description": "Large outbound transfer detected",
            "alert_ids": [1, 2, 3],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["description"] == "Large outbound transfer detected"
    assert body["alert_ids"] == [1, 2, 3]


def test_post_incident_missing_title(client, auth_headers):
    resp = client.post(
        "/incidents/",
        json={"description": "No title provided"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_post_incident_unauthenticated(client):
    resp = client.post("/incidents/", json={"title": "x"})
    assert resp.status_code == 401


# --- GET /incidents/ ---

def test_get_incidents_returns_list(client, auth_headers):
    resp = client.get("/incidents/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_incidents_unauthenticated(client):
    resp = client.get("/incidents/")
    assert resp.status_code == 401


# --- GET /incidents/{id} ---

def test_get_incident_by_id(client, auth_headers):
    create = client.post(
        "/incidents/",
        json={"title": "Phishing campaign"},
        headers=auth_headers,
    )
    incident_id = create.json()["id"]
    resp = client.get(f"/incidents/{incident_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == incident_id


def test_get_incident_not_found(client, auth_headers):
    resp = client.get("/incidents/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_get_incident_by_id_unauthenticated(client, auth_headers):
    create = client.post(
        "/incidents/",
        json={"title": "Privilege escalation"},
        headers=auth_headers,
    )
    incident_id = create.json()["id"]
    resp = client.get(f"/incidents/{incident_id}")
    assert resp.status_code == 401


# --- POST /summaries ---

def test_receive_summary(client, auth_headers):
    create = client.post(
        "/incidents/",
        json={"title": "Zero-day exploit"},
        headers=auth_headers,
    )
    incident_id = create.json()["id"]
    resp = client.post(
        "/summaries",
        json={"incident_id": incident_id, "summary": "Attacker exploited CVE-2024-1234."},
    )
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Attacker exploited CVE-2024-1234."


def test_receive_summary_overwrites_previous(client, auth_headers):
    create = client.post(
        "/incidents/",
        json={"title": "Supply chain attack"},
        headers=auth_headers,
    )
    incident_id = create.json()["id"]
    client.post("/summaries", json={"incident_id": incident_id, "summary": "First summary."})
    resp = client.post("/summaries", json={"incident_id": incident_id, "summary": "Updated summary."})
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Updated summary."


def test_receive_summary_not_found(client):
    resp = client.post("/summaries", json={"incident_id": 99999, "summary": "x"})
    assert resp.status_code == 404


def test_receive_summary_missing_field(client):
    resp = client.post("/summaries", json={"incident_id": 1})   # missing summary
    assert resp.status_code == 422
