"""Tests for cronaudit.differ module."""

import pytest
from cronaudit.loader import CronJob
from cronaudit.differ import diff_crontabs, CrontabDiff
from cronaudit.parser import parse_cron_expression


def _make_job(name: str, expression: str) -> CronJob:
    schedule = parse_cron_expression(expression)
    job = CronJob.__new__(CronJob)
    job.name = name
    job.expression = expression
    job.schedule = schedule
    return job


def test_no_changes_returns_empty_diff():
    jobs = [_make_job("backup", "0 2 * * *")]
    result = diff_crontabs(jobs, jobs)
    assert not result.has_changes
    assert result.added == []
    assert result.removed == []
    assert result.changed == []


def test_added_job_detected():
    old = [_make_job("backup", "0 2 * * *")]
    new = [_make_job("backup", "0 2 * * *"), _make_job("cleanup", "0 3 * * *")]
    result = diff_crontabs(old, new)
    assert len(result.added) == 1
    assert result.added[0].name == "cleanup"
    assert not result.removed
    assert not result.changed


def test_removed_job_detected():
    old = [_make_job("backup", "0 2 * * *"), _make_job("cleanup", "0 3 * * *")]
    new = [_make_job("backup", "0 2 * * *")]
    result = diff_crontabs(old, new)
    assert len(result.removed) == 1
    assert result.removed[0].name == "cleanup"
    assert not result.added
    assert not result.changed


def test_changed_expression_detected():
    old = [_make_job("backup", "0 2 * * *")]
    new = [_make_job("backup", "0 4 * * *")]
    result = diff_crontabs(old, new)
    assert len(result.changed) == 1
    old_job, new_job = result.changed[0]
    assert old_job.expression == "0 2 * * *"
    assert new_job.expression == "0 4 * * *"
    assert not result.added
    assert not result.removed


def test_has_changes_true_when_diff_exists():
    old = [_make_job("backup", "0 2 * * *")]
    new = [_make_job("cleanup", "0 3 * * *")]
    result = diff_crontabs(old, new)
    assert result.has_changes


def test_str_no_changes():
    result = CrontabDiff()
    assert str(result) == "No changes detected."


def test_str_shows_added_removed_changed():
    added = _make_job("newjob", "*/5 * * * *")
    removed = _make_job("oldjob", "0 1 * * *")
    old_changed = _make_job("shared", "0 2 * * *")
    new_changed = _make_job("shared", "0 6 * * *")
    result = CrontabDiff(added=[added], removed=[removed], changed=[(old_changed, new_changed)])
    output = str(result)
    assert "+ newjob" in output
    assert "- oldjob" in output
    assert "~ shared" in output
    assert "->" in output
