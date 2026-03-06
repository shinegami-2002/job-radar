from __future__ import annotations
import json
from datetime import datetime, timedelta
from pathlib import Path

STATE_DIR = Path.home() / ".job-radar"
STATE_FILE = STATE_DIR / "state.json"
SEEN_FILE = STATE_DIR / "seen.json"
UNSENT_FILE = STATE_DIR / "unsent.json"
FINDINGS_FILE = STATE_DIR / "findings.md"


def _load_state() -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {}
    with STATE_FILE.open() as f:
        return json.load(f)


def _save_state(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2))


def get_sha(owner_repo: str, file_path: str) -> str | None:
    state = _load_state()
    return state.get(f"{owner_repo}/{file_path}")


def set_sha(owner_repo: str, file_path: str, sha: str) -> None:
    state = _load_state()
    state[f"{owner_repo}/{file_path}"] = sha
    _save_state(state)


def _load_seen() -> dict:
    """Returns {dedup_key: iso_date_added}."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not SEEN_FILE.exists():
        return {}
    with SEEN_FILE.open() as f:
        return json.load(f)


def _save_seen(data: dict) -> None:
    SEEN_FILE.write_text(json.dumps(data, indent=2))


def is_seen_job(dedup_key: str) -> bool:
    seen = _load_seen()
    return dedup_key in seen


def add_seen_job(dedup_key: str, date_str: str) -> None:
    seen = _load_seen()
    seen[dedup_key] = date_str
    _save_seen(seen)


def prune_seen_jobs(days: int = 30) -> int:
    """Remove entries older than `days` days. Returns count removed."""
    seen = _load_seen()
    cutoff = datetime.now() - timedelta(days=days)
    to_remove = [
        k for k, v in seen.items()
        if datetime.fromisoformat(v) < cutoff
    ]
    for k in to_remove:
        del seen[k]
    _save_seen(seen)
    return len(to_remove)


def load_unsent() -> list[dict]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not UNSENT_FILE.exists():
        return []
    with UNSENT_FILE.open() as f:
        return json.load(f)


def save_unsent(jobs: list[dict]) -> None:
    UNSENT_FILE.write_text(json.dumps(jobs, indent=2))


def append_findings(jobs: list[dict], date_str: str) -> None:
    """Append new jobs to ~/.job-radar/findings.md."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if not FINDINGS_FILE.exists():
        lines.append("# Job Radar Findings\n\n")
    lines.append(f"## {date_str}\n\n")
    lines.append("| Company | Role | Location | Link | Source |\n")
    lines.append("|---------|------|----------|------|--------|\n")
    for j in jobs:
        link = f"[Apply]({j['url']})" if j.get("url") else "N/A"
        lines.append(
            f"| {j['company']} | {j['role']} | {j['location']} | {link} | {j['source_repo']} |\n"
        )
    lines.append("\n")
    with FINDINGS_FILE.open("a") as f:
        f.writelines(lines)
