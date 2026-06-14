"""Incident management endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_incidents():
    """
    Retrieve all incidents.

    TODO:
        - Filter by status (open / closed / in-progress)
        - Include linked alerts
        - Pull from PostgreSQL incidents table
    """
    pass


@router.post("/")
async def create_incident():
    """
    Create a new incident from one or more alerts.

    TODO:
        - Accept list of alert IDs
        - Trigger LLM summarization (Phase 8)
        - Return incident ID and AI-generated summary
    """
    pass


@router.get("/{incident_id}")
async def get_incident(incident_id: int):
    """
    Retrieve a single incident with full detail.

    Args:
        incident_id: Primary key of the incident

    TODO:
        - Return linked alerts, timeline, AI summary
    """
    pass
