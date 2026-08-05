"""
Report ORM model.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Index
from sqlalchemy.orm import Mapped

from database.base import Base


class Report(Base):
    """
    Metadata about a generated report file (PDF, CSV, Excel).
    The actual file is stored on disk in the reports directory.
    """

    __tablename__ = "reports"
    __table_args__ = (
        Index("ix_reports_created_at", "created_at"),
        Index("ix_reports_type", "report_type"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type: str = Column(String(20), nullable=False)   # "pdf" | "csv" | "excel"
    title: str = Column(String(500), nullable=False)
    description: str = Column(Text, nullable=True)
    file_name: str = Column(String(500), nullable=False)
    file_path: str = Column(String(1000), nullable=False)
    file_size_bytes: int = Column(Integer, nullable=True)

    # What the report covers
    job_description_id: str = Column(String(36), nullable=True)
    candidate_count: int = Column(Integer, nullable=True)

    # Metadata about the report contents
    report_metadata: dict = Column(JSON, nullable=True)

    created_by: str = Column(String(100), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Report type={self.report_type!r} title={self.title!r}>"
