"""
Aggregates every v1 router into one object that main.py mounts once.

As new modules are added in later phases (students, attendance, grades,
...), each gets its own file in app/api/v1/ and is included here. main.py
never has to change to pick up new routers.
"""

from fastapi import APIRouter

from app.api.v1 import health, courses

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)

api_v1_router.include_router(courses.router)
