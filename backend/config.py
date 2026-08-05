"""
AI Resume Screening & Candidate Ranking System — Backend Configuration
=======================================================================
Centralised settings loaded from environment variables using Pydantic Settings.
Follows the 12-factor app methodology.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    APP_NAME: str = "AI Resume Screening System"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production-minimum-32-chars-long"

    # -------------------------------------------------------------------------
    # Server
    # -------------------------------------------------------------------------
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    DATABASE_URL: str = "sqlite:///./resume_screening.db"

    # -------------------------------------------------------------------------
    # JWT
    # -------------------------------------------------------------------------
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production-minimum-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # -------------------------------------------------------------------------
    # Default Admin
    # -------------------------------------------------------------------------
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin@123"
    ADMIN_EMAIL: str = "admin@resumescreening.ai"

    # -------------------------------------------------------------------------
    # File Upload
    # -------------------------------------------------------------------------
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "pdf,docx"
    UPLOAD_DIR: str = "uploads"
    BACKEND_UPLOAD_DIR: str = "backend/uploads"

    # -------------------------------------------------------------------------
    # AI / ML
    # -------------------------------------------------------------------------
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    MODEL_CACHE_DIR: str = ".cache/models"
    EMBEDDING_BATCH_SIZE: int = 32

    # -------------------------------------------------------------------------
    # Scoring Weights
    # -------------------------------------------------------------------------
    WEIGHT_SKILL_MATCH: int = 40
    WEIGHT_EXPERIENCE: int = 20
    WEIGHT_EDUCATION: int = 15
    WEIGHT_PROJECTS: int = 15
    WEIGHT_CERTIFICATIONS: int = 10

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "backend/logs"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # -------------------------------------------------------------------------
    # Reports
    # -------------------------------------------------------------------------
    REPORTS_DIR: str = "reports"

    # -------------------------------------------------------------------------
    # Computed properties
    # -------------------------------------------------------------------------
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Return allowed extensions as a list."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def base_dir(self) -> Path:
        """Return the project base directory (parent of backend/)."""
        return Path(__file__).parent.parent

    @property
    def upload_path(self) -> Path:
        """Return the absolute upload directory path."""
        path = Path(self.BACKEND_UPLOAD_DIR)
        if not path.is_absolute():
            path = self.base_dir / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def reports_path(self) -> Path:
        """Return the absolute reports directory path."""
        path = Path(self.REPORTS_DIR)
        if not path.is_absolute():
            path = self.base_dir / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        """Return the absolute log directory path."""
        path = Path(self.LOG_DIR)
        if not path.is_absolute():
            path = self.base_dir / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("JWT_SECRET_KEY", "SECRET_KEY")
    @classmethod
    def validate_secret_keys(cls, v: str) -> str:
        """Ensure secret keys are sufficiently long in production."""
        if len(v) < 32:
            raise ValueError(
                "Secret keys must be at least 32 characters long for security."
            )
        return v

    @model_validator(mode="after")
    def validate_scoring_weights(self) -> "Settings":
        """Ensure scoring weights sum to 100."""
        total = (
            self.WEIGHT_SKILL_MATCH
            + self.WEIGHT_EXPERIENCE
            + self.WEIGHT_EDUCATION
            + self.WEIGHT_PROJECTS
            + self.WEIGHT_CERTIFICATIONS
        )
        if total != 100:
            raise ValueError(
                f"Scoring weights must sum to 100, but got {total}. "
                f"Check WEIGHT_* environment variables."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()


# Module-level convenience accessor
settings = get_settings()
