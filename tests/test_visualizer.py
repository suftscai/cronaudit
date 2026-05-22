"""Tests for the ASCII timeline visualizer."""

import pytest
from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.visualizer import render_timeline, BAR_CHAR, EMPTY_CHAR


def _make_job(name: str, expression: str) -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = name
    job.schedule = parse_cron_expression(expression)
    return job


def test_empty_jobs_returns_placeholder():
    result = render_timeline([])
    assert result == "(no jobs to display)"


def test_header_contains_all_hours():
    job = _make_job("backup", "0 2 * * *")
    result = render_timeline([job])
    header = result.splitlines()[0]
    for h in range(24):
        assert f"{h:02d}" in header


def test_active_hour_shown_as_bar():
    # Job runs at hour 5 only
    job = _make_job("nightly", "0 5 * * *")
    result = render_timeline([job])
    job_line = [l for l in result.splitlines() if "nightly" in l][0]
    # Hour 5 starts at position label_width+2 + 5*2
    label_width = len("nightly")
    col_start = label_width + 2 + 5 * 2
    assert job_line[col_start: col_start + 2] == BAR_CHAR * 2


def test_inactive_hour_shown_as_empty():
    # Job runs at hour 5 only; hour 0 should be empty
    job = _make_job("nightly", "0 5 * * *")
    result = render_timeline([job])
    job_line = [l for l in result.splitlines() if "nightly" in l][0]
    label_width = len("nightly")
    col_start = label_width + 2 + 0 * 2
    assert job_line[col_start: col_start + 2] == EMPTY_CHAR * 2


def test_wildcard_hour_all_bars():
    # Job runs every hour
    job = _make_job("heartbeat", "* * * * *")
    result = render_timeline([job])
    job_line = [l for l in result.splitlines() if "heartbeat" in l][0]
    label_width = len("heartbeat")
    bar_section = job_line[label_width + 2:]
    assert bar_section == BAR_CHAR * 2 * 24


def test_multiple_jobs_all_present():
    jobs = [
        _make_job("alpha", "0 1 * * *"),
        _make_job("beta", "0 2 * * *"),
        _make_job("gamma", "0 3 * * *"),
    ]
    result = render_timeline(jobs)
    for name in ("alpha", "beta", "gamma"):
        assert name in result


def test_label_width_aligns_correctly():
    jobs = [
        _make_job("short", "0 0 * * *"),
        _make_job("a-much-longer-name", "0 0 * * *"),
    ]
    result = render_timeline(jobs)
    lines = [l for l in result.splitlines() if BAR_CHAR in l or EMPTY_CHAR in l]
    # All job lines should have the same total length
    lengths = [len(l) for l in lines]
    assert len(set(lengths)) == 1
