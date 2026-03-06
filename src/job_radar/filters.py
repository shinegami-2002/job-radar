from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


def _haystack(job: dict) -> str:
    """Build a single lowercase string from all searchable job fields."""
    parts = [
        job.get("company", ""),
        job.get("role", ""),
        job.get("location", ""),
        job.get("raw", ""),
    ]
    return " ".join(parts).lower()


def should_include(job: dict, include_keywords: list[str], exclude_keywords: list[str]) -> bool:
    text = _haystack(job)
    for kw in exclude_keywords:
        if kw.lower() in text:
            return False
    for kw in include_keywords:
        if kw.lower() in text:
            return True
    return False


def filter_jobs(
    jobs: list[dict],
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> list[dict]:
    return [j for j in jobs if should_include(j, include_keywords, exclude_keywords)]
