"""Tests for conflict detection logic."""

import pytest
from cronaudit.parser import parse_cron_expression
from cronaudit.conflict import detect_conflicts, Conflict


def _jobs(*expressions_with_names):
    """Helper: list of (name, CronSchedule) from (name, expr) pairs."""
    return [(name, parse_cron_expression(expr)) for name, expr in expressions_with_names]


def test_no_conflict_different_hours():
    jobs = _jobs(("job_a", "0 6 * * *"), ("job_b", "0 7 * * *"))
    assert detect_conflicts(jobs) == []


def test_no_conflict_different_minutes():
    jobs = _jobs(("job_a", "15 6 * * *"), ("job_b", "30 6 * * *"))
    assert detect_conflicts(jobs) == []


def test_exact_same_schedule_conflicts():
    jobs = _jobs(("job_a", "30 6 * * *"), ("job_b", "30 6 * * *"))
    conflicts = detect_conflicts(jobs)
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.job_a == "job_a"
    assert c.job_b == "job_b"
    assert c.overlap_count == 1
    assert c.overlapping_hours == [6]
    assert c.overlapping_minutes == [30]


def test_wildcard_jobs_conflict():
    jobs = _jobs(("job_a", "* * * * *"), ("job_b", "* * * * *"))
    conflicts = detect_conflicts(jobs)
    assert len(conflicts) == 1
    assert conflicts[0].overlap_count == 24 * 60


def test_partial_overlap():
    # job_a runs every 30 min all day; job_b runs at :00 every hour
    jobs = _jobs(("job_a", "0,30 * * * *"), ("job_b", "0 * * * *"))
    conflicts = detect_conflicts(jobs)
    assert len(conflicts) == 1
    assert conflicts[0].overlap_count == 24  # one slot per hour at :00


def test_three_jobs_multiple_conflicts():
    jobs = _jobs(
        ("a", "0 12 * * *"),
        ("b", "0 12 * * *"),
        ("c", "0 12 * * *"),
    )
    conflicts = detect_conflicts(jobs)
    assert len(conflicts) == 3  # a-b, a-c, b-c


def test_conflict_str():
    jobs = _jobs(("alpha", "5 5 * * *"), ("beta", "5 5 * * *"))
    c = detect_conflicts(jobs)[0]
    result = str(c)
    assert "alpha" in result
    assert "beta" in result
    assert "1" in result
