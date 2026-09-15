"""
Application entry point.

This file's only job is to assemble the app: create the FastAPI instance,
attach middleware (CORS), register global exception handlers, and mount
the versioned API router. It intentionally contains no business logic —
that discipline is what keeps main.py readable as the project grows
across 24 phases.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.config.settings import settings
from app.core.exceptions import AppError

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Smart University Academic Management System API — Phase 1 foundation.",
)

# --- CORS ---
# In development, we allow the local Vite dev server origin(s) defined in
# .env (CORS_ORIGINS). In production, this will be set to the real
# deployed frontend URL(s) — never "*" — via the same environment
# variable, with no code change required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Global exception handling ---
# Any AppError (or subclass, like NotFoundError) raised anywhere in the
# app is converted into a consistent JSON error shape instead of a raw
# 500 or an inconsistent ad hoc response.
@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


# --- Routers ---
# Every actual endpoint lives under /api/v1, mounted here in one line.
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root() -> dict:
    """Unversioned root endpoint — just a friendly pointer to the real API."""
    return {
        "message": f"{settings.APP_NAME} is running.",
        "docs": "/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health",
    }
