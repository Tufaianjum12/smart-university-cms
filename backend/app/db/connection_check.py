"""
A small, honest database connectivity check.

This does not create or query any application table (there are none yet).
It just asks PostgreSQL "are you there?" via `SELECT 1`, so the health
endpoint can report real connectivity status instead of assuming it.
"""

from sqlalchemy import text

from app.db.session import engine


def check_database_connection() -> tuple[bool, str]:
    """
    Attempts a real connection to PostgreSQL.

    Returns:
        (True, "connected") on success.
        (False, "<error message>") on failure — never raises, so the
        health endpoint can report a clean status instead of crashing.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "connected"
    except Exception as exc:  # noqa: BLE001 - intentionally broad for a health check
        return False, str(exc)
