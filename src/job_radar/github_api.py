from __future__ import annotations
import logging
import os
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
_SESSION: Optional[requests.Session] = None


def _session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
        token = os.getenv("GITHUB_TOKEN")
        if token:
            _SESSION.headers["Authorization"] = f"Bearer {token}"
        _SESSION.headers["Accept"] = "application/vnd.github+json"
        _SESSION.headers["X-GitHub-Api-Version"] = "2022-11-28"
    return _SESSION


def _get_with_retry(url: str, params: dict | None = None, retries: int = 3) -> requests.Response:
    delay = 1
    for attempt in range(retries):
        try:
            resp = _session().get(url, params=params, timeout=15)
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None:
                logger.debug("GitHub rate limit remaining: %s", remaining)
                if int(remaining) < 5:
                    logger.warning("GitHub rate limit nearly exhausted (%s remaining)", remaining)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 404:
                logger.warning("404 for %s -- repo or file may not exist", url)
                raise FileNotFoundError(url)
            if resp.status_code == 403:
                logger.error("GitHub 403 -- rate limited or forbidden: %s", url)
        except (requests.ConnectionError, requests.Timeout) as exc:
            logger.warning("Network error on attempt %d for %s: %s", attempt + 1, url, exc)
        if attempt < retries - 1:
            time.sleep(delay)
            delay *= 2
    raise RuntimeError(f"Failed to fetch {url} after {retries} attempts")


def get_latest_sha(owner_repo: str, file_path: str) -> str:
    """Return the latest commit SHA for a specific file in a repo."""
    url = f"{GITHUB_API}/repos/{owner_repo}/commits"
    params = {"path": file_path, "per_page": 1}
    resp = _get_with_retry(url, params=params)
    commits = resp.json()
    if not commits:
        raise ValueError(f"No commits found for {owner_repo}/{file_path}")
    return commits[0]["sha"]


def get_raw_file(owner_repo: str, file_path: str) -> str:
    """Return the raw content of a file from a repo's default branch."""
    url = f"https://raw.githubusercontent.com/{owner_repo}/HEAD/{file_path}"
    resp = _get_with_retry(url)
    return resp.text


def get_diff(owner_repo: str, old_sha: str, new_sha: str) -> str:
    """Return the unified diff text between two SHAs."""
    url = f"{GITHUB_API}/repos/{owner_repo}/compare/{old_sha}...{new_sha}"
    sess = _session()
    resp = sess.get(
        url,
        headers={**sess.headers, "Accept": "application/vnd.github.diff"},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Compare API returned {resp.status_code} for {url}")
    return resp.text
