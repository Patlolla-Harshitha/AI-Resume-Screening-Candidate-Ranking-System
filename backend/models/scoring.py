"""
Scoring, Ranking, and Skill Gap ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON, Index
from sqlalchemy.orm import relationship, Mapped

from database.base import Base


class Score(Base):
    """
    Explainable AI score for a candidate against a specific job description.
    Stores the 100-point breakdown across all scoring dimensions.
    """

    __tablename__ = "scores"
    __table_args__ = (
        Index("ix_scores_candidate_job", "candidate_id", "job_description_id"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_description_id: str = Column(
        String(36),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Overall score (0–100)
    overall_score: float = Column(Float, nullable=False, default=0.0)

    # Component scores (max values defined by weights in config)
    skill_match_score: float = Column(Float, nullable=False, default=0.0)   # /40
    experience_score: float = Column(Float, nullable=False, default=0.0)    # /20
    education_score: float = Column(Float, nullable=False, default=0.0)     # /15
    projects_score: float = Column(Float, nullable=False, default=0.0)      # /15
    certifications_score: float = Column(Float, nullable=False, default=0.0)  # /10

    # Semantic similarity from Sentence Transformers (0–1)
    semantic_similarity: float = Column(Float, nullable=True)

    # Human-readable explanation of the score
    reasoning: str = Column(Text, nullable=True)

    # JSON breakdown for detailed display
    score_breakdown: dict = Column(JSON, nullable=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate")
    job_description: Mapped["JobDescription"] = relationship("JobDescription")

    def __repr__(self) -> str:
        return (
            f"<Score candidate={self.candidate_id!r} "
            f"job={self.job_description_id!r} overall={self.overall_score:.1f}>"
        )


class Ranking(Base):
    """
    The ranked position of a candidate for a specific job description.
    Updated every time ranking is re-run.
    """

    __tablename__ = "rankings"
    __table_args__ = (
        Index("ix_rankings_job_rank", "job_description_id", "rank"),
    )

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_description_id: str = Column(
        String(36),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rank: int = Column(Integer, nullable=False)
    overall_score: float = Column(Float, nullable=False)
    semantic_similarity: float = Column(Float, nullable=True)

    # Recommendation label
    recommendation: str = Column(String(50), nullable=False)  # Excellent/Good/Moderate/Poor Fit

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="rankings")
    job_description: Mapped["JobDescription"] = relationship(
        "JobDescription", back_populates="rankings"
    )

    def __repr__(self) -> str:
        return (
            f"<Ranking rank={self.rank} candidate={self.candidate_id!r} "
            f"recommendation={self.recommendation!r}>"
        )


class SkillGap(Base):
    """
    Skill gap analysis result for a candidate against a job description.
    """

    __tablename__ = "skill_gaps"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_description_id: str = Column(
        String(36),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Lists stored as JSON arrays
    matching_skills: list = Column(JSON, nullable=True)
    missing_skills: list = Column(JSON, nullable=True)
    extra_skills: list = Column(JSON, nullable=True)
    suggested_skills: list = Column(JSON, nullable=True)

    # Percentage of required skills the candidate has
    skill_coverage_percentage: float = Column(Float, nullable=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)


class ATSFeedback(Base):
    """ATS compatibility analysis result for a candidate's resume."""

    __tablename__ = "ats_feedback"

    id: str = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: str = Column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_description_id: str = Column(
        String(36),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    ats_score: float = Column(Float, nullable=False, default=0.0)
    resume_strength: str = Column(String(50), nullable=True)

    missing_keywords: list = Column(JSON, nullable=True)
    formatting_suggestions: list = Column(JSON, nullable=True)
    weak_sections: list = Column(JSON, nullable=True)
    project_improvements: list = Column(JSON, nullable=True)
    certification_suggestions: list = Column(JSON, nullable=True)
    experience_improvements: list = Column(JSON, nullable=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
