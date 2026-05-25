"""Tests for cronaudit.cli_recommender."""

import argparse
import textwrap
from pathlib import Path

import pytest

from cronaudit.cli_recommender import add_recommender_subcommand, _run_recommender


@pytest.fixture()
def crontab_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        # daily backup
        0 2 * * * /usr/bin/backup.sh
        # weekly cleanup
        0 3 * * 0 /usr/bin/cleanup.sh
    """)
    p = tmp_path / "crontab"
    p.write_text(content)
    return p


@pytest.fixture()
def conflict_crontab_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        0 2 * * * /usr/bin/job_a.sh
        0 2 * * * /usr/bin/job_b.sh
    """)
    p = tmp_path / "conflict_crontab"
    p.write_text(content)
    return p


def _make_args(crontab: str, severity=None) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.crontab = crontab
    ns.severity = severity
    ns.func = _run_recommender
    return ns


# ---------------------------------------------------------------------------
# sub-command registration
# ---------------------------------------------------------------------------

def test_add_recommender_subcommand_registers():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_recommender_subcommand(sub)
    args = root.parse_args(["recommend", "/fake/path"])
    assert hasattr(args, "func")


def test_add_recommender_subcommand_severity_flag():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_recommender_subcommand(sub)
    args = root.parse_args(["recommend", "/fake", "--severity", "warning"])
    assert args.severity == "warning"


def test_add_recommender_subcommand_default_severity_is_none():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_recommender_subcommand(sub)
    args = root.parse_args(["recommend", "/fake"])
    assert args.severity is None


# ---------------------------------------------------------------------------
# _run_recommender
# ---------------------------------------------------------------------------

def test_run_recommender_returns_zero_on_healthy_file(crontab_file, capsys):
    args = _make_args(str(crontab_file))
    rc = _run_recommender(args)
    assert rc == 0


def test_run_recommender_healthy_output_mentions_healthy(crontab_file, capsys):
    args = _make_args(str(crontab_file))
    _run_recommender(args)
    out = capsys.readouterr().out
    assert "healthy" in out.lower()


def test_run_recommender_conflict_produces_output(conflict_crontab_file, capsys):
    args = _make_args(str(conflict_crontab_file))
    rc = _run_recommender(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Recommendations" in out


def test_run_recommender_severity_filter_hides_info(conflict_crontab_file, capsys):
    # Filter to critical only — should suppress info and warning recs
    args = _make_args(str(conflict_crontab_file), severity="critical")
    _run_recommender(args)
    out = capsys.readouterr().out
    assert "healthy" in out.lower() or "Recommendations" not in out


def test_run_recommender_missing_file_returns_one(tmp_path, capsys):
    args = _make_args(str(tmp_path / "nonexistent.txt"))
    rc = _run_recommender(args)
    assert rc == 1
    err = capsys.readouterr().err
    assert "Error" in err
