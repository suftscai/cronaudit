"""Tag cron jobs with descriptive labels based on their schedule and command."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from cronaudit.loader import CronJob
from cronaudit.summarizer import _classify_frequency, _runs_per_hour


@dataclass
class TaggedJob:
    job: CronJob
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "(no tags)"
        return f"{self.job.name}: [{tag_str}]"


_COMMAND_TAGS: Dict[str, str] = {
    "backup": "backup",
    "rsync": "backup",
    "dump": "backup",
    "log": "logging",
    "rotate": "maintenance",
    "clean": "maintenance",
    "purge": "maintenance",
    "report": "reporting",
    "mail": "notification",
    "send": "notification",
    "deploy": "deployment",
    "sync": "sync",
    "update": "update",
    "check": "monitoring",
    "monitor": "monitoring",
    "health": "monitoring",
}


def _command_tags(command: str) -> List[str]:
    """Derive tags from keywords found in the command string."""
    lower = command.lower()
    seen: Dict[str, bool] = {}
    result: List[str] = []
    for keyword, tag in _COMMAND_TAGS.items():
        if keyword in lower and tag not in seen:
            seen[tag] = True
            result.append(tag)
    return result


def _frequency_tag(job: CronJob) -> str:
    """Return a frequency label tag for the job."""
    schedule = job.schedule
    rph = _runs_per_hour(schedule)
    return _classify_frequency(schedule, rph)


def tag_job(job: CronJob) -> TaggedJob:
    """Produce a TaggedJob with all applicable tags for a single job."""
    tags: List[str] = []
    tags.append(_frequency_tag(job))
    tags.extend(_command_tags(job.command))
    return TaggedJob(job=job, tags=tags)


def tag_jobs(jobs: List[CronJob]) -> List[TaggedJob]:
    """Tag all jobs in a list."""
    return [tag_job(j) for j in jobs]


def format_tag_report(tagged: List[TaggedJob]) -> str:
    """Format a human-readable tag report."""
    if not tagged:
        return "No jobs to tag."
    lines = ["Tagged Jobs", "-" * 40]
    for tj in tagged:
        lines.append(str(tj))
    return "\n".join(lines)
