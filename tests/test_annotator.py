"""Tests for cronaudit.annotator."""

import pytest

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.annotator import (
    AnnotatedJob,
    annotate_job,
    annotate_jobs,
    describe_schedule,
    format_annotation_report,
)


def _make_job(expression: str, command: str = "run.sh") -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = command
    job.command = command
    job.expression = expression
    job.schedule = parse_cron_expression(expression)
    return job


def test_annotated_job_str_contains_name():
    job = _make_job("0 * * * *")
    annotated = annotate_job(job)
    assert job.name in str(annotated)


def test_annotated_job_str_contains_description():
    job = _make_job("0 * * * *")
    annotated = annotate_job(job)
    assert annotated.description in str(annotated)


def test_describe_every_minute():
    job = _make_job("* * * * *")
    desc = describe_schedule(job.schedule)
    assert "every minute" in desc
    assert "every hour" in desc


def test_describe_single_minute_and_hour():
    job = _make_job("30 6 * * *")
    desc = describe_schedule(job.schedule)
    assert "minute 30" in desc
    assert "hour 6" in desc


def test_describe_range_expression():
    job = _make_job("0 1-5 * * *")
    desc = describe_schedule(job.schedule)
    assert "from 1 to 5" in desc


def test_note_high_frequency_every_minute():
    job = _make_job("* * * * *")
    annotated = annotate_job(job)
    assert any("high frequency" in n for n in annotated.notes)


def test_note_more_than_once_per_hour():
    job = _make_job("*/5 * * * *")
    annotated = annotate_job(job)
    assert any("more than once per hour" in n for n in annotated.notes)


def test_note_midnight_only():
    job = _make_job("0 0 * * *")
    annotated = annotate_job(job)
    assert any("midnight" in n for n in annotated.notes)


def test_note_weekday_schedule():
    job = _make_job("0 9 * * 1-5")
    annotated = annotate_job(job)
    assert any("Weekday" in n for n in annotated.notes)


def test_note_weekend_schedule():
    job = _make_job("0 10 * * 0,6")
    annotated = annotate_job(job)
    assert any("Weekend" in n for n in annotated.notes)


def test_annotate_jobs_returns_list():
    jobs = [_make_job("0 * * * *"), _make_job("30 6 * * *")]
    result = annotate_jobs(jobs)
    assert len(result) == 2
    assert all(isinstance(a, AnnotatedJob) for a in result)


def test_format_annotation_report_empty():
    report = format_annotation_report([])
    assert "no jobs" in report


def test_format_annotation_report_contains_all_names():
    jobs = [_make_job("0 * * * *", "backup.sh"), _make_job("*/10 * * * *", "sync.sh")]
    annotated = annotate_jobs(jobs)
    report = format_annotation_report(annotated)
    assert "backup.sh" in report
    assert "sync.sh" in report
