"""Tests for cronaudit.profiler."""

import pytest
from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.profiler import (
    ProfileResult,
    _slots_per_day,
    _build_hourly_density,
    profile_jobs,
    format_profile_report,
)


def _make_job(expr: str, command: str = "cmd") -> CronJob:
    job = CronJob.__new__(CronJob)
    job.expression = expr
    job.command = command
    job.name = command
    job.schedule = parse_cron_expression(expr)
    return job


def test_slots_per_day_every_minute():
    job = _make_job("* * * * *")
    assert _slots_per_day(job) == 1440


def test_slots_per_day_hourly():
    job = _make_job("0 * * * *")
    assert _slots_per_day(job) == 24


def test_slots_per_day_daily():
    job = _make_job("0 0 * * *")
    assert _slots_per_day(job) == 1


def test_slots_per_day_twice_daily():
    job = _make_job("0 6,18 * * *")
    assert _slots_per_day(job) == 2


def test_build_hourly_density_single_job():
    job = _make_job("0 * * * *")  # runs once per hour
    density = _build_hourly_density([job])
    assert len(density) == 24
    assert all(v == 1 for v in density.values())


def test_build_hourly_density_two_jobs_same_hour():
    job_a = _make_job("0 3 * * *")
    job_b = _make_job("30 3 * * *")
    density = _build_hourly_density([job_a, job_b])
    assert density[3] == 2
    assert density[4] == 0


def test_profile_jobs_empty_returns_empty():
    assert profile_jobs([]) == []


def test_profile_jobs_returns_one_result_per_job():
    jobs = [_make_job("0 * * * *", "job1"), _make_job("30 * * * *", "job2")]
    results = profile_jobs(jobs)
    assert len(results) == 2


def test_profile_jobs_contention_score_between_0_and_1():
    jobs = [_make_job("* * * * *", "heavy"), _make_job("0 0 * * *", "light")]
    results = profile_jobs(jobs)
    for r in results:
        assert 0.0 <= r.contention_score <= 1.0


def test_profile_jobs_sorted_by_contention_descending():
    jobs = [
        _make_job("0 0 * * *", "rare"),
        _make_job("* * * * *", "frequent"),
    ]
    results = profile_jobs(jobs)
    scores = [r.contention_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_profile_result_str_contains_name():
    job = _make_job("0 * * * *", "myjob")
    result = ProfileResult(job=job, slots_per_day=24, contention_score=0.5, peak_hours=[3, 9])
    assert "myjob" in str(result)


def test_profile_result_str_contains_slots():
    job = _make_job("0 * * * *", "myjob")
    result = ProfileResult(job=job, slots_per_day=24, contention_score=0.5, peak_hours=[])
    assert "24" in str(result)


def test_format_profile_report_empty():
    assert format_profile_report([]) == "No jobs to profile."


def test_format_profile_report_contains_header():
    job = _make_job("0 * * * *", "j1")
    results = profile_jobs([job])
    report = format_profile_report(results)
    assert "Profile Report" in report


def test_format_profile_report_contains_job_name():
    job = _make_job("0 * * * *", "my_hourly_job")
    results = profile_jobs([job])
    report = format_profile_report(results)
    assert "my_hourly_job" in report
