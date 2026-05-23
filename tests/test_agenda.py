"""Tests for cronaudit.agenda."""

from datetime import datetime

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.scheduler import NextRun
from cronaudit.agenda import format_agenda


def _make_job(expr: str, name: str = "job") -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = name
    job.expression = expr
    job.schedule = parse_cron_expression(expr)
    return job


def _make_run(expr: str, name: str, dt: datetime) -> NextRun:
    return NextRun(job=_make_job(expr, name), run_at=dt)


_T1 = datetime(2024, 3, 5, 9, 0)   # Tue
_T2 = datetime(2024, 3, 5, 14, 30)


def test_empty_runs_returns_placeholder():
    result = format_agenda([])
    assert "no upcoming runs" in result


def test_header_contains_time_and_job_labels():
    runs = [_make_run("0 9 * * *", "backup", _T1)]
    result = format_agenda(runs)
    assert "TIME" in result
    assert "JOB" in result


def test_separator_line_present():
    runs = [_make_run("0 9 * * *", "backup", _T1)]
    result = format_agenda(runs)
    assert "---" in result


def test_run_time_appears_in_output():
    runs = [_make_run("0 9 * * *", "backup", _T1)]
    result = format_agenda(runs)
    assert "2024-03-05 09:00" in result


def test_job_name_appears_in_output():
    runs = [_make_run("0 9 * * *", "backup", _T1)]
    result = format_agenda(runs)
    assert "backup" in result


def test_multiple_runs_all_listed():
    runs = [
        _make_run("0 9 * * *", "morning", _T1),
        _make_run("30 14 * * *", "afternoon", _T2),
    ]
    result = format_agenda(runs)
    assert "morning" in result
    assert "afternoon" in result
    assert "09:00" in result
    assert "14:30" in result


def test_day_of_week_abbreviation_in_timestamp():
    runs = [_make_run("0 9 * * *", "job", _T1)]  # Tuesday
    result = format_agenda(runs)
    assert "Tue" in result
