"""
User model for authentication and authorization.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from database.base import Base


class User(Base):
    """System user (recruiter / admin) with JWT-based authentication."""

    __tablename__ = "users"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: str = Column(String(100), unique=True, nullable=False, index=True)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password: str = Column(String(255), nullable=False)
    full_name: str = Column(String(255), nullable=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_admin: bool = Column(Boolean, default=False, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login: datetime = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User username={self.username!r} admin={self.is_admin}>"
