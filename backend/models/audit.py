"""
Audit log and processing history ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Index
from sqlalchemy.orm import Mapped

from database.base import Base


class AuditLog(Base):
    """
    Immutable audit trail of all significant system actions.
    Used for compliance, debugging, and security monitoring.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action: str = Column(String(100), nullable=False)          # e.g., "RESUME_UPLOADED"
    entity_type: str = Column(String(100), nullable=True)      # e.g., "Candidate"
    entity_id: str = Column(String(36), nullable=True)
    actor_id: str = Column(String(36), nullable=True)          # User who performed the action
    actor_username: str = Column(String(100), nullable=True)
    ip_address: str = Column(String(45), nullable=True)
    user_agent: str = Column(String(500), nullable=True)
    details: dict = Column(JSON, nullable=True)
    status: str = Column(String(50), nullable=True)            # "SUCCESS" | "FAILURE"
    error_message: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action!r} entity={self.entity_type!r}/{self.entity_id!r}>"


class ProcessingHistory(Base):
    """
    Records the timing and outcome of every AI processing operation
    (parsing, embedding, ranking) for performance monitoring.
    """

    __tablename__ = "processing_history"
    __table_args__ = (
        Index("ix_processing_history_operation", "operation"),
        Index("ix_processing_history_entity", "entity_id"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    operation: str = Column(String(100), nullable=False)       # "parse_resume", "rank", etc.
    entity_id: str = Column(String(36), nullable=True)
    entity_type: str = Column(String(50), nullable=True)
    status: str = Column(String(50), nullable=False)           # "SUCCESS" | "FAILURE"
    duration_ms: int = Column(Integer, nullable=True)
    details: dict = Column(JSON, nullable=True)
    error: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
