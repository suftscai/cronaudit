"""Tests for cronaudit.summarizer module."""

import pytest
from unittest.mock import patch
import io

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.summarizer import (
    ScheduleSummary,
    _classify_frequency,
    _runs_per_hour,
    summarize,
    print_summary,
)


def _make_job(expr: str, cmd: str = "job") -> CronJob:
    return CronJob(name=cmd, expression=expr, schedule=parse_cron_expression(expr))


# --- _classify_frequency ---

def test_classify_every_minute():
    schedule = parse_cron_expression("* * * * *")
    assert _classify_frequency(schedule) == "every minute"


def test_classify_every_hour():
    schedule = parse_cron_expression("0 * * * *")
    assert _classify_frequency(schedule) == "every hour"


def test_classify_daily():
    schedule = parse_cron_expression("30 6 * * *")
    assert _classify_frequency(schedule) == "daily"


def test_classify_multiple_times_day():
    schedule = parse_cron_expression("0 0,6,12,18 * * *")
    assert _classify_frequency(schedule) == "multiple times/day"


# --- _runs_per_hour ---

def test_runs_per_hour_has_24_keys():
    jobs = [_make_job("0 9 * * *")]
    rph = _runs_per_hour(jobs)
    assert len(rph) == 24


def test_runs_per_hour_correct_count():
    jobs = [_make_job("0,30 9 * * *")]
    rph = _runs_per_hour(jobs)
    assert rph[9] == 2
    assert rph[10] == 0


def test_runs_per_hour_multiple_jobs():
    jobs = [
        _make_job("0 9 * * *"),
        _make_job("0 9 * * *"),
    ]
    rph = _runs_per_hour(jobs)
    assert rph[9] == 2


# --- summarize ---

def test_summarize_empty_returns_defaults():
    summary = summarize([])
    assert summary.total_jobs == 0
    assert summary.runs_per_day == 0


def test_summarize_total_jobs():
    jobs = [_make_job("0 9 * * *"), _make_job("0 10 * * *")]
    summary = summarize(jobs)
    assert summary.total_jobs == 2


def test_summarize_busiest_hour():
    jobs = [
        _make_job("0,15,30,45 9 * * *"),
        _make_job("0 10 * * *"),
    ]
    summary = summarize(jobs)
    assert summary.busiest_hour == 9


def test_summarize_runs_per_day():
    jobs = [_make_job("0 9 * * *"), _make_job("0 10 * * *")]
    summary = summarize(jobs)
    assert summary.runs_per_day == 2


def test_summary_str_contains_jobs():
    jobs = [_make_job("0 9 * * *")]
    summary = summarize(jobs)
    assert "Jobs: 1" in str(summary)


# --- print_summary ---

def test_print_summary_outputs_header(capsys):
    jobs = [_make_job("0 9 * * *")]
    print_summary(jobs)
    captured = capsys.readouterr()
    assert "Schedule Summary" in captured.out
    assert "Total jobs" in captured.out
