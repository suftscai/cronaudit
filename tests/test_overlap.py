"""Tests for cronaudit.overlap — overlap detection within a time window."""

from datetime import datetime

import pytest

from cronaudit.loader import CronJob
from cronaudit.overlap import OverlapWindow, find_overlaps, format_overlap_report


def _make_job(name: str, expression: str) -> CronJob:
    return CronJob(name=name, expression=expression, command=f"run_{name}")


START = datetime(2024, 1, 15, 0, 0)


# ---------------------------------------------------------------------------
# OverlapWindow.__str__
# ---------------------------------------------------------------------------

def test_overlap_window_str_shows_names():
    job_a = _make_job("alpha", "0 * * * *")
    job_b = _make_job("beta", "0 * * * *")
    times = [datetime(2024, 1, 15, h, 0) for h in range(2)]
    ow = OverlapWindow(job_a=job_a, job_b=job_b, overlapping_times=times)
    result = str(ow)
    assert "alpha" in result
    assert "beta" in result


def test_overlap_window_str_shows_count():
    job_a = _make_job("a", "0 * * * *")
    job_b = _make_job("b", "0 * * * *")
    times = [datetime(2024, 1, 15, h, 0) for h in range(5)]
    ow = OverlapWindow(job_a=job_a, job_b=job_b, overlapping_times=times)
    assert "5" in str(ow)


def test_overlap_window_str_truncates_long_list():
    job_a = _make_job("a", "* * * * *")
    job_b = _make_job("b", "* * * * *")
    times = [datetime(2024, 1, 15, 0, m) for m in range(10)]
    ow = OverlapWindow(job_a=job_a, job_b=job_b, overlapping_times=times)
    assert "+7 more" in str(ow)


# ---------------------------------------------------------------------------
# find_overlaps
# ---------------------------------------------------------------------------

def test_no_overlap_different_schedules():
    job_a = _make_job("a", "0 6 * * *")   # 06:00 daily
    job_b = _make_job("b", "0 12 * * *")  # 12:00 daily
    result = find_overlaps([job_a, job_b], START, lookahead_minutes=1440)
    assert result == []


def test_overlap_detected_same_schedule():
    job_a = _make_job("a", "0 6 * * *")
    job_b = _make_job("b", "0 6 * * *")
    result = find_overlaps([job_a, job_b], START, lookahead_minutes=1440)
    assert len(result) == 1
    assert result[0].job_a.name == "a"
    assert result[0].job_b.name == "b"


def test_overlap_shared_times_correct():
    job_a = _make_job("a", "0 6,12 * * *")
    job_b = _make_job("b", "0 12 * * *")
    result = find_overlaps([job_a, job_b], START, lookahead_minutes=1440)
    assert len(result) == 1
    hours = [t.hour for t in result[0].overlapping_times]
    assert 12 in hours
    assert 6 not in hours


def test_no_overlap_empty_list():
    assert find_overlaps([], START) == []


def test_no_overlap_single_job():
    job = _make_job("solo", "* * * * *")
    assert find_overlaps([job], START) == []


# ---------------------------------------------------------------------------
# format_overlap_report
# ---------------------------------------------------------------------------

def test_format_no_overlaps():
    report = format_overlap_report([])
    assert "No overlapping" in report


def test_format_with_overlaps_contains_count():
    job_a = _make_job("a", "0 6 * * *")
    job_b = _make_job("b", "0 6 * * *")
    overlaps = find_overlaps([job_a, job_b], START, lookahead_minutes=1440)
    report = format_overlap_report(overlaps)
    assert "1 overlapping" in report
    assert "a" in report
    assert "b" in report
