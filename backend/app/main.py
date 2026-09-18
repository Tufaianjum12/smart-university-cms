from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.security_test import router as security_router
from app.api.v1.cms import router as cms_router
from app.api.v1.courses import router as courses_router
from app.core.config import settings
from app.db.session import engine

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(security_router, prefix="/api/v1")
app.include_router(cms_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")


def check_database():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"connected": True, "detail": "PostgreSQL connection successful"}
    except Exception:
        return {"connected": False, "detail": "Database connection failed"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "database": check_database(),
    }


@app.get("/api/v1/health")
def api_v1_health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "database": check_database(),
    }
