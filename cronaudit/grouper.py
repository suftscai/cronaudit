"""Groups cron jobs by shared schedule expression or frequency bucket."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from cronaudit.loader import CronJob
from cronaudit.summarizer import _classify_frequency, _runs_per_hour


@dataclass
class JobGroup:
    """A collection of jobs that share the same grouping key."""

    key: str
    jobs: List[CronJob] = field(default_factory=list)

    def __str__(self) -> str:
        job_names = ", ".join(j.name for j in self.jobs)
        return f"[{self.key}] ({len(self.jobs)} job(s)): {job_names}"


def group_by_expression(jobs: List[CronJob]) -> Dict[str, JobGroup]:
    """Group jobs that share an identical cron expression."""
    groups: Dict[str, JobGroup] = {}
    for job in jobs:
        expr = job.schedule.expression
        if expr not in groups:
            groups[expr] = JobGroup(key=expr)
        groups[expr].jobs.append(job)
    return groups


def group_by_frequency(jobs: List[CronJob]) -> Dict[str, JobGroup]:
    """Group jobs by their human-readable frequency classification."""
    groups: Dict[str, JobGroup] = {}
    for job in jobs:
        try:
            rph = _runs_per_hour(job.schedule)
            label = _classify_frequency(job.schedule, rph)
        except Exception:
            label = "unknown"
        if label not in groups:
            groups[label] = JobGroup(key=label)
        groups[label].jobs.append(job)
    return groups


def format_group_report(groups: Dict[str, JobGroup], title: str = "Job Groups") -> str:
    """Render a human-readable report of grouped jobs."""
    if not groups:
        return f"=== {title} ===\n(no groups)"

    lines = [f"=== {title} ==="]
    for group in sorted(groups.values(), key=lambda g: (-len(g.jobs), g.key)):
        lines.append(str(group))
        for job in group.jobs:
            lines.append(f"    - {job.name}  [{job.schedule.expression}]")
    return "\n".join(lines)


def print_group_report(groups: Dict[str, JobGroup], title: str = "Job Groups") -> None:
    """Print the group report to stdout."""
    print(format_group_report(groups, title=title))
