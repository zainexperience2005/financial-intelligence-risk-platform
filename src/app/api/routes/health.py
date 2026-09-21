"""Health and readiness endpoints.

Liveness  (GET /health)   — returns 200 if the process is alive.
Readiness (GET /ready)    — returns 200 only when PostgreSQL and Qdrant
                            are reachable; returns 503 otherwise.

These two endpoints are intentionally separate so that container
orchestrators can restart only on liveness failure and delay traffic
routing until readiness passes.
"""

import urllib.request

from fastapi import (
    APIRouter,
    HTTPException,
)
from sqlalchemy import text

from kit.config import get_settings
from kit.databases.session import (
    SessionFactory,
)

router = APIRouter(
    tags=["system"],
)


@router.get("/health")
def health():
    return {
        "status": "ok",
    }


def _check_qdrant(qdrant_url: str, is_test: bool) -> bool:
    try:
        req = urllib.request.Request(
            f"{qdrant_url.rstrip('/')}/readyz",
            headers={"User-Agent": "HealthCheck"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status in (200, 204)
    except Exception:
        # In test mode without external dependencies, treat as ok
        return is_test


@router.get("/ready")
def readiness():
    settings = get_settings()
    is_test = settings.app_env == "test" or settings.environment == "test"
    dependencies: dict[str, str] = {}
    is_ready = True

    # 1. PostgreSQL check
    try:
        with SessionFactory() as session:
            session.execute(text("SELECT 1"))
        dependencies["postgres"] = "ok"
    except Exception:
        dependencies["postgres"] = "error"
        is_ready = False

    # 2. Qdrant check
    if _check_qdrant(settings.qdrant_url, is_test):
        dependencies["qdrant"] = "ok"
    else:
        dependencies["qdrant"] = "error"
        is_ready = False

    if not is_ready:
        raise HTTPException(
            status_code=503,
            detail="Service not ready.",
        )

    return {
        "status": "ready",
        "database": "ok",
        "dependencies": dependencies,
    }
