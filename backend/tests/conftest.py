import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


# --- Auth token helpers ---

@pytest.fixture(scope="session")
def analyst_token(client):
    try:
        resp = client.post("/auth/login", json={"username": "analyst", "password": "analyst123"})
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except Exception:
        pass
    return None


@pytest.fixture(scope="session")
def admin_token(client):
    try:
        resp = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except Exception:
        pass
    return None


@pytest.fixture(scope="session")
def auth_headers(analyst_token):
    if analyst_token is None:
        return {}
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    if admin_token is None:
        return {}
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset database tables before every test for isolation.
    
    When the database is unreachable (e.g. no .env configured), this fixture
    silently skips cleanup so tests that don't need the DB can still run.
    """
    from app.database import SessionLocal
    from app.models.database import IncidentAlert, Incident, Alert, Log, User

    db = None
    try:
        db = SessionLocal()
        db.query(IncidentAlert).delete()
        db.query(Incident).delete()
        db.query(Alert).delete()
        db.query(Log).delete()
        db.query(User).filter(User.username.notin_(["analyst", "admin"])).delete(
            synchronize_session=False
        )
        db.commit()
    except Exception:
        if db:
            try:
                db.rollback()
            except Exception:
                pass
        # DB not reachable — skip cleanup silently
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass
    yield
