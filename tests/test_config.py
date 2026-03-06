import json, os, tempfile, pytest
from unittest.mock import patch

def test_default_config_has_repos():
    from job_radar.config import DEFAULT_CONFIG
    assert len(DEFAULT_CONFIG["repos"]) >= 6
    assert all("owner_repo" in r and "file_path" in r for r in DEFAULT_CONFIG["repos"])

def test_default_config_has_keywords():
    from job_radar.config import DEFAULT_CONFIG
    assert len(DEFAULT_CONFIG["include_keywords"]) > 5
    assert len(DEFAULT_CONFIG["exclude_keywords"]) > 5

def test_load_config_returns_dict(tmp_path):
    config_dir = tmp_path / ".job-radar"
    with patch("job_radar.config.CONFIG_DIR", config_dir):
        with patch("job_radar.config.CONFIG_FILE", config_dir / "config.json"):
            from job_radar.config import load_config
            cfg = load_config()
    assert "repos" in cfg
    assert "include_keywords" in cfg
