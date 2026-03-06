from __future__ import annotations
import re
import logging

logger = logging.getLogger(__name__)

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\)]+)\)")
_SEP_ROW_RE = re.compile(r"^\s*\|[-| :]+\|\s*$")


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
            jobs.append({
                "company": company,
                "role": role,
                "location": location,
                "url": url,
                "source_repo": source_repo,
            })
        except Exception as exc:
            logger.warning("Could not parse row %r: %s", raw_line, exc)
    return jobs
