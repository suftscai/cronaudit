"""Tests for cronaudit/exporter.py"""

import json
import csv
import io
import pytest

from unittest.mock import MagicMock
from cronaudit.exporter import (
    jobs_to_dict,
    conflicts_to_dict,
    export_json,
    export_csv,
    write_export,
)


def _make_job(name, expression="* * * * *", command="/bin/true"):
    from cronaudit.loader import CronJob
    from cronaudit.parser import parse_cron_expression
    job = MagicMock(spec=CronJob)
    job.name = name
    job.command = command
    job.schedule = MagicMock()
    job.schedule.expression = expression
    return job


def _make_conflict(name_a, name_b, slots=5):
    from cronaudit.conflict import Conflict
    conflict = MagicMock(spec=Conflict)
    conflict.job_a = _make_job(name_a)
    conflict.job_b = _make_job(name_b)
    conflict.overlapping_slots = list(range(slots))
    return conflict


def test_jobs_to_dict_contains_name_and_expression():
    jobs = [_make_job("backup", "0 2 * * *")]
    result = jobs_to_dict(jobs)
    assert result[0]["name"] == "backup"
    assert result[0]["expression"] == "0 2 * * *"


def test_conflicts_to_dict_contains_slot_count():
    conflicts = [_make_conflict("job_a", "job_b", slots=3)]
    result = conflicts_to_dict(conflicts)
    assert result[0]["overlapping_slots"] == 3
    assert result[0]["job_a"] == "job_a"
    assert result[0]["job_b"] == "job_b"


def test_export_json_is_valid_json():
    jobs = [_make_job("sync", "*/5 * * * *")]
    conflicts = [_make_conflict("sync", "backup", slots=10)]
    result = export_json(jobs, conflicts)
    parsed = json.loads(result)
    assert "jobs" in parsed
    assert "conflicts" in parsed
    assert len(parsed["jobs"]) == 1
    assert len(parsed["conflicts"]) == 1


def test_export_csv_has_header_and_row():
    conflicts = [_make_conflict("alpha", "beta", slots=7)]
    result = export_csv([], conflicts)
    reader = csv.reader(io.StringIO(result))
    rows = list(reader)
    assert rows[0] == ["job_a", "job_b", "overlapping_slots"]
    assert rows[1][0] == "alpha"
    assert rows[1][1] == "beta"
    assert rows[1][2] == "7"


def test_export_csv_no_conflicts_only_header():
    result = export_csv([], [])
    reader = csv.reader(io.StringIO(result))
    rows = list(reader)
    assert rows[0] == ["job_a", "job_b", "overlapping_slots"]
    assert len(rows) == 1


def test_write_export_unsupported_extension_raises():
    with pytest.raises(ValueError, match="Unsupported export format"):
        write_export("output.xml", [], [])


def test_write_export_json(tmp_path):
    out = tmp_path / "report.json"
    jobs = [_make_job("nightly", "0 0 * * *")]
    write_export(str(out), jobs, [])
    data = json.loads(out.read_text())
    assert data["jobs"][0]["name"] == "nightly"


def test_write_export_csv(tmp_path):
    out = tmp_path / "report.csv"
    conflicts = [_make_conflict("x", "y", slots=2)]
    write_export(str(out), [], conflicts)
    content = out.read_text()
    assert "x" in content
    assert "y" in content
