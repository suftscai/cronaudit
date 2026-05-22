"""Summarizes cron job statistics and schedule frequency analysis."""

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict

from cronaudit.loader import CronJob
from cronaudit.parser import CronSchedule


@dataclass
class ScheduleSummary:
    total_jobs: int = 0
    runs_per_hour: Dict[int, int] = field(default_factory=dict)
    runs_per_day: int = 0
    busiest_hour: int = -1
    least_busy_hour: int = -1
    frequency_label: str = "unknown"

    def __str__(self) -> str:
        return (
            f"Jobs: {self.total_jobs}, "
            f"Runs/day: {self.runs_per_day}, "
            f"Busiest hour: {self.busiest_hour:02d}:00, "
            f"Frequency: {self.frequency_label}"
        )


def _classify_frequency(schedule: CronSchedule) -> str:
    """Return a human-readable frequency label for a cron schedule."""
    total_slots = len(schedule.minutes) * len(schedule.hours)
    if total_slots >= 1440:
        return "every minute"
    elif total_slots >= 60:
        return "every hour"
    elif total_slots >= 24:
        return "multiple times/day"
    elif total_slots >= 1:
        return "daily"
    return "rare"


def _runs_per_hour(jobs: List[CronJob]) -> Dict[int, int]:
    """Count how many job executions occur in each hour across all jobs."""
    counts: Counter = Counter()
    for job in jobs:
        for hour in job.schedule.hours:
            counts[hour] += len(job.schedule.minutes)
    return {h: counts[h] for h in range(24)}


def summarize(jobs: List[CronJob]) -> ScheduleSummary:
    """Compute a ScheduleSummary for a list of CronJobs."""
    if not jobs:
        return ScheduleSummary()

    rph = _runs_per_hour(jobs)
    total_runs = sum(rph.values())
    busiest = max(rph, key=lambda h: rph[h])
    least = min(rph, key=lambda h: rph[h])

    # Use the first job's schedule for a representative frequency label
    freq = _classify_frequency(jobs[0].schedule)

    return ScheduleSummary(
        total_jobs=len(jobs),
        runs_per_hour=rph,
        runs_per_day=total_runs,
        busiest_hour=busiest,
        least_busy_hour=least,
        frequency_label=freq,
    )


def print_summary(jobs: List[CronJob]) -> None:
    """Print a formatted schedule summary to stdout."""
    summary = summarize(jobs)
    print("=== Schedule Summary ===")
    print(f"  Total jobs      : {summary.total_jobs}")
    print(f"  Total runs/day  : {summary.runs_per_day}")
    print(f"  Busiest hour    : {summary.busiest_hour:02d}:00 "
          f"({summary.runs_per_hour.get(summary.busiest_hour, 0)} runs)")
    print(f"  Quietest hour   : {summary.least_busy_hour:02d}:00 "
          f"({summary.runs_per_hour.get(summary.least_busy_hour, 0)} runs)")
    print(f"  Lead frequency  : {summary.frequency_label}")
