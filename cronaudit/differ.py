"""Compares two crontab files and reports added, removed, and changed jobs."""

from dataclasses import dataclass, field
from typing import List, Tuple
from cronaudit.loader import CronJob


@dataclass
class CrontabDiff:
    added: List[CronJob] = field(default_factory=list)
    removed: List[CronJob] = field(default_factory=list)
    changed: List[Tuple[CronJob, CronJob]] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def __str__(self) -> str:
        lines = []
        for job in self.added:
            lines.append(f"+ {job.name}: {job.expression}")
        for job in self.removed:
            lines.append(f"- {job.name}: {job.expression}")
        for old, new in self.changed:
            lines.append(f"~ {old.name}: {old.expression} -> {new.expression}")
        return "\n".join(lines) if lines else "No changes detected."


def _index_jobs(jobs: List[CronJob]) -> dict:
    """Index jobs by name for fast lookup."""
    return {job.name: job for job in jobs}


def diff_crontabs(old_jobs: List[CronJob], new_jobs: List[CronJob]) -> CrontabDiff:
    """Compare two lists of CronJobs and return a CrontabDiff."""
    old_index = _index_jobs(old_jobs)
    new_index = _index_jobs(new_jobs)

    added = [job for name, job in new_index.items() if name not in old_index]
    removed = [job for name, job in old_index.items() if name not in new_index]
    changed = [
        (old_index[name], new_job)
        for name, new_job in new_index.items()
        if name in old_index and old_index[name].expression != new_job.expression
    ]

    return CrontabDiff(added=added, removed=removed, changed=changed)
