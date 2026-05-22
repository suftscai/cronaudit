"""Validates cron expressions and crontab files for common mistakes."""

from dataclasses import dataclass, field
from typing import List

from cronaudit.loader import CronJob


@dataclass
class ValidationIssue:
    job: CronJob
    severity: str  # 'error' or 'warning'
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.job.name!r}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def __str__(self) -> str:
        if not self.issues:
            return "No validation issues found."
        return "\n".join(str(i) for i in self.issues)


def _check_always_running(job: CronJob) -> List[ValidationIssue]:
    """Warn if a job runs every minute of every hour."""
    issues = []
    s = job.schedule
    if (
        len(s.minutes) == 60
        and len(s.hours) == 24
        and len(s.days_of_month) == 31
        and len(s.months) == 12
    ):
        issues.append(
            ValidationIssue(
                job=job,
                severity="warning",
                message="Job runs every minute — consider a less frequent schedule.",
            )
        )
    return issues


def _check_never_runs(job: CronJob) -> List[ValidationIssue]:
    """Error if any field resolved to an empty set (should not happen with valid parse)."""
    issues = []
    s = job.schedule
    for attr, label in [
        ("minutes", "minutes"),
        ("hours", "hours"),
        ("days_of_month", "days-of-month"),
        ("months", "months"),
        ("days_of_week", "days-of-week"),
    ]:
        if not getattr(s, attr):
            issues.append(
                ValidationIssue(
                    job=job,
                    severity="error",
                    message=f"Field '{label}' resolved to an empty set — job will never run.",
                )
            )
    return issues


def _check_midnight_only(job: CronJob) -> List[ValidationIssue]:
    """Warn if a job runs only at midnight (common misconfiguration)."""
    issues = []
    s = job.schedule
    if s.hours == {0} and s.minutes == {0}:
        issues.append(
            ValidationIssue(
                job=job,
                severity="warning",
                message="Job runs only at midnight (00:00) — verify this is intentional.",
            )
        )
    return issues


def validate_jobs(jobs: List[CronJob]) -> ValidationResult:
    """Run all validation checks against a list of CronJob instances."""
    result = ValidationResult()
    for job in jobs:
        result.issues.extend(_check_never_runs(job))
        result.issues.extend(_check_always_running(job))
        result.issues.extend(_check_midnight_only(job))
    return result
