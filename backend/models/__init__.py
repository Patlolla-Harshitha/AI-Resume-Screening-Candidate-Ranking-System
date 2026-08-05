"""Models package — import all models here for Alembic auto-discovery."""

from models.user import User
from models.candidate import (
    Candidate,
    Resume,
    Education,
    Experience,
    Certification,
    Project,
    CandidateSkill,
)
from models.job import JobDescription, RequiredSkill
from models.scoring import Score, Ranking, SkillGap, ATSFeedback
from models.audit import AuditLog, ProcessingHistory
from models.report import Report

__all__ = [
    "User",
    "Candidate",
    "Resume",
    "Education",
    "Experience",
    "Certification",
    "Project",
    "CandidateSkill",
    "JobDescription",
    "RequiredSkill",
    "Score",
    "Ranking",
    "SkillGap",
    "ATSFeedback",
    "AuditLog",
    "ProcessingHistory",
    "Report",
]
