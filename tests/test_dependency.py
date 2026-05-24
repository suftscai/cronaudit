"""Tests for cronaudit.dependency."""

import pytest
from cronaudit.dependency import (
    _tokenize_command,
    find_dependencies,
    format_dependency_report,
    JobDependency,
)
from cronaudit.loader import CronJob
from cronaudit.parser import parse_cron_expression


def _make_job(name: str, command: str, expr: str = "* * * * *") -> CronJob:
    job = CronJob.__new__(CronJob)
    job.name = name
    job.command = command
    job.expression = expr
    job.schedule = parse_cron_expression(expr)
    return job


def test_tokenize_returns_lowercase_tokens():
    tokens = _tokenize_command("/usr/bin/backup.sh")
    assert "backup.sh" in tokens


def test_tokenize_skips_short_tokens():
    tokens = _tokenize_command("ls -la /tmp")
    assert "la" not in tokens
    assert "ls" not in tokens


def test_tokenize_strips_separators():
    tokens = _tokenize_command("backup.sh && cleanup.sh")
    assert "backup.sh" in tokens
    assert "cleanup.sh" in tokens


def test_no_dependency_when_no_shared_tokens():
    jobs = [
        _make_job("alpha", "/usr/bin/alpha_task.sh"),
        _make_job("beta", "/usr/bin/beta_worker.sh"),
    ]
    deps = find_dependencies(jobs)
    assert deps == []


def test_dependency_detected_on_shared_token():
    jobs = [
        _make_job("backup-start", "/usr/bin/backup.sh start"),
        _make_job("backup-verify", "/usr/bin/backup.sh verify"),
    ]
    deps = find_dependencies(jobs)
    assert len(deps) == 1
    assert "backup.sh" in deps[0].shared_tokens


def test_dependency_source_and_target_set_correctly():
    jobs = [
        _make_job("job-a", "/scripts/deploy.sh"),
        _make_job("job-b", "/scripts/deploy.sh --rollback"),
    ]
    deps = find_dependencies(jobs)
    assert deps[0].source.name == "job-a"
    assert deps[0].target.name == "job-b"


def test_multiple_shared_tokens_captured():
    jobs = [
        _make_job("j1", "python manage.py migrate"),
        _make_job("j2", "python manage.py collectstatic"),
    ]
    deps = find_dependencies(jobs)
    assert len(deps) == 1
    assert "python" in deps[0].shared_tokens or "manage.py" in deps[0].shared_tokens


def test_format_report_no_deps():
    report = format_dependency_report([])
    assert "No suspected" in report


def test_format_report_lists_pairs():
    jobs = [
        _make_job("sync", "/opt/sync.sh"),
        _make_job("verify", "/opt/sync.sh --check"),
    ]
    deps = find_dependencies(jobs)
    report = format_dependency_report(deps)
    assert "sync" in report
    assert "verify" in report


def test_job_dependency_str_contains_names():
    job_a = _make_job("writer", "/bin/write.sh")
    job_b = _make_job("reader", "/bin/read.sh")
    dep = JobDependency(source=job_a, target=job_b, shared_tokens=["data"])
    result = str(dep)
    assert "writer" in result
    assert "reader" in result
    assert "data" in result


def test_job_dependency_str_no_tokens_shows_placeholder():
    job_a = _make_job("a", "/bin/a.sh")
    job_b = _make_job("b", "/bin/b.sh")
    dep = JobDependency(source=job_a, target=job_b, shared_tokens=[])
    assert "(none)" in str(dep)
