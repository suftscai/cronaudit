"""Tests for cronaudit.cli_simulator."""

import argparse
import os
import tempfile
from datetime import datetime
from unittest.mock import patch

import pytest

from cronaudit.cli_simulator import add_simulator_subcommand, _run_simulator


@pytest.fixture
def crontab_file():
    content = "* * * * * /usr/bin/tick\n0 * * * * /usr/bin/hourly\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".cron", delete=False) as f:
        f.write(content)
        path = f.name
    yield path
    os.unlink(path)


def _make_args(crontab, start=None, hours=24):
    ns = argparse.Namespace(crontab=crontab, start=start, hours=hours)
    return ns


def test_add_simulator_subcommand_registers():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_simulator_subcommand(subparsers)
    args = parser.parse_args(["simulate", "some_file"])
    assert hasattr(args, "func")


def test_add_simulator_subcommand_hours_flag():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_simulator_subcommand(subparsers)
    args = parser.parse_args(["simulate", "file.cron", "--hours", "48"])
    assert args.hours == 48


def test_add_simulator_subcommand_start_flag():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_simulator_subcommand(subparsers)
    args = parser.parse_args(["simulate", "file.cron", "--start", "2024-06-01T08:00"])
    assert args.start == "2024-06-01T08:00"


def test_run_simulator_returns_zero(crontab_file):
    args = _make_args(crontab_file, start="2024-01-01T00:00", hours=1)
    result = _run_simulator(args)
    assert result == 0


def test_run_simulator_prints_output(crontab_file, capsys):
    args = _make_args(crontab_file, start="2024-01-01T00:00", hours=1)
    _run_simulator(args)
    captured = capsys.readouterr()
    assert "Simulation window" in captured.out


def test_run_simulator_no_start_uses_now(crontab_file):
    args = _make_args(crontab_file, start=None, hours=1)
    result = _run_simulator(args)
    assert result == 0


def test_run_simulator_reports_total_runs(crontab_file, capsys):
    args = _make_args(crontab_file, start="2024-01-01T00:00", hours=1)
    _run_simulator(args)
    captured = capsys.readouterr()
    assert "Total runs" in captured.out
