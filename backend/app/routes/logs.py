"""Log ingestion and retrieval endpoints."""

from fastapi import APIRouter

router = APIRouter()
ingest_router = APIRouter(prefix="/ingest")


@router.get("/")
async def get_logs():
    """
    Retrieve recent security logs.

    TODO:
        - Add query params: source, severity, time range, pagination
        - Connect to Elasticsearch / PostgreSQL
    """
    pass


@router.post("/")
async def ingest_log():
    """
    Ingest a new security log entry.

    TODO:
        - Validate log schema (Pydantic model)
        - Publish to Kafka topic
    """
    pass
