"""
Input validators for file uploads and request data.
"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Maximum filename display length in error messages
_MAX_DISPLAY_LEN = 100


def validate_resume_file(file: UploadFile) -> None:
    """
    Validate an uploaded resume file for type, size, and integrity.

    Args:
        file: The uploaded file from FastAPI.

    Raises:
        HTTPException 400: If the file type is not allowed.
        HTTPException 413: If the file exceeds the size limit.
        HTTPException 400: If the filename is missing or malformed.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file has no filename.",
        )

    # Check extension
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '.{ext}' is not allowed. "
                f"Accepted types: {', '.join(settings.allowed_extensions_list)}"
            ),
        )

    # Check content type (secondary validation)
    allowed_content_types = {
        "pdf": ["application/pdf"],
        "docx": [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "application/octet-stream",
        ],
    }
    if file.content_type and ext in allowed_content_types:
        if file.content_type not in allowed_content_types[ext]:
            logger.warning(
                "Unexpected content type '%s' for extension '.%s' — proceeding with caution",
                file.content_type,
                ext,
            )


def validate_file_size(content: bytes, filename: str = "file") -> None:
    """
    Validate that file content does not exceed the configured size limit.

    Args:
        content:  Raw file bytes.
        filename: Filename for error messages.

    Raises:
        HTTPException 413: If the file is too large.
    """
    size = len(content)
    if size > settings.max_file_size_bytes:
        display_name = filename[:_MAX_DISPLAY_LEN]
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File '{display_name}' is {size / 1024 / 1024:.1f} MB, "
                f"which exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB."
            ),
        )


def validate_text_input(text: str, field_name: str = "text", min_length: int = 10) -> None:
    """
    Validate that a text input meets minimum length requirements.

    Args:
        text:       Input text to validate.
        field_name: Name of the field (for error messages).
        min_length: Minimum required character count.

    Raises:
        HTTPException 400: If the text is too short.
    """
    if not text or len(text.strip()) < min_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"'{field_name}' must be at least {min_length} characters long. "
                f"Received {len(text.strip()) if text else 0} characters."
            ),
        )
