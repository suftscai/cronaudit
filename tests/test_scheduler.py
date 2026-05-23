"""Tests for cronaudit.scheduler."""

from datetime import datetime

import pytest

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.scheduler import NextRun, next_run, next_runs


def _make_job(expr: str, name: str = "job") -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = name
    job.expression = expr
    job.schedule = parse_cron_expression(expr)
    return job


_BASE = datetime(2024, 1, 15, 12, 0)  # Monday noon


def test_exact_minute_match():
    job = _make_job("0 12 15 1 *")  # 12:00 on Jan 15
    nr = next_run(job, after=_BASE)
    assert nr.run_at == _BASE


def test_next_minute_when_current_does_not_match():
    job = _make_job("5 12 * * *")  # 12:05 every day
    nr = next_run(job, after=_BASE)  # base is 12:00
    assert nr.run_at == datetime(2024, 1, 15, 12, 5)


def test_next_hour_rollover():
    job = _make_job("0 13 * * *")  # 13:00 every day
    nr = next_run(job, after=_BASE)
    assert nr.run_at == datetime(2024, 1, 15, 13, 0)


def test_next_day_rollover():
    job = _make_job("0 8 * * *")  # 08:00 every day
    nr = next_run(job, after=_BASE)  # base is 12:00, so tomorrow
    assert nr.run_at == datetime(2024, 1, 16, 8, 0)


def test_wildcard_every_minute_returns_same_slot():
    job = _make_job("* * * * *")
    nr = next_run(job, after=_BASE)
    assert nr.run_at == _BASE


def test_next_run_returns_nextruns_instance():
    job = _make_job("* * * * *")
    result = next_run(job, after=_BASE)
    assert isinstance(result, NextRun)
    assert result.job is job


def test_next_runs_returns_sorted_list():
    j1 = _make_job("30 14 * * *", "afternoon")
    j2 = _make_job("0 9 * * *", "morning")
    results = next_runs([j1, j2], after=_BASE, count=2)
    assert len(results) == 2
    assert results[0].run_at <= results[1].run_at


def test_next_runs_respects_count():
    job = _make_job("* * * * *")
    results = next_runs([job], after=_BASE, count=3)
    assert len(results) == 3


def test_impossible_schedule_raises():
    # Feb 30 never exists
    job = _make_job("0 0 30 2 *")
    with pytest.raises(ValueError, match="No execution time found"):
        next_run(job, after=datetime(2024, 3, 1, 0, 0))
