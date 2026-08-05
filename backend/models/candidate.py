"""
Candidate and Resume ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, JSON, Index
)
from sqlalchemy.orm import relationship, Mapped

from database.base import Base


class Candidate(Base):
    """
    Represents a job applicant whose resume has been uploaded and parsed.
    One candidate can have multiple resumes (e.g., updated versions).
    """

    __tablename__ = "candidates"
    __table_args__ = (
        Index("ix_candidates_email", "email"),
        Index("ix_candidates_name", "full_name"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: str = Column(String(255), nullable=False, index=True)
    email: str = Column(String(255), nullable=True, index=True)
    phone: str = Column(String(50), nullable=True)
    address: str = Column(Text, nullable=True)
    linkedin_url: str = Column(String(500), nullable=True)
    github_url: str = Column(String(500), nullable=True)
    portfolio_url: str = Column(String(500), nullable=True)

    # Summary extracted from resume
    summary: str = Column(Text, nullable=True)

    # Years of experience (computed from experience sections)
    years_of_experience: float = Column(Float, default=0.0)

    # Education level (highest degree detected)
    highest_education: str = Column(String(100), nullable=True)

    # File hash for duplicate detection
    file_hash: str = Column(String(64), nullable=True, index=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    resumes: Mapped[List["Resume"]] = relationship(
        "Resume", back_populates="candidate", cascade="all, delete-orphan"
    )
    skills: Mapped[List["CandidateSkill"]] = relationship(
        "CandidateSkill", back_populates="candidate", cascade="all, delete-orphan"
    )
    educations: Mapped[List["Education"]] = relationship(
        "Education", back_populates="candidate", cascade="all, delete-orphan"
    )
    experiences: Mapped[List["Experience"]] = relationship(
        "Experience", back_populates="candidate", cascade="all, delete-orphan"
    )
    certifications: Mapped[List["Certification"]] = relationship(
        "Certification", back_populates="candidate", cascade="all, delete-orphan"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="candidate", cascade="all, delete-orphan"
    )
    rankings: Mapped[List["Ranking"]] = relationship(
        "Ranking", back_populates="candidate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Candidate name={self.full_name!r} email={self.email!r}>"


class Resume(Base):
    """Stores the uploaded resume file metadata and raw extracted text."""

    __tablename__ = "resumes"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: str = Column(String(500), nullable=False)
    stored_filename: str = Column(String(500), nullable=False)
    file_path: str = Column(String(1000), nullable=False)
    file_size_bytes: int = Column(Integer, nullable=False)
    file_type: str = Column(String(10), nullable=False)  # 'pdf' or 'docx'
    file_hash: str = Column(String(64), nullable=False, unique=True, index=True)
    raw_text: str = Column(Text, nullable=True)
    parsed_data: dict = Column(JSON, nullable=True)   # Full structured parse output
    is_processed: bool = Column(Boolean, default=False, nullable=False)
    processing_time_ms: int = Column(Integer, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="resumes")

    def __repr__(self) -> str:
        return f"<Resume file={self.original_filename!r} candidate={self.candidate_id!r}>"


class Education(Base):
    """A single education entry extracted from a resume."""

    __tablename__ = "educations"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    degree: str = Column(String(255), nullable=True)
    field_of_study: str = Column(String(255), nullable=True)
    institution: str = Column(String(500), nullable=True)
    start_year: int = Column(Integer, nullable=True)
    end_year: int = Column(Integer, nullable=True)
    gpa: float = Column(Float, nullable=True)
    is_current: bool = Column(Boolean, default=False)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="educations")


class Experience(Base):
    """A single work experience entry extracted from a resume."""

    __tablename__ = "experiences"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_title: str = Column(String(255), nullable=True)
    company: str = Column(String(500), nullable=True)
    location: str = Column(String(255), nullable=True)
    start_date: str = Column(String(50), nullable=True)
    end_date: str = Column(String(50), nullable=True)
    is_current: bool = Column(Boolean, default=False)
    duration_months: int = Column(Integer, nullable=True)
    description: str = Column(Text, nullable=True)
    responsibilities: list = Column(JSON, nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="experiences")


class Certification(Base):
    """A certification or license from a resume."""

    __tablename__ = "certifications"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: str = Column(String(500), nullable=False)
    issuer: str = Column(String(500), nullable=True)
    issue_date: str = Column(String(50), nullable=True)
    expiry_date: str = Column(String(50), nullable=True)
    credential_id: str = Column(String(200), nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="certifications")


class Project(Base):
    """A project from a resume."""

    __tablename__ = "projects"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: str = Column(String(500), nullable=False)
    description: str = Column(Text, nullable=True)
    technologies: list = Column(JSON, nullable=True)
    url: str = Column(String(500), nullable=True)
    start_date: str = Column(String(50), nullable=True)
    end_date: str = Column(String(50), nullable=True)

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="projects")


class CandidateSkill(Base):
    """Junction table mapping candidates to skills with proficiency levels."""

    __tablename__ = "candidate_skills"
    __table_args__ = (
        Index("ix_candidate_skills_candidate", "candidate_id"),
        Index("ix_candidate_skills_skill", "skill_name"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: str = Column(String(200), nullable=False)
    skill_category: str = Column(String(100), nullable=True)  # e.g., "Programming Language"
    proficiency: str = Column(String(50), nullable=True)       # e.g., "Intermediate"

    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="skills")

    def __repr__(self) -> str:
        return f"<CandidateSkill skill={self.skill_name!r} category={self.skill_category!r}>"
