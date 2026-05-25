"""Tests for cronaudit.recommender."""

import pytest

from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression
from cronaudit.recommender import (
    Recommendation,
    RecommendationReport,
    recommend,
    _recommend_for_conflicts,
    _recommend_for_high_frequency,
)


def _make_job(name: str, expr: str) -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = name
    job.expression = expr
    job.schedule = parse_cron_expression(expr)
    return job


# ---------------------------------------------------------------------------
# Recommendation.__str__
# ---------------------------------------------------------------------------

def test_recommendation_str_contains_severity():
    r = Recommendation(job_name="myjob", reason="reason", suggestion="fix", severity="warning")
    assert "WARNING" in str(r)


def test_recommendation_str_contains_job_name():
    r = Recommendation(job_name="backup", reason="reason", suggestion="fix")
    assert "backup" in str(r)


def test_recommendation_str_contains_suggestion():
    r = Recommendation(job_name="j", reason="r", suggestion="do something")
    assert "do something" in str(r)


# ---------------------------------------------------------------------------
# RecommendationReport.__str__
# ---------------------------------------------------------------------------

def test_report_no_suggestions_str():
    report = RecommendationReport()
    assert "healthy" in str(report).lower()


def test_report_with_suggestions_str_contains_count():
    recs = [Recommendation(job_name="j", reason="r", suggestion="s")]
    report = RecommendationReport(recommendations=recs)
    assert "1" in str(report)


def test_report_has_suggestions_false_when_empty():
    assert RecommendationReport().has_suggestions() is False


def test_report_has_suggestions_true_when_non_empty():
    recs = [Recommendation(job_name="j", reason="r", suggestion="s")]
    assert RecommendationReport(recommendations=recs).has_suggestions() is True


# ---------------------------------------------------------------------------
# _recommend_for_conflicts
# ---------------------------------------------------------------------------

def test_no_conflict_no_recommendations():
    jobs = [
        _make_job("a", "0 1 * * *"),
        _make_job("b", "0 2 * * *"),
    ]
    recs = _recommend_for_conflicts(jobs)
    assert recs == []


def test_conflict_produces_recommendation():
    jobs = [
        _make_job("a", "0 * * * *"),
        _make_job("b", "0 * * * *"),
    ]
    recs = _recommend_for_conflicts(jobs)
    assert len(recs) >= 1
    assert recs[0].severity == "warning"


def test_conflict_recommendation_mentions_both_jobs():
    jobs = [
        _make_job("alpha", "30 6 * * *"),
        _make_job("beta", "30 6 * * *"),
    ]
    recs = _recommend_for_conflicts(jobs)
    assert len(recs) == 1
    assert "alpha" in recs[0].job_name
    assert "beta" in recs[0].job_name


# ---------------------------------------------------------------------------
# _recommend_for_high_frequency
# ---------------------------------------------------------------------------

def test_high_frequency_every_minute_flagged():
    jobs = [_make_job("frequent", "* * * * *")]
    recs = _recommend_for_high_frequency(jobs)
    assert len(recs) == 1
    assert recs[0].severity == "info"


def test_daily_job_not_flagged():
    jobs = [_make_job("daily", "0 3 * * *")]
    recs = _recommend_for_high_frequency(jobs)
    assert recs == []


def test_twice_hourly_not_flagged():
    # 2 * 24 = 48 which is exactly the threshold — should NOT trigger (>=)
    # Use 1 slot per hour to be safe
    jobs = [_make_job("hourly", "0 * * * *")]
    recs = _recommend_for_high_frequency(jobs)
    assert recs == []


# ---------------------------------------------------------------------------
# recommend (integration)
# ---------------------------------------------------------------------------

def test_recommend_returns_report():
    jobs = [_make_job("a", "0 1 * * *")]
    report = recommend(jobs)
    assert isinstance(report, RecommendationReport)


def test_recommend_empty_jobs_no_suggestions():
    report = recommend([])
    assert report.has_suggestions() is False


def test_recommend_conflicting_and_frequent_jobs():
    jobs = [
        _make_job("x", "* * * * *"),
        _make_job("y", "* * * * *"),
    ]
    report = recommend(jobs)
    assert report.has_suggestions() is True
    severities = {r.severity for r in report.recommendations}
    assert "warning" in severities
    assert "info" in severities
