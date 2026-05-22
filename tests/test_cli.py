"""Tests for cronaudit/cli.py"""

import json
import pytest
from unittest.mock import patch, MagicMock

from cronaudit.cli import build_parser, main


CRONTAB_CONTENT = """# daily backup
0 2 * * * /usr/bin/backup
# hourly sync
0 * * * * /usr/bin/sync
"""


@pytest.fixture()
def crontab_file(tmp_path):
    f = tmp_path / "test.crontab"
    f.write_text(CRONTAB_CONTENT)
    return str(f)


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["somefile"])
    assert args.crontab == "somefile"
    assert args.timeline is False
    assert args.export is None
    assert args.no_color is False


def test_build_parser_timeline_flag():
    parser = build_parser()
    args = parser.parse_args(["somefile", "--timeline"])
    assert args.timeline is True


def test_build_parser_export_option():
    parser = build_parser()
    args = parser.parse_args(["somefile", "--export", "out.json"])
    assert args.export == "out.json"


def test_main_returns_zero_on_valid_file(crontab_file, capsys):
    result = main([crontab_file])
    assert result == 0


def test_main_returns_one_on_missing_file():
    result = main(["nonexistent_file.crontab"])
    assert result == 1


def test_main_with_timeline_flag(crontab_file, capsys):
    result = main([crontab_file, "--timeline"])
    assert result == 0
    captured = capsys.readouterr()
    assert "Hour" in captured.out


def test_main_exports_json(crontab_file, tmp_path):
    out = tmp_path / "result.json"
    result = main([crontab_file, "--export", str(out)])
    assert result == 0
    data = json.loads(out.read_text())
    assert "jobs" in data
    assert "conflicts" in data


def test_main_exports_csv(crontab_file, tmp_path):
    out = tmp_path / "result.csv"
    result = main([crontab_file, "--export", str(out)])
    assert result == 0
    content = out.read_text()
    assert "job_a" in content


def test_main_bad_export_extension_returns_one(crontab_file):
    result = main([crontab_file, "--export", "report.xml"])
    assert result == 1
