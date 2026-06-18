import pytest


# --- Registration ---

def test_register_new_user(client):
    resp = client.post("/auth/register", json={"username": "newuser", "password": "pass123"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "newuser"
    assert body["role"] == "analyst"          # default role


def test_register_custom_role(client):
    resp = client.post("/auth/register", json={"username": "soc_admin", "password": "x", "role": "admin"})
    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


def test_register_duplicate(client):
    client.post("/auth/register", json={"username": "dupuser", "password": "pass"})
    resp = client.post("/auth/register", json={"username": "dupuser", "password": "pass"})
    assert resp.status_code == 409


def test_register_missing_fields(client):
    resp = client.post("/auth/register", json={"username": "incomplete"})
    assert resp.status_code == 422


# --- Login ---

def test_login_valid_analyst(client):
    resp = client.post("/auth/login", json={"username": "analyst", "password": "analyst123"})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    # token must be a non-empty string
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 20


def test_login_valid_admin(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    resp = client.post("/auth/login", json={"username": "analyst", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/auth/login", json={"username": "ghost", "password": "x"})
    assert resp.status_code == 401


def test_login_missing_fields(client):
    resp = client.post("/auth/login", json={"username": "analyst"})
    assert resp.status_code == 422


# --- /users/me ---

def test_me_analyst(client, auth_headers):
    resp = client.get("/auth/users/me", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "analyst"
    assert body["role"] == "analyst"


def test_me_admin(client, admin_headers):
    resp = client.get("/auth/users/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_me_no_token(client):
    resp = client.get("/auth/users/me")
    assert resp.status_code == 401


def test_me_invalid_token(client):
    resp = client.get("/auth/users/me", headers={"Authorization": "Bearer not.a.valid.token"})
    assert resp.status_code == 401


def test_me_malformed_header(client):
    resp = client.get("/auth/users/me", headers={"Authorization": "Token abc123"})
    assert resp.status_code == 401
