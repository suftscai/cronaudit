"""Tests for cronaudit.validator."""

import pytest

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.validator import (
    ValidationIssue,
    ValidationResult,
    validate_jobs,
    _check_always_running,
    _check_midnight_only,
    _check_never_runs,
)


def _make_job(expression: str, command: str = "cmd") -> CronJob:
    return CronJob(name=command, expression=expression, schedule=parse_cron_expression(expression))


# --- ValidationResult ---

def test_result_no_issues_has_no_errors():
    result = ValidationResult()
    assert not result.has_errors


def test_result_with_error_has_errors():
    job = _make_job("* * * * *")
    issue = ValidationIssue(job=job, severity="error", message="bad")
    result = ValidationResult(issues=[issue])
    assert result.has_errors


def test_result_str_no_issues():
    result = ValidationResult()
    assert "No validation issues" in str(result)


def test_result_str_with_issues():
    job = _make_job("* * * * *")
    issue = ValidationIssue(job=job, severity="warning", message="runs too often")
    result = ValidationResult(issues=[issue])
    assert "WARNING" in str(result)
    assert "runs too often" in str(result)


# --- _check_always_running ---

def test_always_running_wildcard_warns():
    job = _make_job("* * * * *")
    issues = _check_always_running(job)
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "every minute" in issues[0].message


def test_always_running_specific_hour_no_warn():
    job = _make_job("* 6 * * *")
    issues = _check_always_running(job)
    assert issues == []


# --- _check_midnight_only ---

def test_midnight_only_warns():
    job = _make_job("0 0 * * *")
    issues = _check_midnight_only(job)
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "midnight" in issues[0].message


def test_non_midnight_no_warn():
    job = _make_job("30 6 * * *")
    issues = _check_midnight_only(job)
    assert issues == []


# --- _check_never_runs ---

def test_never_runs_valid_job_no_error():
    job = _make_job("*/15 * * * *")
    issues = _check_never_runs(job)
    assert issues == []


# --- validate_jobs ---

def test_validate_jobs_returns_result():
    jobs = [_make_job("*/10 * * * *"), _make_job("0 12 * * 1")]
    result = validate_jobs(jobs)
    assert isinstance(result, ValidationResult)


def test_validate_jobs_detects_always_running():
    jobs = [_make_job("* * * * *", "noisy-job")]
    result = validate_jobs(jobs)
    assert result.has_warnings
    assert any("every minute" in i.message for i in result.issues)


def test_validate_jobs_no_issues_for_clean_schedule():
    jobs = [_make_job("30 9 * * 1-5", "weekday-morning")]
    result = validate_jobs(jobs)
    assert not result.has_errors
    assert not result.has_warnings


def test_validate_multiple_jobs_aggregates_issues():
    jobs = [
        _make_job("* * * * *", "always"),
        _make_job("0 0 * * *", "midnight"),
    ]
    result = validate_jobs(jobs)
    assert len(result.issues) == 2
