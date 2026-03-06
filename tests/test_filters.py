import pytest

INCLUDE_KW = ["software engineer", "ml engineer", "new grad", "entry level", "backend"]
EXCLUDE_KW = ["phd required", "us citizen only", "no sponsorship", "senior staff", "10+ years"]


def test_include_match_keeps_job():
    from job_radar.filters import should_include
    job = {"company": "Acme", "role": "Software Engineer New Grad", "location": "NYC", "url": "", "source_repo": "x"}
    assert should_include(job, INCLUDE_KW, EXCLUDE_KW)


def test_exclude_match_drops_job():
    from job_radar.filters import should_include
    job = {"company": "Acme", "role": "Software Engineer", "location": "NYC", "url": "", "source_repo": "x",
           "raw": "No sponsorship available"}
    assert not should_include(job, INCLUDE_KW, EXCLUDE_KW)


def test_no_include_match_drops_job():
    from job_radar.filters import should_include
    job = {"company": "Acme", "role": "Accountant", "location": "NYC", "url": "", "source_repo": "x"}
    assert not should_include(job, INCLUDE_KW, EXCLUDE_KW)


def test_exclude_in_location_drops_job():
    from job_radar.filters import should_include
    job = {"company": "Acme", "role": "ML Engineer", "location": "US Citizen Only", "url": "", "source_repo": "x"}
    assert not should_include(job, INCLUDE_KW, EXCLUDE_KW)


def test_case_insensitive():
    from job_radar.filters import should_include
    job = {"company": "Acme", "role": "BACKEND ENGINEER", "location": "Remote", "url": "", "source_repo": "x"}
    assert should_include(job, INCLUDE_KW, EXCLUDE_KW)


def test_filter_jobs_list():
    from job_radar.filters import filter_jobs
    jobs = [
        {"company": "A", "role": "New Grad SWE", "location": "NY", "url": "", "source_repo": "x"},
        {"company": "B", "role": "Director of Engineering", "location": "NY", "url": "", "source_repo": "x"},
        {"company": "C", "role": "ML Engineer", "location": "Remote", "url": "http://x", "source_repo": "x"},
    ]
    result = filter_jobs(jobs, INCLUDE_KW, EXCLUDE_KW)
    assert len(result) == 2
    assert all(j["company"] in ("A", "C") for j in result)
