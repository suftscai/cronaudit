"""Tests for cronaudit.cli_notifier."""

import argparse
import pytest
from unittest.mock import patch, MagicMock
from cronaudit.cli_notifier import add_notifier_subcommand, _run_notifier
from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "crontab": "fake.cron",
        "command_contains": None,
        "frequency": None,
        "rule_name": "user-rule",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_job(expression: str, command: str = "run.sh") -> CronJob:
    schedule = parse_cron_expression(expression)
    return CronJob(name=command, expression=expression, command=command, schedule=schedule)


# --- subcommand registration ---

def test_add_notifier_subcommand_registers():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_notifier_subcommand(sub)
    args = parser.parse_args(["notify", "my.cron", "--command-contains", "backup"])
    assert args.crontab == "my.cron"
    assert args.command_contains == "backup"


def test_add_notifier_subcommand_frequency_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_notifier_subcommand(sub)
    args = parser.parse_args(["notify", "my.cron", "--frequency", "every_minute"])
    assert args.frequency == "every_minute"


def test_add_notifier_subcommand_default_rule_name():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_notifier_subcommand(sub)
    args = parser.parse_args(["notify", "my.cron", "--command-contains", "x"])
    assert args.rule_name == "user-rule"


# --- _run_notifier ---

def test_run_notifier_no_criteria_returns_one(capsys):
    args = _make_args(command_contains=None, frequency=None)
    with patch("cronaudit.cli_notifier.load_from_file", return_value=[]):
        rc = _run_notifier(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "Error" in captured.out


def test_run_notifier_with_match_prints_notification(capsys):
    job = _make_job("0 2 * * *", "backup.sh")
    args = _make_args(command_contains="backup", rule_name="bk")
    with patch("cronaudit.cli_notifier.load_from_file", return_value=[job]):
        rc = _run_notifier(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "bk" in captured.out


def test_run_notifier_no_match_prints_no_notifications(capsys):
    job = _make_job("0 2 * * *", "cleanup.sh")
    args = _make_args(command_contains="backup")
    with patch("cronaudit.cli_notifier.load_from_file", return_value=[job]):
        rc = _run_notifier(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No notifications" in captured.out
