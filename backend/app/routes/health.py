"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Returns service health status.

    Returns:
        dict: status and API version
    """
    return {"status": "ok", "version": "0.1.0"}
