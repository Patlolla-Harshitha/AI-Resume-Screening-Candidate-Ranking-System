"""
Database initialization — creates all tables and seeds the default admin user.
"""

from __future__ import annotations

from passlib.context import CryptContext

from config import settings
from database.base import Base, engine, SessionLocal
from utils.logger import get_logger

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def initialize_database() -> None:
    """
    Create all SQLAlchemy tables and insert seed data if not already present.
    Safe to call multiple times (idempotent).
    """
    # Import all models so Base.metadata is populated
    import models.candidate  # noqa: F401
    import models.job        # noqa: F401
    import models.scoring    # noqa: F401
    import models.audit      # noqa: F401
    import models.report     # noqa: F401
    import models.user       # noqa: F401

    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created / verified")

    # Seed admin user
    with SessionLocal() as db:
        from models.user import User
        existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not existing:
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=pwd_context.hash(settings.ADMIN_PASSWORD),
                is_active=True,
                is_admin=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Default admin user '%s' created", settings.ADMIN_USERNAME)
        else:
            logger.debug("Admin user '%s' already exists", settings.ADMIN_USERNAME)
