import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.services.log_service as _log_svc
import app.services.alert_service as _alert_svc
import app.services.incident_service as _inc_svc


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# --- Auth token helpers ---

@pytest.fixture(scope="session")
def analyst_token(client):
    resp = client.post("/auth/login", json={"username": "analyst", "password": "analyst123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(client):
    resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(analyst_token):
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# --- Store reset between tests that need isolation ---

@pytest.fixture(autouse=True)
def reset_stores():
    """Reset all database tables and in-memory stores before every test."""
    from app.database import SessionLocal
    from app.models.database import Log, Alert, Incident, User
    
    db = SessionLocal()
    try:
        db.query(Incident).delete()
        db.query(Alert).delete()
        db.query(Log).delete()
        db.query(User).filter(User.username.notin_(["analyst", "admin"])).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    _log_svc._store.clear()
    _log_svc._counter = 0
    _alert_svc._store.clear()
    _alert_svc._counter = 0
    _inc_svc._store.clear()
    _inc_svc._counter = 0
    yield
