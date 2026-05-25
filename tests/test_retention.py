"""Tests for cronaudit.retention."""

import pytest

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.retention import (
    RetentionFlag,
    RetentionReport,
    _is_duplicate_expression,
    _is_high_frequency,
    analyze_retention,
    format_retention_report,
)


def _make_job(name: str, expression: str) -> CronJob:
    return CronJob(name=name, expression=expression, schedule=parse_cron_expression(expression))


# ---------------------------------------------------------------------------
# RetentionFlag / RetentionReport helpers
# ---------------------------------------------------------------------------

def test_retention_flag_str_contains_severity():
    job = _make_job("backup", "0 2 * * *")
    flag = RetentionFlag(job=job, reason="test reason", severity="warning")
    assert "WARNING" in str(flag)


def test_retention_flag_str_contains_job_name():
    job = _make_job("cleanup", "0 3 * * *")
    flag = RetentionFlag(job=job, reason="some reason", severity="info")
    assert "cleanup" in str(flag)


def test_report_no_flags_has_no_warnings():
    report = RetentionReport()
    assert not report.has_warnings()


def test_report_with_info_flag_has_no_warnings():
    job = _make_job("job", "* * * * *")
    report = RetentionReport(flags=[RetentionFlag(job=job, reason="r", severity="info")])
    assert not report.has_warnings()


def test_report_with_warning_flag_has_warnings():
    job = _make_job("job", "0 1 * * *")
    report = RetentionReport(flags=[RetentionFlag(job=job, reason="r", severity="warning")])
    assert report.has_warnings()


def test_report_str_no_issues():
    report = RetentionReport()
    assert "no issues" in str(report)


def test_report_str_lists_flags():
    job = _make_job("job", "0 1 * * *")
    flag = RetentionFlag(job=job, reason="duplicate", severity="warning")
    report = RetentionReport(flags=[flag])
    assert "duplicate" in str(report)


# ---------------------------------------------------------------------------
# _is_high_frequency
# ---------------------------------------------------------------------------

def test_every_minute_is_high_frequency():
    job = _make_job("noisy", "* * * * *")
    assert _is_high_frequency(job, threshold=12.0)


def test_hourly_is_not_high_frequency():
    job = _make_job("hourly", "0 * * * *")
    assert not _is_high_frequency(job, threshold=12.0)


def test_every_5_minutes_is_high_frequency():
    job = _make_job("frequent", "*/5 * * * *")
    # 12 runs/hour, threshold=12 means strictly greater, so 12 is NOT high
    assert not _is_high_frequency(job, threshold=12.0)


def test_every_4_minutes_is_high_frequency():
    job = _make_job("veryfreq", "*/4 * * * *")
    assert _is_high_frequency(job, threshold=12.0)


# ---------------------------------------------------------------------------
# _is_duplicate_expression
# ---------------------------------------------------------------------------

def test_no_duplicate_when_unique_expressions():
    jobs = [_make_job("a", "0 1 * * *"), _make_job("b", "0 2 * * *")]
    assert _is_duplicate_expression(jobs[0], jobs) is None


def test_duplicate_detected():
    jobs = [_make_job("a", "0 1 * * *"), _make_job("b", "0 1 * * *")]
    result = _is_duplicate_expression(jobs[0], jobs)
    assert result is not None
    assert result.name == "b"


def test_duplicate_not_self():
    jobs = [_make_job("a", "0 1 * * *")]
    assert _is_duplicate_expression(jobs[0], jobs) is None


# ---------------------------------------------------------------------------
# analyze_retention integration
# ---------------------------------------------------------------------------

def test_analyze_no_issues():
    jobs = [_make_job("a", "0 1 * * *"), _make_job("b", "0 2 * * *")]
    report = analyze_retention(jobs)
    assert not report.has_warnings()
    assert report.flags == []


def test_analyze_flags_duplicate():
    jobs = [_make_job("a", "0 1 * * *"), _make_job("b", "0 1 * * *")]
    report = analyze_retention(jobs)
    names = [f.job.name for f in report.flags]
    assert "a" in names or "b" in names


def test_analyze_flags_high_frequency():
    jobs = [_make_job("fast", "* * * * *")]
    report = analyze_retention(jobs, high_freq_threshold=12.0)
    assert any("consolidating" in f.reason for f in report.flags)


def test_format_retention_report_returns_string():
    jobs = [_make_job("a", "0 1 * * *")]
    report = analyze_retention(jobs)
    result = format_retention_report(report)
    assert isinstance(result, str)
