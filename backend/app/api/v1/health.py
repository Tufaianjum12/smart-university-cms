"""
Health check endpoint.

This is the ONLY endpoint Phase 1 needs. Its job is to prove three things
are true at once:
  1. FastAPI itself is running.
  2. Configuration loaded correctly from the environment.
  3. PostgreSQL is actually reachable (real check, not assumed).

Real academic endpoints (students, courses, attendance, ...) start in
later phases.
"""

from fastapi import APIRouter

from app.config.settings import settings
from app.db.connection_check import check_database_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    db_connected, db_detail = check_database_connection()

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": {
            "connected": db_connected,
            "detail": db_detail,
        },
    }
