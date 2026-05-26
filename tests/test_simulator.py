"""Tests for cronaudit.simulator."""

from datetime import datetime

import pytest

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.simulator import (
    SimulatedRun,
    SimulationResult,
    format_simulation_report,
    simulate,
)


def _make_job(name: str, expression: str) -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = name
    job.schedule = parse_cron_expression(expression)
    job.raw = expression
    return job


@pytest.fixture
def every_minute_job():
    return _make_job("tick", "* * * * *")


@pytest.fixture
def hourly_job():
    return _make_job("hourly", "0 * * * *")


def test_simulated_run_str_contains_job_name(every_minute_job):
    ts = datetime(2024, 1, 1, 12, 0)
    run = SimulatedRun(job=every_minute_job, timestamp=ts)
    assert "tick" in str(run)


def test_simulated_run_str_contains_timestamp(every_minute_job):
    ts = datetime(2024, 1, 1, 12, 0)
    run = SimulatedRun(job=every_minute_job, timestamp=ts)
    assert "2024-01-01 12:00" in str(run)


def test_simulation_result_str_contains_run_count(every_minute_job):
    start = datetime(2024, 1, 1, 0, 0)
    end = datetime(2024, 1, 1, 0, 5)
    result = simulate([every_minute_job], start, end)
    assert str(result.total_runs) in str(result)


def test_every_minute_job_runs_every_minute(every_minute_job):
    start = datetime(2024, 1, 1, 0, 0)
    end = datetime(2024, 1, 1, 0, 5)
    result = simulate([every_minute_job], start, end)
    assert result.total_runs == 5


def test_hourly_job_runs_once_per_hour(hourly_job):
    start = datetime(2024, 1, 1, 0, 0)
    end = datetime(2024, 1, 1, 3, 0)
    result = simulate([hourly_job], start, end)
    assert result.total_runs == 3


def test_no_runs_outside_window(hourly_job):
    start = datetime(2024, 1, 1, 0, 1)
    end = datetime(2024, 1, 1, 0, 59)
    result = simulate([hourly_job], start, end)
    assert result.total_runs == 0


def test_runs_for_job_filters_correctly(every_minute_job, hourly_job):
    start = datetime(2024, 1, 1, 0, 0)
    end = datetime(2024, 1, 1, 0, 5)
    result = simulate([every_minute_job, hourly_job], start, end)
    tick_runs = result.runs_for_job(every_minute_job)
    hourly_runs = result.runs_for_job(hourly_job)
    assert len(tick_runs) == 5
    assert len(hourly_runs) == 1


def test_format_report_contains_window(every_minute_job):
    start = datetime(2024, 1, 1, 6, 0)
    end = datetime(2024, 1, 1, 6, 3)
    result = simulate([every_minute_job], start, end)
    report = format_simulation_report(result)
    assert "2024-01-01 06:00" in report
    assert "2024-01-01 06:03" in report


def test_format_report_no_runs_shows_placeholder():
    start = datetime(2024, 1, 1, 0, 0)
    end = datetime(2024, 1, 1, 0, 0)
    result = SimulationResult(start=start, end=end)
    report = format_simulation_report(result)
    assert "no runs" in report


def test_format_report_lists_run_entries(every_minute_job):
    start = datetime(2024, 1, 1, 0, 0)
    end = datetime(2024, 1, 1, 0, 2)
    result = simulate([every_minute_job], start, end)
    report = format_simulation_report(result)
    assert "tick" in report
