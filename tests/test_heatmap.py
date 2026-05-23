"""Tests for cronaudit.heatmap."""

from unittest.mock import MagicMock

import pytest

from cronaudit.heatmap import (
    Heatmap,
    build_heatmap,
    render_heatmap,
    DAYS,
)
from cronaudit.parser import CronSchedule


def _make_job(expression: str) -> MagicMock:
    job = MagicMock()
    job.schedule = CronSchedule.parse_cron_expression(expression)
    return job


# ---------------------------------------------------------------------------
# Heatmap dataclass
# ---------------------------------------------------------------------------

def test_heatmap_initial_all_zeros():
    hm = Heatmap()
    assert all(v == 0 for row in hm.grid for v in row)


def test_heatmap_increment():
    hm = Heatmap()
    hm.increment(0, 3)
    assert hm.grid[0][3] == 1


def test_heatmap_max_value():
    hm = Heatmap()
    hm.increment(1, 5)
    hm.increment(1, 5)
    assert hm.max_value() == 2


def test_heatmap_max_value_empty_is_zero():
    hm = Heatmap()
    assert hm.max_value() == 0


# ---------------------------------------------------------------------------
# build_heatmap
# ---------------------------------------------------------------------------

def test_build_heatmap_no_jobs_all_zeros():
    hm = build_heatmap([])
    assert all(v == 0 for row in hm.grid for v in row)


def test_build_heatmap_single_job_increments_correct_cell():
    # "0 9 * * 1" => every Monday at 09:00
    job = _make_job("0 9 * * 1")
    hm = build_heatmap([job])
    # Monday is index 0 in DAYS
    assert hm.grid[0][9] >= 1


def test_build_heatmap_wildcard_dow_fills_all_days():
    # "0 6 * * *" => every day at 06:00
    job = _make_job("0 6 * * *")
    hm = build_heatmap([job])
    assert all(hm.grid[d][6] >= 1 for d in range(7))


def test_build_heatmap_multiple_jobs_accumulate():
    job1 = _make_job("0 8 * * 1")
    job2 = _make_job("0 8 * * 1")
    hm = build_heatmap([job1, job2])
    assert hm.grid[0][8] == 2


# ---------------------------------------------------------------------------
# render_heatmap
# ---------------------------------------------------------------------------

def test_render_heatmap_empty_returns_placeholder():
    assert render_heatmap([]) == "(no jobs to display)"


def test_render_heatmap_contains_day_labels():
    job = _make_job("0 0 * * *")
    output = render_heatmap([job])
    for day in DAYS:
        assert day in output


def test_render_heatmap_contains_hour_header():
    job = _make_job("0 0 * * *")
    output = render_heatmap([job])
    assert "00" in output
    assert "23" in output


def test_render_heatmap_active_cell_not_space():
    # All hours, all days — every cell should be non-space shade
    job = _make_job("* * * * *")
    output = render_heatmap([job])
    # At least one filled shade character should be present
    assert any(ch in output for ch in "░▒▓█")
