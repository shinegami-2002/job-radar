import pytest


def test_normalize_company():
    from job_radar.dedup import normalize_company
    assert normalize_company("Amazon Inc.") == "amazon"
    assert normalize_company("Google LLC") == "google"
    assert normalize_company("Meta Platforms Corp") == "meta platforms"
    assert normalize_company("  Stripe  ") == "stripe"


def test_dedup_key_format():
    from job_radar.dedup import make_dedup_key
    job = {"company": "Amazon Inc.", "role": "SWE New Grad 2026"}
    key = make_dedup_key(job)
    assert key == "amazon|swe new grad 2026"


def test_dedup_within_run_keeps_one():
    from job_radar.dedup import dedup_jobs
    jobs = [
        {"company": "Amazon", "role": "SWE New Grad", "url": "", "location": "NY", "source_repo": "a"},
        {"company": "Amazon Inc.", "role": "SWE New Grad", "url": "https://x.com", "location": "NY", "source_repo": "b"},
    ]
    result = dedup_jobs(jobs)
    assert len(result) == 1
    assert result[0]["url"] == "https://x.com"


def test_dedup_keeps_distinct_jobs():
    from job_radar.dedup import dedup_jobs
    jobs = [
        {"company": "Amazon", "role": "SWE New Grad", "url": "", "location": "NY", "source_repo": "a"},
        {"company": "Google", "role": "ML Engineer", "url": "https://x.com", "location": "CA", "source_repo": "b"},
    ]
    result = dedup_jobs(jobs)
    assert len(result) == 2


def test_filter_already_seen():
    from job_radar.dedup import filter_seen
    jobs = [
        {"company": "Amazon", "role": "SWE New Grad", "url": "", "location": "NY", "source_repo": "a"},
        {"company": "Google", "role": "ML Engineer", "url": "", "location": "CA", "source_repo": "b"},
    ]
    seen_keys = {"amazon|swe new grad"}
    new_jobs = filter_seen(jobs, seen_keys)
    assert len(new_jobs) == 1
    assert new_jobs[0]["company"] == "Google"
