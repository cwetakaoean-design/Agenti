"""Health and configuration status endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict[str, object]:
    s = get_settings()
    return {
        "status": "ok",
        "llm_mode": "stub" if s.llm_is_stub() else "gigachat",
    }
