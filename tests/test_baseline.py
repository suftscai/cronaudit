"""Tests for cronaudit.baseline."""
import json
import pytest
from pathlib import Path

from cronaudit.baseline import (
    BaselineSnapshot,
    BaselineDiff,
    snapshot_from_jobs,
    save_baseline,
    load_baseline,
    compare_to_baseline,
)
from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression


def _make_job(name: str, expression: str) -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = name
    job.schedule = parse_cron_expression(expression)
    return job


# --- BaselineSnapshot ---

def test_snapshot_str_singular():
    snap = BaselineSnapshot(label="v1", jobs=[{"name": "a", "expression": "* * * * *"}])
    assert "1 job" in str(snap)
    assert "jobs" not in str(snap)


def test_snapshot_str_plural():
    snap = BaselineSnapshot(label="v1", jobs=[
        {"name": "a", "expression": "* * * * *"},
        {"name": "b", "expression": "0 * * * *"},
    ])
    assert "2 jobs" in str(snap)


def test_snapshot_from_jobs_captures_names():
    jobs = [_make_job("backup", "0 2 * * *"), _make_job("sync", "*/5 * * * *")]
    snap = snapshot_from_jobs("test", jobs)
    names = [e["name"] for e in snap.jobs]
    assert "backup" in names
    assert "sync" in names


def test_snapshot_from_jobs_captures_expressions():
    jobs = [_make_job("backup", "0 2 * * *")]
    snap = snapshot_from_jobs("test", jobs)
    assert snap.jobs[0]["expression"] == "0 2 * * *"


# --- save / load round-trip ---

def test_save_and_load_roundtrip(tmp_path):
    snap = BaselineSnapshot(label="prod", jobs=[{"name": "x", "expression": "0 0 * * *"}])
    p = tmp_path / "baseline.json"
    save_baseline(snap, p)
    loaded = load_baseline(p)
    assert loaded.label == "prod"
    assert loaded.jobs == snap.jobs


def test_save_creates_valid_json(tmp_path):
    snap = BaselineSnapshot(label="ci", jobs=[])
    p = tmp_path / "b.json"
    save_baseline(snap, p)
    data = json.loads(p.read_text())
    assert "label" in data
    assert "jobs" in data


# --- compare_to_baseline ---

def test_no_changes_empty_diff():
    jobs = [_make_job("a", "0 * * * *")]
    snap = snapshot_from_jobs("v1", jobs)
    diff = compare_to_baseline(jobs, snap)
    assert not diff.has_changes


def test_added_job_detected():
    snap = BaselineSnapshot(label="v1", jobs=[{"name": "a", "expression": "0 * * * *"}])
    jobs = [_make_job("a", "0 * * * *"), _make_job("b", "*/10 * * * *")]
    diff = compare_to_baseline(jobs, snap)
    assert "b" in diff.added


def test_removed_job_detected():
    snap = BaselineSnapshot(label="v1", jobs=[
        {"name": "a", "expression": "0 * * * *"},
        {"name": "gone", "expression": "5 * * * *"},
    ])
    jobs = [_make_job("a", "0 * * * *")]
    diff = compare_to_baseline(jobs, snap)
    assert "gone" in diff.removed


def test_changed_expression_detected():
    snap = BaselineSnapshot(label="v1", jobs=[{"name": "a", "expression": "0 * * * *"}])
    jobs = [_make_job("a", "30 * * * *")]
    diff = compare_to_baseline(jobs, snap)
    assert "a" in diff.changed


def test_diff_str_no_changes():
    diff = BaselineDiff()
    assert "No changes" in str(diff)


def test_diff_str_shows_symbols():
    diff = BaselineDiff(added=["new"], removed=["old"], changed=["mod"])
    text = str(diff)
    assert "+" in text
    assert "-" in text
    assert "~" in text
