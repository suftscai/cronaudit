"""Next-run scheduler: computes upcoming execution times for cron jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from cronaudit.loader import CronJob


@dataclass
class NextRun:
    job: CronJob
    run_at: datetime

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.job.name!r} next runs at {self.run_at.strftime('%Y-%m-%d %H:%M')}"


def _matches(dt: datetime, job: CronJob) -> bool:
    """Return True when *dt* (minute-precision) satisfies the job's schedule."""
    s = job.schedule
    return (
        dt.minute in s.minutes
        and dt.hour in s.hours
        and dt.day in s.days
        and dt.month in s.months
        and dt.weekday() in {wd % 7 for wd in s.weekdays}  # 0=Mon in Python, 0=Sun in cron
    )


def next_run(job: CronJob, after: datetime | None = None) -> NextRun:
    """Return the first minute at or after *after* when *job* will execute.

    Searches up to 366 days ahead; raises ``ValueError`` if no match is found.
    """
    start = (after or datetime.now()).replace(second=0, microsecond=0)
    candidate = start
    limit = start + timedelta(days=366)
    while candidate <= limit:
        if _matches(candidate, job):
            return NextRun(job=job, run_at=candidate)
        candidate += timedelta(minutes=1)
    raise ValueError(f"No execution time found for job {job.name!r} within 366 days")


def next_runs(jobs: List[CronJob], after: datetime | None = None, count: int = 5) -> List[NextRun]:
    """Return the *count* soonest upcoming runs across all *jobs*, sorted by time."""
    results: List[NextRun] = []
    for job in jobs:
        cursor = after
        for _ in range(count):
            nr = next_run(job, after=cursor)
            results.append(nr)
            cursor = nr.run_at + timedelta(minutes=1)
    results.sort(key=lambda r: r.run_at)
    return results[:count]
