def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data
    assert "components" in data


def test_health_components_present(client):
    resp = client.get("/health")
    components = resp.json()["components"]
    assert "database" in components
    assert "kafka" in components
    assert "spark" in components
    assert "ml_model" in components
    assert "llm" in components
    assert "elasticsearch" in components


def test_health_ml_model_reflects_artifacts(client):
    """ml_model should be True when saved_models/ files exist."""
    from pathlib import Path
    model_dir = Path(__file__).parent.parent.parent / "ml" / "saved_models"
    expected = all((model_dir / f).exists() for f in ["cnn_lstm.pt", "pipeline.pkl", "threshold.pkl"])
    resp = client.get("/health")
    assert resp.json()["components"]["ml_model"] == expected


def test_health_elasticsearch_disabled(client):
    """Elasticsearch should report disabled when ELASTICSEARCH_ENABLED=false."""
    from app.utils.config import settings
    resp = client.get("/health")
    es = resp.json()["components"]["elasticsearch"]
    if not settings.elasticsearch_enabled:
        assert es == {"enabled": False, "healthy": False}
