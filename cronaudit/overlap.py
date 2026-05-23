"""Detects and reports time-based overlaps between cron jobs within a rolling window."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Tuple

from cronaudit.loader import CronJob
from cronaudit.scheduler import next_runs


@dataclass
class OverlapWindow:
    """Represents two jobs whose scheduled runs overlap within a time window."""

    job_a: CronJob
    job_b: CronJob
    overlapping_times: List[datetime] = field(default_factory=list)

    def __str__(self) -> str:
        times = ", ".join(t.strftime("%Y-%m-%d %H:%M") for t in self.overlapping_times[:3])
        suffix = f" (+{len(self.overlapping_times) - 3} more)" if len(self.overlapping_times) > 3 else ""
        return (
            f"OVERLAP: '{self.job_a.name}' and '{self.job_b.name}' "
            f"share {len(self.overlapping_times)} run(s): {times}{suffix}"
        )


def _collect_run_times(job: CronJob, start: datetime, count: int) -> List[datetime]:
    """Return up to `count` next run datetimes for a job starting from `start`."""
    runs = next_runs(job, start, count)
    return [r.scheduled_time for r in runs]


def find_overlaps(
    jobs: List[CronJob],
    start: datetime,
    lookahead_minutes: int = 1440,
    sample_size: int = 200,
) -> List[OverlapWindow]:
    """Find all pairs of jobs that share at least one run time within the window.

    Args:
        jobs: List of cron jobs to compare.
        start: Starting datetime for the analysis window.
        lookahead_minutes: How many minutes ahead to analyse (default: 1 day).
        sample_size: Number of future runs to sample per job.

    Returns:
        List of OverlapWindow instances for each overlapping pair.
    """
    end = start + timedelta(minutes=lookahead_minutes)
    run_map: dict[str, List[datetime]] = {}

    for job in jobs:
        times = _collect_run_times(job, start, sample_size)
        run_map[job.name] = [t for t in times if t <= end]

    overlaps: List[OverlapWindow] = []

    for i, job_a in enumerate(jobs):
        for job_b in jobs[i + 1 :]:
            set_a = set(run_map[job_a.name])
            set_b = set(run_map[job_b.name])
            shared = sorted(set_a & set_b)
            if shared:
                overlaps.append(
                    OverlapWindow(job_a=job_a, job_b=job_b, overlapping_times=shared)
                )

    return overlaps


def format_overlap_report(overlaps: List[OverlapWindow]) -> str:
    """Return a human-readable summary of detected overlaps."""
    if not overlaps:
        return "No overlapping jobs detected."
    lines = [f"Detected {len(overlaps)} overlapping job pair(s):", ""]
    for ow in overlaps:
        lines.append(f"  {ow}")
    return "\n".join(lines)
