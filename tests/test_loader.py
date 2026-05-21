"""Tests for the crontab loader."""

import pytest
from cronaudit.loader import load_from_string, jobs_to_schedule_pairs, CronJob


SAMPLE_CRONTAB = """
# Daily backup at 2am
0 2 * * * /usr/local/bin/backup.sh --full

# Hourly health check
0 * * * * /usr/local/bin/healthcheck.py

# Every 15 minutes log rotation
*/15 * * * * /usr/sbin/logrotate /etc/logrotate.conf
"""


def test_load_ignores_comments_and_blanks():
    jobs = load_from_string(SAMPLE_CRONTAB)
    assert len(jobs) == 3


def test_job_names_derived_from_command():
    jobs = load_from_string(SAMPLE_CRONTAB)
    names = [j.name for j in jobs]
    assert "backup.sh" in names
    assert "healthcheck.py" in names
    assert "logrotate" in names


def test_job_has_schedule():
    jobs = load_from_string(SAMPLE_CRONTAB)
    backup = next(j for j in jobs if j.name == "backup.sh")
    assert backup.schedule.minutes == [0]
    assert backup.schedule.hours == [2]


def test_job_repr():
    jobs = load_from_string("0 6 * * * /bin/task")
    assert "task" in repr(jobs[0])
    assert "0 6 * * *" in repr(jobs[0])


def test_invalid_line_raises():
    with pytest.raises(ValueError, match="Line 1"):
        load_from_string("not enough fields")


def test_jobs_to_schedule_pairs():
    jobs = load_from_string("30 8 * * * /bin/report")
    pairs = jobs_to_schedule_pairs(jobs)
    assert len(pairs) == 1
    name, sched = pairs[0]
    assert name == "report"
    assert sched.minutes == [30]
    assert sched.hours == [8]


def test_step_expression_loaded_correctly():
    jobs = load_from_string("*/15 * * * * /bin/ping")
    sched = jobs[0].schedule
    assert 0 in sched.minutes
    assert 15 in sched.minutes
    assert 30 in sched.minutes
    assert 45 in sched.minutes
