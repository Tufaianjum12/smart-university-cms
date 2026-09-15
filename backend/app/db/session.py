"""
Database connection infrastructure.

Phase 1 scope: create the SQLAlchemy engine, a session factory, and a
FastAPI dependency (`get_db`) that hands each request its own database
session. This is the plumbing every future model/repository will sit on
top of — it does NOT define any academic tables. Those start in Phase 2.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config.settings import settings

# The engine manages the actual pool of connections to PostgreSQL.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a factory that produces new Session objects on demand.
# We don't share one global session across requests — each request gets
# its own, which is committed/closed at the end of that request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    Base class every future ORM model (Student, Course, etc. in later
    phases) will inherit from. Defined now so Alembic and the models
    package have a stable import target from day one.
    """

    pass


def get_db() -> Generator:
    """
    FastAPI dependency that yields a database session for the lifetime of
    a single request, and guarantees it is closed afterwards even if the
    request raises an error.

    Usage in a future route:
        def some_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
