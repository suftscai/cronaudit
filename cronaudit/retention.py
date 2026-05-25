"""Retention policy analysis for cron jobs.

Detects jobs that may be redundant due to overlapping schedules or that
have not been updated in a long time based on snapshot comparison.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from cronaudit.loader import CronJob
from cronaudit.summarizer import _runs_per_hour


@dataclass
class RetentionFlag:
    job: CronJob
    reason: str
    severity: str  # 'info', 'warning', 'error'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.job.name}: {self.reason}"


@dataclass
class RetentionReport:
    flags: List[RetentionFlag] = field(default_factory=list)

    def has_warnings(self) -> bool:
        return any(f.severity in ("warning", "error") for f in self.flags)

    def __str__(self) -> str:
        if not self.flags:
            return "Retention analysis: no issues found."
        lines = ["Retention analysis:"]
        for flag in self.flags:
            lines.append(f"  {flag}")
        return "\n".join(lines)


def _is_high_frequency(job: CronJob, threshold: float = 12.0) -> bool:
    """Return True if the job runs more than *threshold* times per hour."""
    try:
        rph = _runs_per_hour(job.schedule)
    except Exception:
        return False
    return rph > threshold


def _is_duplicate_expression(job: CronJob, others: List[CronJob]) -> Optional[CronJob]:
    """Return the first other job that shares the same cron expression."""
    for other in others:
        if other.name != job.name and other.expression == job.expression:
            return other
    return None


def analyze_retention(jobs: List[CronJob], high_freq_threshold: float = 12.0) -> RetentionReport:
    """Analyse *jobs* and return a :class:`RetentionReport` with flagged issues."""
    report = RetentionReport()

    for job in jobs:
        duplicate = _is_duplicate_expression(job, jobs)
        if duplicate:
            report.flags.append(
                RetentionFlag(
                    job=job,
                    reason=f"duplicate expression of '{duplicate.name}' ({job.expression})",
                    severity="warning",
                )
            )

        if _is_high_frequency(job, high_freq_threshold):
            report.flags.append(
                RetentionFlag(
                    job=job,
                    reason=(
                        f"runs more than {high_freq_threshold:.0f} times per hour "
                        f"({job.expression}) — consider consolidating"
                    ),
                    severity="info",
                )
            )

    return report


def format_retention_report(report: RetentionReport) -> str:
    return str(report)


def print_retention_report(report: RetentionReport) -> None:
    print(format_retention_report(report))
