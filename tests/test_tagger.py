"""Tests for cronaudit.tagger."""

from unittest.mock import MagicMock

from cronaudit.loader import CronJob
from cronaudit.parser import CronSchedule
from cronaudit.tagger import (
    TaggedJob,
    _command_tags,
    _frequency_tag,
    tag_job,
    tag_jobs,
    format_tag_report,
)


def _make_job(expression: str, command: str = "run_task.sh") -> CronJob:
    job = MagicMock(spec=CronJob)
    job.name = command.split()[0]
    job.command = command
    from cronaudit.parser import parse_cron_expression
    job.schedule = parse_cron_expression(expression)
    return job


def test_tagged_job_str_contains_name():
    job = _make_job("* * * * *", "backup.sh")
    tj = TaggedJob(job=job, tags=["every-minute"])
    assert "backup.sh" in str(tj)


def test_tagged_job_str_contains_tags():
    job = _make_job("* * * * *", "backup.sh")
    tj = TaggedJob(job=job, tags=["every-minute", "backup"])
    result = str(tj)
    assert "every-minute" in result
    assert "backup" in result


def test_tagged_job_str_no_tags_shows_placeholder():
    job = _make_job("0 * * * *", "task.sh")
    tj = TaggedJob(job=job, tags=[])
    assert "(no tags)" in str(tj)


def test_command_tags_backup_keyword():
    tags = _command_tags("/usr/local/bin/backup_db.sh")
    assert "backup" in tags


def test_command_tags_monitoring_keyword():
    tags = _command_tags("health_check.sh --verbose")
    assert "monitoring" in tags


def test_command_tags_no_match_returns_empty():
    tags = _command_tags("arbitrary_script_xyz.sh")
    assert tags == []


def test_command_tags_multiple_keywords():
    tags = _command_tags("send_report.sh")
    assert "notification" in tags
    assert "reporting" in tags


def test_frequency_tag_every_minute():
    job = _make_job("* * * * *", "task.sh")
    tag = _frequency_tag(job)
    assert tag == "every-minute"


def test_frequency_tag_hourly():
    job = _make_job("0 * * * *", "task.sh")
    tag = _frequency_tag(job)
    assert tag == "hourly"


def test_frequency_tag_daily():
    job = _make_job("0 2 * * *", "task.sh")
    tag = _frequency_tag(job)
    assert tag == "daily"


def test_tag_job_includes_frequency():
    job = _make_job("* * * * *", "task.sh")
    tj = tag_job(job)
    assert "every-minute" in tj.tags


def test_tag_job_includes_command_tag():
    job = _make_job("0 3 * * *", "rotate_logs.sh")
    tj = tag_job(job)
    assert "maintenance" in tj.tags


def test_tag_jobs_returns_one_per_job():
    jobs = [_make_job("* * * * *"), _make_job("0 1 * * *")]
    result = tag_jobs(jobs)
    assert len(result) == 2


def test_format_tag_report_empty():
    assert format_tag_report([]) == "No jobs to tag."


def test_format_tag_report_contains_header():
    jobs = [_make_job("0 * * * *", "check.sh")]
    tagged = tag_jobs(jobs)
    report = format_tag_report(tagged)
    assert "Tagged Jobs" in report


def test_format_tag_report_contains_job_name():
    jobs = [_make_job("0 0 * * *", "deploy.sh")]
    tagged = tag_jobs(jobs)
    report = format_tag_report(tagged)
    assert "deploy.sh" in report
