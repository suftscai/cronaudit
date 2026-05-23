"""Agenda: formats upcoming job runs into a human-readable schedule view."""

from __future__ import annotations

from datetime import datetime
from typing import List

from cronaudit.loader import CronJob
from cronaudit.scheduler import NextRun, next_runs

_DATE_FMT = "%a %Y-%m-%d %H:%M"
_COL_WIDTH = 22


def format_agenda(runs: List[NextRun]) -> str:
    """Return a formatted agenda table for the given *runs*."""
    if not runs:
        return "(no upcoming runs)"

    header = f"{'TIME':<{_COL_WIDTH}}  JOB"
    separator = "-" * (len(header) + 10)
    lines = [header, separator]
    for nr in runs:
        time_str = nr.run_at.strftime(_DATE_FMT)
        lines.append(f"{time_str:<{_COL_WIDTH}}  {nr.job.name}")
    return "\n".join(lines)


def print_agenda(
    jobs: List[CronJob],
    after: datetime | None = None,
    count: int = 10,
) -> None:  # pragma: no cover
    """Print the next *count* runs across *jobs* to stdout."""
    runs = next_runs(jobs, after=after, count=count)
    print(format_agenda(runs))
