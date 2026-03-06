from __future__ import annotations
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".job-radar"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: dict = {
    "repos": [
        {"owner_repo": "speedyapply/2026-AI-College-Jobs",     "file_path": "NEW_GRAD_USA.md"},
        {"owner_repo": "speedyapply/2026-SWE-College-Jobs",    "file_path": "NEW_GRAD_USA.md"},
        {"owner_repo": "SimplifyJobs/New-Grad-Positions",      "file_path": "README.md"},
        {"owner_repo": "vanshb03/New-Grad-2026",               "file_path": "README.md"},
        {"owner_repo": "jobright-ai/Daily-H1B-Jobs-In-Tech",   "file_path": "README.md"},
        {"owner_repo": "skillsire/Daily-H1B-Jobs",             "file_path": "README.md"},
    ],
    "include_keywords": [
        "software engineer", "software developer", "swe", "sde",
        "ai engineer", "ml engineer", "machine learning", "data engineer",
        "data scientist", "full stack", "fullstack", "full-stack",
        "backend engineer", "backend developer", "frontend engineer",
        "frontend developer", "cloud engineer", "platform engineer",
        "site reliability", "sre", "infrastructure engineer",
        "genai", "generative ai", "llm", "nlp", "deep learning",
        "computer vision", "ai/ml", "ai engineer", "ml ops", "mlops",
        "devops engineer", "dev ops engineer", "systems engineer",
        "solutions engineer", "solutions architect",
        "data analyst", "analytics engineer", "data science",
        "embedded engineer", "firmware engineer",
        "security engineer", "cybersecurity engineer",
        "network engineer", "automation engineer",
        "python developer", "java developer", "react developer",
        "developer", "programmer", "coder",
        "new grad", "new graduate", "entry level", "entry-level",
    ],
    "exclude_keywords": [
        "phd required", "phd only",
        "security clearance", "ts/sci",
        "us citizen only", "us citizens only",
        "no sponsorship", "not eligible for sponsorship",
        "does not provide immigration", "unauthorized workers",
        "must be a u.s. citizen", "clearance required",
        "7+ years", "10+ years",
    ],
}


def load_config() -> dict:
    """Load config from ~/.job-radar/config.json, creating it with defaults if missing."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
    with CONFIG_FILE.open() as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
