from __future__ import annotations
import re
import logging

logger = logging.getLogger(__name__)

_STRIP_SUFFIXES = re.compile(
    r"\b(inc|llc|corp|corporation|ltd|limited|co|company|group|technologies|technology|tech|labs|lab|software)\b\.?",
    re.IGNORECASE,
)


def normalize_company(name: str) -> str:
    name = name.strip().lower()
    name = _STRIP_SUFFIXES.sub("", name)
    name = re.sub(r"[.,]", "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def make_dedup_key(job: dict) -> str:
    company = normalize_company(job.get("company", ""))
    role = job.get("role", "").strip().lower()
    return f"{company}|{role}"


def dedup_jobs(jobs: list[dict]) -> list[dict]:
    """Deduplicate within a single batch. Prefer entries with a URL."""
    seen: dict[str, dict] = {}
    for job in jobs:
        key = make_dedup_key(job)
        if key not in seen:
            seen[key] = job
        else:
            if job.get("url") and not seen[key].get("url"):
                seen[key] = job
    return list(seen.values())


def filter_seen(jobs: list[dict], seen_keys: set[str]) -> list[dict]:
    """Remove jobs whose dedup key is already in seen_keys."""
    return [job for job in jobs if make_dedup_key(job) not in seen_keys]
