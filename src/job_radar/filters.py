from __future__ import annotations
import logging
import re

logger = logging.getLogger(__name__)

# These are checked against the ROLE TITLE only (word-boundary matching)
# to avoid false positives like "internal" matching "intern"
ROLE_EXCLUDE_PATTERNS = [
    r"\bintern\b", r"\binternship\b", r"\bco-op\b", r"\bcoop\b",
    r"\bsenior\b", r"\bsr\.?\b", r"\bstaff\b", r"\bprincipal\b",
    r"\bdirector\b", r"\bmanager\b", r"\blead\b",
]

_role_exclude_re = re.compile("|".join(ROLE_EXCLUDE_PATTERNS), re.IGNORECASE)


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
    role = job.get("role", "").lower()
    text = _haystack(job)

    # 1. Role-title word-boundary excludes (intern, senior, etc.)
    if _role_exclude_re.search(role):
        return False

    # 2. Global text excludes (sponsorship, clearance, years of exp)
    for kw in exclude_keywords:
        if kw.lower() in text:
            return False

    # 3. Include keywords match against role title only
    for kw in include_keywords:
        if kw.lower() in role:
            return True

    return False


def filter_jobs(
    jobs: list[dict],
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> list[dict]:
    return [j for j in jobs if should_include(j, include_keywords, exclude_keywords)]
