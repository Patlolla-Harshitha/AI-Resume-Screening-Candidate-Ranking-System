"""
Job Description ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON, Index
from sqlalchemy.orm import relationship, Mapped

from database.base import Base


class JobDescription(Base):
    """
    A recruiter-supplied job description used as the benchmark
    against which resumes are ranked.
    """

    __tablename__ = "job_descriptions"
    __table_args__ = (
        Index("ix_job_descriptions_title", "title"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: str = Column(String(500), nullable=False, index=True)
    company: str = Column(String(500), nullable=True)
    department: str = Column(String(255), nullable=True)
    location: str = Column(String(255), nullable=True)
    employment_type: str = Column(String(100), nullable=True)  # Full-time, Part-time, Contract
    experience_required: str = Column(String(100), nullable=True)  # e.g., "3-5 years"
    education_required: str = Column(String(255), nullable=True)

    # Raw text of the JD
    raw_text: str = Column(Text, nullable=False)

    # Parsed structured data
    responsibilities: list = Column(JSON, nullable=True)
    qualifications: list = Column(JSON, nullable=True)
    benefits: list = Column(JSON, nullable=True)

    # Embedding stored as JSON list for similarity computation
    embedding: list = Column(JSON, nullable=True)

    original_filename: str = Column(String(500), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    required_skills: Mapped[List["RequiredSkill"]] = relationship(
        "RequiredSkill", back_populates="job_description", cascade="all, delete-orphan"
    )
    rankings: Mapped[List["Ranking"]] = relationship(
        "Ranking", back_populates="job_description", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<JobDescription title={self.title!r} company={self.company!r}>"


class RequiredSkill(Base):
    """A skill requirement attached to a job description."""

    __tablename__ = "required_skills"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_description_id: str = Column(
        String(36),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_name: str = Column(String(200), nullable=False)
    skill_category: str = Column(String(100), nullable=True)
    is_mandatory: bool = Column(Integer, default=True)  # 1=mandatory, 0=nice-to-have
    importance_weight: float = Column(Float, default=1.0)

    job_description: Mapped["JobDescription"] = relationship(
        "JobDescription", back_populates="required_skills"
    )

    def __repr__(self) -> str:
        return f"<RequiredSkill skill={self.skill_name!r} mandatory={self.is_mandatory}>"
