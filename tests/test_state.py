import json
from pathlib import Path
from unittest.mock import patch


def test_get_sha_returns_none_when_missing(tmp_path):
    with patch("job_radar.state.STATE_DIR", tmp_path):
        with patch("job_radar.state.STATE_FILE", tmp_path / "state.json"):
            from job_radar.state import get_sha
            assert get_sha("owner/repo", "README.md") is None


def test_set_and_get_sha(tmp_path):
    with patch("job_radar.state.STATE_DIR", tmp_path):
        with patch("job_radar.state.STATE_FILE", tmp_path / "state.json"):
            from job_radar.state import set_sha, get_sha
            set_sha("owner/repo", "README.md", "abc123")
            assert get_sha("owner/repo", "README.md") == "abc123"


def test_seen_jobs_roundtrip(tmp_path):
    with patch("job_radar.state.STATE_DIR", tmp_path):
        with patch("job_radar.state.SEEN_FILE", tmp_path / "seen.json"):
            from job_radar.state import add_seen_job, is_seen_job
            add_seen_job("amazon|swe new grad", "2026-03-05")
            assert is_seen_job("amazon|swe new grad")
            assert not is_seen_job("google|ml engineer")
