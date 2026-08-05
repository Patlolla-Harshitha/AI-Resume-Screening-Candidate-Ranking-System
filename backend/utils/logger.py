"""
Centralised logging utility with rotating file handler.
Provides a consistent logger factory for all backend modules.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Singleton flag to prevent duplicate handler registration
_configured: bool = False


def setup_logging(
    log_dir: str | Path = "backend/logs",
    log_level: str = "INFO",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """
    Configure the root logger with both console and rotating file handlers.
    Call once at application startup. Safe to call multiple times (idempotent).

    Args:
        log_dir:      Directory where log files are stored.
        log_level:    Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_bytes:    Maximum size of each log file before rotation.
        backup_count: Number of backup log files to keep.
    """
    global _configured
    if _configured:
        return

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Determine numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers to avoid duplicate output
    root_logger.handlers.clear()

    # Formatter: timestamp | level | module | message
    fmt = "%(asctime)s | %(levelname)-8s | %(name)-40s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=date_fmt)

    # --- Console handler (stdout) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- Rotating file handler (general app log) ---
    app_log_file = log_dir / "app.log"
    file_handler = RotatingFileHandler(
        filename=str(app_log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # --- Rotating file handler (error-only log) ---
    error_log_file = log_dir / "error.log"
    error_handler = RotatingFileHandler(
        filename=str(error_log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # --- Rotating file handler (AI inference log) ---
    ai_log_file = log_dir / "inference.log"
    ai_handler = RotatingFileHandler(
        filename=str(ai_log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    ai_handler.setLevel(logging.DEBUG)
    ai_handler.setFormatter(formatter)
    # Only attach to specific loggers
    ai_logger = logging.getLogger("ai")
    ai_logger.addHandler(ai_handler)

    # Suppress noisy third-party loggers in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if log_level == "DEBUG" else logging.WARNING
    )
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger, initialising the logging system with defaults
    if it has not yet been configured.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        logging.Logger: Configured logger instance.
    """
    if not _configured:
        try:
            from config import settings
            setup_logging(
                log_dir=settings.log_path,
                log_level=settings.LOG_LEVEL,
                max_bytes=settings.LOG_MAX_BYTES,
                backup_count=settings.LOG_BACKUP_COUNT,
            )
        except Exception:
            # Fallback if config not available (e.g., during import)
            setup_logging()

    return logging.getLogger(name)
