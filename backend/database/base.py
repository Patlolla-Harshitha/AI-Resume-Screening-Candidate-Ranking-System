"""
Database base configuration — SQLAlchemy engine, session factory, and declarative base.
Designed for SQLite in development and PostgreSQL in production (change DATABASE_URL).
"""

from __future__ import annotations

from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
# SQLite-specific configuration for WAL mode and foreign key enforcement.
# For PostgreSQL, these engine args are ignored — the URL change is sufficient.
connect_args: dict = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,          # Log all SQL in debug mode
    pool_pre_ping=True,           # Verify connection before use
    pool_size=10 if "sqlite" not in settings.DATABASE_URL else 1,
    max_overflow=20 if "sqlite" not in settings.DATABASE_URL else 0,
)

# Enable WAL mode and foreign keys for SQLite
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[type-arg]
        """Apply SQLite-specific PRAGMAs on every new connection."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64 MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """All ORM models inherit from this base."""
    pass


# ---------------------------------------------------------------------------
# Dependency injection helpers
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per request and
    ensures it is closed after the request completes.

    Usage::

        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
