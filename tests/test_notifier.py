"""Tests for cronaudit.notifier."""

import pytest
from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.notifier import (
    NotificationRule,
    Notification,
    evaluate_rules,
    format_notification_report,
)


def _make_job(expression: str, command: str = "run.sh") -> CronJob:
    schedule = parse_cron_expression(expression)
    name = command.split()[0]
    return CronJob(name=name, expression=expression, command=command, schedule=schedule)


# --- NotificationRule.matches ---

def test_rule_matches_command_substring():
    rule = NotificationRule(name="backup-alert", command_contains="backup")
    job = _make_job("0 2 * * *", "backup.sh")
    assert rule.matches(job)


def test_rule_no_match_command_substring():
    rule = NotificationRule(name="backup-alert", command_contains="backup")
    job = _make_job("0 2 * * *", "cleanup.sh")
    assert not rule.matches(job)


def test_rule_matches_frequency():
    rule = NotificationRule(name="minutely", frequency="every_minute")
    job = _make_job("* * * * *", "poll.sh")
    assert rule.matches(job)


def test_rule_no_match_frequency():
    rule = NotificationRule(name="minutely", frequency="every_minute")
    job = _make_job("0 * * * *", "hourly.sh")
    assert not rule.matches(job)


def test_rule_combined_both_must_match():
    rule = NotificationRule(name="combined", frequency="every_minute", command_contains="poll")
    job_both = _make_job("* * * * *", "poll.sh")
    job_only_freq = _make_job("* * * * *", "other.sh")
    assert rule.matches(job_both)
    assert not rule.matches(job_only_freq)


# --- evaluate_rules ---

def test_evaluate_returns_notification_for_match():
    rule = NotificationRule(name="backup-alert", command_contains="backup")
    job = _make_job("0 2 * * *", "backup.sh")
    result = evaluate_rules([job], [rule])
    assert len(result) == 1
    assert result[0].rule_name == "backup-alert"
    assert result[0].job is job


def test_evaluate_no_match_returns_empty():
    rule = NotificationRule(name="backup-alert", command_contains="backup")
    job = _make_job("0 2 * * *", "cleanup.sh")
    result = evaluate_rules([job], [rule])
    assert result == []


def test_evaluate_multiple_rules_multiple_notifications():
    r1 = NotificationRule(name="r1", command_contains="backup")
    r2 = NotificationRule(name="r2", frequency="every_minute")
    j1 = _make_job("* * * * *", "backup.sh")
    result = evaluate_rules([j1], [r1, r2])
    assert len(result) == 2


# --- format_notification_report ---

def test_format_report_no_notifications():
    output = format_notification_report([])
    assert "No notifications" in output


def test_format_report_contains_rule_name():
    rule = NotificationRule(name="my-rule", command_contains="run")
    job = _make_job("0 * * * *", "run.sh")
    notifs = evaluate_rules([job], [rule])
    output = format_notification_report(notifs)
    assert "my-rule" in output


def test_notification_str_format():
    job = _make_job("0 * * * *", "run.sh")
    n = Notification(rule_name="test-rule", job=job)
    s = str(n)
    assert "test-rule" in s
    assert "0 * * * *" in s
