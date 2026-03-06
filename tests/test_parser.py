from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_diff_extracts_added_rows():
    from job_radar.parser import parse_diff
    diff = (FIXTURES / "sample_diff.txt").read_text()
    jobs = parse_diff(diff, source_repo="SimplifyJobs/New-Grad-Positions")
    assert len(jobs) == 3


def test_parse_diff_extracts_company_and_role():
    from job_radar.parser import parse_diff
    diff = (FIXTURES / "sample_diff.txt").read_text()
    jobs = parse_diff(diff, source_repo="SimplifyJobs/New-Grad-Positions")
    companies = [j["company"] for j in jobs]
    assert "Amazon" in companies
    assert "Google" in companies


def test_parse_diff_extracts_url():
    from job_radar.parser import parse_diff
    diff = (FIXTURES / "sample_diff.txt").read_text()
    jobs = parse_diff(diff, source_repo="SimplifyJobs/New-Grad-Positions")
    amazon = next(j for j in jobs if j["company"] == "Amazon")
    assert "amazon.jobs" in amazon["url"]


def test_parse_diff_handles_missing_url():
    from job_radar.parser import parse_diff
    diff = (FIXTURES / "sample_diff.txt").read_text()
    jobs = parse_diff(diff, source_repo="SimplifyJobs/New-Grad-Positions")
    meta = next(j for j in jobs if j["company"] == "Meta")
    assert meta["url"] == ""


def test_parse_diff_skips_non_added_lines():
    from job_radar.parser import parse_diff
    diff = (FIXTURES / "sample_diff.txt").read_text()
    jobs = parse_diff(diff, source_repo="test")
    companies = [j["company"] for j in jobs]
    assert "Microsoft" not in companies


def test_parse_diff_empty_returns_empty():
    from job_radar.parser import parse_diff
    assert parse_diff("", "test") == []
