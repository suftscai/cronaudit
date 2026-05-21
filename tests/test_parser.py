"""Tests for cronaudit.parser module."""

import pytest
from cronaudit.parser import parse_cron_expression, CronSchedule


def test_wildcard_expands_all_minutes():
    schedule = parse_cron_expression("* * * * *", "echo hello")
    assert schedule.minute == list(range(0, 60))


def test_wildcard_expands_all_hours():
    schedule = parse_cron_expression("* * * * *")
    assert schedule.hour == list(range(0, 24))


def test_step_expression():
    schedule = parse_cron_expression("*/15 * * * *")
    assert schedule.minute == [0, 15, 30, 45]


def test_range_expression():
    schedule = parse_cron_expression("0 9-17 * * *")
    assert schedule.hour == list(range(9, 18))
    assert schedule.minute == [0]


def test_list_expression():
    schedule = parse_cron_expression("0 8,12,18 * * *")
    assert schedule.hour == [8, 12, 18]


def test_combined_expression():
    schedule = parse_cron_expression("0,30 */6 * * *")
    assert schedule.minute == [0, 30]
    assert schedule.hour == [0, 6, 12, 18]


def test_day_of_week():
    schedule = parse_cron_expression("0 0 * * 1-5")
    assert schedule.day_of_week == [1, 2, 3, 4, 5]


def test_month_range():
    schedule = parse_cron_expression("0 0 1 1-6 *")
    assert schedule.month == [1, 2, 3, 4, 5, 6]
    assert schedule.day_of_month == [1]


def test_command_stored():
    schedule = parse_cron_expression("* * * * *", "/usr/bin/backup.sh")
    assert schedule.command == "/usr/bin/backup.sh"


def test_expression_stored():
    expr = "30 4 * * 0"
    schedule = parse_cron_expression(expr)
    assert schedule.expression == expr


def test_invalid_expression_too_few_fields():
    with pytest.raises(ValueError, match="expected 5 fields"):
        parse_cron_expression("* * * *")


def test_invalid_expression_too_many_fields():
    with pytest.raises(ValueError, match="expected 5 fields"):
        parse_cron_expression("* * * * * *")


def test_str_representation():
    schedule = parse_cron_expression("0 12 * * *", "lunch.sh")
    assert "0 12 * * *" in str(schedule)
    assert "lunch.sh" in str(schedule)


def test_step_with_range():
    schedule = parse_cron_expression("0 8-20/4 * * *")
    assert schedule.hour == [8, 12, 16, 20]
