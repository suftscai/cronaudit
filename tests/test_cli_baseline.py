"""Tests for cronaudit.cli_baseline."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from cronaudit.cli_baseline import add_baseline_subcommand, _run_baseline
from cronaudit.baseline import BaselineSnapshot, save_baseline


@pytest.fixture()
def crontab_file(tmp_path: Path) -> Path:
    p = tmp_path / "crontab"
    p.write_text("0 2 * * * /usr/bin/backup\n*/5 * * * * /usr/bin/sync\n")
    return p


@pytest.fixture()
def baseline_file(tmp_path: Path) -> Path:
    snap = BaselineSnapshot(
        label="v1",
        jobs=[
            {"name": "/usr/bin/backup", "expression": "0 2 * * *"},
            {"name": "/usr/bin/sync", "expression": "*/5 * * * *"},
        ],
    )
    p = tmp_path / "baseline.json"
    save_baseline(snap, p)
    return p


def _make_args(**kwargs):
    import argparse
    defaults = {"crontab": "", "save": None, "compare": None, "label": "snapshot"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_baseline_subcommand_registers():
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    add_baseline_subcommand(sub)
    args = p.parse_args(["baseline", "crontab.txt", "--label", "ci"])
    assert args.label == "ci"


def test_save_creates_file(tmp_path, crontab_file):
    out = tmp_path / "snap.json"
    args = _make_args(crontab=str(crontab_file), save=str(out))
    rc = _run_baseline(args)
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["label"] == "snapshot"


def test_save_uses_label(tmp_path, crontab_file):
    out = tmp_path / "snap.json"
    args = _make_args(crontab=str(crontab_file), save=str(out), label="prod")
    _run_baseline(args)
    data = json.loads(out.read_text())
    assert data["label"] == "prod"


def test_compare_no_changes(capsys, crontab_file, baseline_file):
    args = _make_args(crontab=str(crontab_file), compare=str(baseline_file))
    rc = _run_baseline(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No changes" in captured.out


def test_compare_detects_change(tmp_path, capsys, crontab_file):
    snap = BaselineSnapshot(
        label="old",
        jobs=[{"name": "/usr/bin/backup", "expression": "0 3 * * *"}],
    )
    bf = tmp_path / "old.json"
    save_baseline(snap, bf)
    args = _make_args(crontab=str(crontab_file), compare=str(bf))
    rc = _run_baseline(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "Changes detected" in captured.out


def test_missing_crontab_returns_error(tmp_path):
    args = _make_args(crontab="/nonexistent/crontab", save=str(tmp_path / "s.json"))
    rc = _run_baseline(args)
    assert rc == 1


def test_no_flag_returns_error(capsys, crontab_file):
    args = _make_args(crontab=str(crontab_file))
    rc = _run_baseline(args)
    assert rc == 1
