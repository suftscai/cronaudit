"""Simulate cron job execution over a time window and collect run events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

from cronaudit.loader import CronJob
from cronaudit.scheduler import _matches


@dataclass
class SimulatedRun:
    job: CronJob
    timestamp: datetime

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M")
        return f"[{ts}] {self.job.name}"


@dataclass
class SimulationResult:
    start: datetime
    end: datetime
    runs: List[SimulatedRun] = field(default_factory=list)

    @property
    def total_runs(self) -> int:
        return len(self.runs)

    def runs_for_job(self, job: CronJob) -> List[SimulatedRun]:
        return [r for r in self.runs if r.job.name == job.name]

    def __str__(self) -> str:
        start_s = self.start.strftime("%Y-%m-%d %H:%M")
        end_s = self.end.strftime("%Y-%m-%d %H:%M")
        return (
            f"SimulationResult({self.total_runs} runs, "
            f"{start_s} -> {end_s})"
        )


def simulate(
    jobs: List[CronJob],
    start: datetime,
    end: datetime,
) -> SimulationResult:
    """Iterate every minute in [start, end) and record matching runs."""
    result = SimulationResult(start=start, end=end)
    current = start.replace(second=0, microsecond=0)
    while current < end:
        for job in jobs:
            if _matches(job.schedule, current):
                result.runs.append(SimulatedRun(job=job, timestamp=current))
        current += timedelta(minutes=1)
    return result


def format_simulation_report(result: SimulationResult) -> str:
    """Return a human-readable summary of the simulation result."""
    lines: List[str] = []
    start_s = result.start.strftime("%Y-%m-%d %H:%M")
    end_s = result.end.strftime("%Y-%m-%d %H:%M")
    lines.append(f"Simulation window: {start_s} -> {end_s}")
    lines.append(f"Total runs: {result.total_runs}")
    if not result.runs:
        lines.append("  (no runs scheduled in this window)")
    else:
        for run in result.runs:
            lines.append(f"  {run}")
    return "\n".join(lines)
