"""Health check endpoint."""

from fastapi import APIRouter
from app.database import check_connection
from app.utils.config import settings
from app.utils.elasticsearch_client import check_es_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Returns service health status.

    Returns:
        dict: status, API version, and component health
    """
    db_ok = check_connection()
    es_ok = False
    if settings.elasticsearch_enabled:
        es_ok = check_es_connection()
        
    return {
        "status": "ok" if db_ok else "error",
        "version": "0.1.0",
        "components": {
            "database": db_ok,
            "elasticsearch": es_ok,
            "kafka": False,
            "spark": False,
            "ml_model": False,
        }
    }
