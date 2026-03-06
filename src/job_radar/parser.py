from __future__ import annotations
import re
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
_SEP_ROW_RE = re.compile(r"^\s*\|[-| :]+\|\s*$")
_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def _extract_url(cell: str) -> str:
    m = _LINK_RE.search(cell)
    return m.group(2) if m else ""


def parse_diff(diff_text: str, source_repo: str) -> list[dict]:
    """
    Parse a GitHub unified diff and return job dicts for every ADDED table row.
    Returns list of: {company, role, location, url, source_repo}
    """
    jobs: list[dict] = []
    for raw_line in diff_text.splitlines():
        if not raw_line.startswith("+"):
            continue
        # Strip the leading "+"
        line = raw_line[1:]
        if "|" not in line:
            continue
        # Skip separator rows like |---|---|
        if _SEP_ROW_RE.match(line):
            continue
        # Skip header rows
        if re.search(r"\bCompany\b|\bRole\b|\bApplication\b", line, re.IGNORECASE):
            continue
        # Split into cells
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        try:
            company = cells[0]
            role = cells[1]
            location = cells[2] if len(cells) > 2 else ""
            url_cell = cells[3] if len(cells) > 3 else ""
            url = _extract_url(url_cell)
            if not company or company in ("-", "---"):
                continue
            job = {
                "company": company,
                "role": role,
                "location": location,
                "url": url,
                "source_repo": source_repo,
            }
            date_match = _DATE_RE.search(line)
            if date_match:
                job["date_posted"] = date_match.group(1)
            jobs.append(job)
        except Exception as exc:
            logger.warning("Could not parse row %r: %s", raw_line, exc)
    return jobs


def parse_raw_file(content: str, source_repo: str, max_age_days: int = 1) -> list[dict]:
    """
    Parse a full markdown file (not a diff) and return job dicts for rows
    with a date within the last max_age_days.
    """
    cutoff = date.today() - timedelta(days=max_age_days)
    jobs: list[dict] = []
    for line in content.splitlines():
        if "|" not in line:
            continue
        if _SEP_ROW_RE.match(line):
            continue
        if re.search(r"\bCompany\b|\bRole\b|\bApplication\b", line, re.IGNORECASE):
            continue
        # Check if the row has a date and if it's recent enough
        date_match = _DATE_RE.search(line)
        if date_match:
            try:
                row_date = date.fromisoformat(date_match.group(1))
                if row_date < cutoff:
                    continue
            except ValueError:
                continue
        else:
            # No date found in row -- skip it (can't tell if it's recent)
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        try:
            company = cells[0]
            role = cells[1]
            location = cells[2] if len(cells) > 2 else ""
            url_cell = cells[3] if len(cells) > 3 else ""
            url = _extract_url(url_cell)
            if not company or company in ("-", "---"):
                continue
            jobs.append({
                "company": company,
                "role": role,
                "location": location,
                "url": url,
                "source_repo": source_repo,
                "date_posted": date_match.group(1),
            })
        except Exception as exc:
            logger.warning("Could not parse row %r: %s", line, exc)
    return jobs
