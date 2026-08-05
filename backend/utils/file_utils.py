"""
File utility functions — secure filename sanitization, hash computation,
path traversal prevention, and upload path management.
"""

from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from pathlib import Path
from typing import BinaryIO

from utils.logger import get_logger

logger = get_logger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an uploaded filename to prevent path traversal and injection attacks.

    - Strips directory components
    - Normalizes unicode characters
    - Replaces unsafe characters with underscores
    - Limits length to 255 characters

    Args:
        filename: The raw filename from the upload.

    Returns:
        str: A safe, sanitized filename.

    Raises:
        ValueError: If the filename is empty after sanitization.
    """
    if not filename:
        raise ValueError("Filename cannot be empty")

    # Normalize unicode (NFKD form) and encode to ASCII, ignoring non-ASCII
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    # Strip any directory components (prevent path traversal)
    filename = os.path.basename(filename)
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")

    # Replace whitespace and unsafe characters with underscores
    filename = re.sub(r"[^\w\.\-]", "_", filename)

    # Collapse multiple underscores
    filename = re.sub(r"_+", "_", filename)

    # Strip leading/trailing underscores and dots
    filename = filename.strip("._")

    # Enforce length limit (preserve extension)
    if len(filename) > 255:
        stem, ext = os.path.splitext(filename)
        filename = stem[: 255 - len(ext)] + ext

    if not filename:
        raise ValueError("Filename is empty after sanitization")

    return filename


def compute_file_hash(file_content: bytes) -> str:
    """
    Compute the SHA-256 hash of file content for duplicate detection.

    Args:
        file_content: Raw bytes of the file.

    Returns:
        str: Hexadecimal SHA-256 digest.
    """
    return hashlib.sha256(file_content).hexdigest()


def compute_file_hash_from_stream(stream: BinaryIO, chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 hash by reading a file stream in chunks.
    Efficient for large files — does not load entire file into memory.

    Args:
        stream:     File-like object opened in binary mode.
        chunk_size: Number of bytes to read at a time.

    Returns:
        str: Hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()
    stream.seek(0)
    while chunk := stream.read(chunk_size):
        hasher.update(chunk)
    stream.seek(0)
    return hasher.hexdigest()


def safe_path_join(base_dir: Path, *parts: str) -> Path:
    """
    Safely join path components, raising an error if the result escapes base_dir.
    Prevents directory traversal attacks.

    Args:
        base_dir: The allowed root directory.
        *parts:   Path components to join.

    Returns:
        Path: Safe resolved path inside base_dir.

    Raises:
        ValueError: If the resolved path is outside base_dir.
    """
    base_resolved = base_dir.resolve()
    target = (base_dir / Path(*parts)).resolve()

    if not str(target).startswith(str(base_resolved)):
        raise ValueError(
            f"Path traversal detected: '{target}' is outside base directory '{base_resolved}'"
        )

    return target


def get_file_extension(filename: str) -> str:
    """
    Extract the lowercase file extension without the leading dot.

    Args:
        filename: Filename with extension.

    Returns:
        str: Lowercase extension (e.g., 'pdf', 'docx').
    """
    return Path(filename).suffix.lstrip(".").lower()


def format_file_size(size_bytes: int) -> str:
    """
    Convert a byte count to a human-readable string.

    Args:
        size_bytes: File size in bytes.

    Returns:
        str: Human-readable size (e.g., '2.4 MB').
    """
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
