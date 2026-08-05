"""
Text utility functions — cleaning, normalization, and extraction helpers.
Used across parsers and AI modules.
"""

from __future__ import annotations

import re
import unicodedata
from typing import List


def clean_text(text: str) -> str:
    """
    Clean raw text extracted from a resume or job description.

    Operations:
    - Normalize unicode to NFKC form
    - Replace Windows/Mac line endings with Unix
    - Collapse multiple blank lines into a single blank line
    - Strip leading/trailing whitespace

    Args:
        text: Raw extracted text.

    Returns:
        str: Cleaned text.
    """
    if not text:
        return ""

    # Normalize unicode
    text = unicodedata.normalize("NFKC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove null bytes and other control characters (preserve newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces/tabs within a line
    lines = [re.sub(r"[ \t]+", " ", line) for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def normalize_whitespace(text: str) -> str:
    """
    Collapse all whitespace sequences (including newlines) into a single space.
    Useful for embedding generation where whitespace structure is irrelevant.

    Args:
        text: Input text.

    Returns:
        str: Single-line text with normalized whitespace.
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_emails(text: str) -> List[str]:
    """
    Extract all email addresses from text using a robust regex pattern.

    Args:
        text: Input text.

    Returns:
        List[str]: Unique list of email addresses found.
    """
    pattern = r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
    return list(dict.fromkeys(re.findall(pattern, text)))


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text. Handles international formats,
    parentheses, dashes, dots, and spaces.

    Args:
        text: Input text.

    Returns:
        List[str]: Unique list of cleaned phone numbers found.
    """
    pattern = r"(?:\+?\d{1,3}[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
    raw_matches = re.findall(pattern, text)
    # Clean each match: keep only digits and leading +
    cleaned = []
    for match in raw_matches:
        digits = re.sub(r"[^\d+]", "", match)
        if len(digits) >= 10:
            cleaned.append(digits)
    return list(dict.fromkeys(cleaned))


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs (http, https, and www) from text.

    Args:
        text: Input text.

    Returns:
        List[str]: List of found URLs.
    """
    pattern = r"https?://[^\s<>\"]+|www\.[^\s<>\"]+\.[^\s<>\"]{2,}"
    return list(dict.fromkeys(re.findall(pattern, text, re.IGNORECASE)))


def extract_linkedin_url(text: str) -> str | None:
    """
    Extract the first LinkedIn profile URL from text.

    Args:
        text: Input text.

    Returns:
        str | None: LinkedIn URL or None.
    """
    urls = extract_urls(text)
    for url in urls:
        if "linkedin.com" in url.lower():
            return url
    # Fallback: partial pattern
    match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
    return f"https://{match.group()}" if match else None


def extract_github_url(text: str) -> str | None:
    """
    Extract the first GitHub profile URL from text.

    Args:
        text: Input text.

    Returns:
        str | None: GitHub URL or None.
    """
    urls = extract_urls(text)
    for url in urls:
        if "github.com" in url.lower() and "//" in url:
            return url
    match = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
    return f"https://{match.group()}" if match else None


def split_into_sections(text: str) -> dict[str, str]:
    """
    Attempt to split a resume text into named sections based on common headings.
    Returns a dict mapping section name -> section content.

    Args:
        text: Cleaned resume text.

    Returns:
        dict[str, str]: Section name to content mapping.
    """
    section_headers = [
        r"EDUCATION",
        r"EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE|EMPLOYMENT",
        r"SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|COMPETENCIES",
        r"PROJECTS|PERSONAL PROJECTS|ACADEMIC PROJECTS",
        r"CERTIFICATIONS?|LICENSES?|CREDENTIALS?",
        r"ACHIEVEMENTS?|AWARDS?|HONORS?",
        r"LANGUAGES?",
        r"PUBLICATIONS?",
        r"VOLUNTEER",
        r"SUMMARY|OBJECTIVE|PROFILE|ABOUT",
        r"CONTACT",
        r"REFERENCES?",
    ]

    # Build a single pattern that matches any section header
    combined = "|".join(f"(?P<{re.sub(r'[^a-z]', '_', h.split('|')[0].lower())}>{h})" for h in section_headers)
    # Simpler approach: find section boundaries
    header_pattern = re.compile(
        r"^(?:" + "|".join(section_headers) + r")\s*$",
        re.MULTILINE | re.IGNORECASE,
    )

    lines = text.split("\n")
    sections: dict[str, list[str]] = {}
    current_section = "HEADER"
    sections[current_section] = []

    for line in lines:
        if header_pattern.match(line.strip()):
            current_section = line.strip().upper()
            sections[current_section] = []
        else:
            sections.setdefault(current_section, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}


def extract_years(text: str) -> List[int]:
    """
    Extract 4-digit years (1970–2030) from text.

    Args:
        text: Input text.

    Returns:
        List[int]: Sorted list of unique years found.
    """
    pattern = r"\b(19[7-9]\d|20[0-2]\d|2030)\b"
    return sorted(set(int(y) for y in re.findall(pattern, text)))


def calculate_duration_months(start: str, end: str) -> int:
    """
    Calculate the number of months between two date strings.
    Handles formats like "Jan 2020", "2020", "Present", "Current".

    Args:
        start: Start date string.
        end:   End date string.

    Returns:
        int: Approximate number of months (0 if parsing fails).
    """
    import calendar
    from datetime import date

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    def parse_date(s: str) -> date | None:
        s = s.strip().lower()
        if s in ("present", "current", "now", "ongoing"):
            return date.today()
        # Try "Month YYYY"
        m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})", s)
        if m:
            return date(int(m.group(2)), month_map[m.group(1)[:3]], 1)
        # Try "YYYY"
        m = re.search(r"\b(\d{4})\b", s)
        if m:
            return date(int(m.group(1)), 1, 1)
        return None

    start_date = parse_date(start)
    end_date = parse_date(end)

    if start_date and end_date and end_date >= start_date:
        delta = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        return max(0, delta)
    return 0
