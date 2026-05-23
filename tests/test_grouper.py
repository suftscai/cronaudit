"""Tests for cronaudit.grouper."""

from __future__ import annotations

import pytest

from cronaudit.grouper import (
    JobGroup,
    format_group_report,
    group_by_expression,
    group_by_frequency,
)
from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression


def _make_job(name: str, expression: str) -> CronJob:
    schedule = parse_cron_expression(expression)
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = name
    job.schedule = schedule
    return job


# ---------------------------------------------------------------------------
# JobGroup
# ---------------------------------------------------------------------------

def test_job_group_str_contains_key():
    group = JobGroup(key="*/5 * * * *")
    assert "*/5 * * * *" in str(group)


def test_job_group_str_shows_job_count():
    group = JobGroup(key="*/5 * * * *", jobs=[_make_job("a", "*/5 * * * *")])
    assert "1 job" in str(group)


def test_job_group_str_lists_job_names():
    jobs = [_make_job("alpha", "*/5 * * * *"), _make_job("beta", "*/5 * * * *")]
    group = JobGroup(key="*/5 * * * *", jobs=jobs)
    assert "alpha" in str(group)
    assert "beta" in str(group)


# ---------------------------------------------------------------------------
# group_by_expression
# ---------------------------------------------------------------------------

def test_group_by_expression_same_expression():
    jobs = [_make_job("a", "0 * * * *"), _make_job("b", "0 * * * *")]
    groups = group_by_expression(jobs)
    assert len(groups) == 1
    assert len(list(groups.values())[0].jobs) == 2


def test_group_by_expression_different_expressions():
    jobs = [_make_job("a", "0 * * * *"), _make_job("b", "*/5 * * * *")]
    groups = group_by_expression(jobs)
    assert len(groups) == 2


def test_group_by_expression_empty_list():
    assert group_by_expression([]) == {}


def test_group_by_expression_key_is_expression():
    jobs = [_make_job("a", "30 6 * * *")]
    groups = group_by_expression(jobs)
    assert "30 6 * * *" in groups


# ---------------------------------------------------------------------------
# group_by_frequency
# ---------------------------------------------------------------------------

def test_group_by_frequency_every_minute_bucket():
    jobs = [_make_job("a", "* * * * *"), _make_job("b", "* * * * *")]
    groups = group_by_frequency(jobs)
    assert any("every minute" in k for k in groups)


def test_group_by_frequency_daily_bucket():
    jobs = [_make_job("a", "0 3 * * *")]
    groups = group_by_frequency(jobs)
    assert any("daily" in k for k in groups)


def test_group_by_frequency_empty_list():
    assert group_by_frequency([]) == {}


# ---------------------------------------------------------------------------
# format_group_report
# ---------------------------------------------------------------------------

def test_format_group_report_title_present():
    jobs = [_make_job("x", "0 * * * *")]
    groups = group_by_expression(jobs)
    report = format_group_report(groups, title="Test Groups")
    assert "Test Groups" in report


def test_format_group_report_empty_groups():
    report = format_group_report({})
    assert "no groups" in report


def test_format_group_report_contains_job_name():
    jobs = [_make_job("myjob", "*/10 * * * *")]
    groups = group_by_expression(jobs)
    report = format_group_report(groups)
    assert "myjob" in report
