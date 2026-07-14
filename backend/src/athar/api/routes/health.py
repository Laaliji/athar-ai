"""Health and status routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from athar.config import settings
from athar.models.schemas import HealthResponse, SystemStatus
from athar.rag.pipeline import pipeline

router = APIRouter(tags=["Health"])


@router.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/api/docs",
    }


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Lightweight health check — used by load balancers."""
    status = "healthy" if pipeline.is_ready else "degraded"
    return HealthResponse(
        status=status,
        message=f"{settings.app_name} is {status}",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app_version,
    )


@router.get("/api/status", response_model=SystemStatus)
async def system_status() -> SystemStatus:
    """Detailed system status including LLM provider and vector DB state."""
    status_dict = pipeline.get_status()
    return SystemStatus(**status_dict)
