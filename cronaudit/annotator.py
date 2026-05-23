"""Annotates cron jobs with human-readable descriptions of their schedules."""

from dataclasses import dataclass, field
from typing import List

from cronaudit.loader import CronJob
from cronaudit.parser import CronSchedule


@dataclass
class AnnotatedJob:
    job: CronJob
    description: str
    notes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [f"{self.job.name}: {self.description}"]
        for note in self.notes:
            lines.append(f"  * {note}")
        return "\n".join(lines)


def _describe_field(values: List[int], unit: str, total: int) -> str:
    """Return a short description of an expanded cron field."""
    if len(values) == total:
        return f"every {unit}"
    if len(values) == 1:
        return f"at {unit} {values[0]}"
    if values == list(range(values[0], values[-1] + 1)):
        return f"every {unit} from {values[0]} to {values[-1]}"
    return f"at {unit}s {', '.join(str(v) for v in values)}"


def _build_notes(schedule: CronSchedule) -> List[str]:
    notes = []
    if len(schedule.minutes) == 60 and len(schedule.hours) == 24:
        notes.append("Runs every minute of every hour — high frequency")
    if len(schedule.minutes) > 30:
        notes.append("Runs more than once per hour")
    if 0 in schedule.hours and len(schedule.hours) == 1:
        notes.append("Runs only at midnight")
    if set(schedule.days_of_week) == {0, 6}:
        notes.append("Weekend-only schedule")
    if set(schedule.days_of_week) == {1, 2, 3, 4, 5}:
        notes.append("Weekday-only schedule")
    return notes


def describe_schedule(schedule: CronSchedule) -> str:
    """Produce a human-readable description of a CronSchedule."""
    minute_desc = _describe_field(schedule.minutes, "minute", 60)
    hour_desc = _describe_field(schedule.hours, "hour", 24)
    dom_desc = _describe_field(schedule.days_of_month, "day-of-month", 31)
    dow_desc = _describe_field(schedule.days_of_week, "day-of-week", 7)

    parts = [minute_desc, hour_desc]
    if len(schedule.days_of_month) < 31:
        parts.append(dom_desc)
    if len(schedule.days_of_week) < 7:
        parts.append(dow_desc)

    return "; ".join(parts)


def annotate_job(job: CronJob) -> AnnotatedJob:
    """Annotate a single CronJob with a description and notes."""
    description = describe_schedule(job.schedule)
    notes = _build_notes(job.schedule)
    return AnnotatedJob(job=job, description=description, notes=notes)


def annotate_jobs(jobs: List[CronJob]) -> List[AnnotatedJob]:
    """Annotate a list of CronJobs."""
    return [annotate_job(job) for job in jobs]


def format_annotation_report(annotated: List[AnnotatedJob]) -> str:
    """Format all annotated jobs into a printable report."""
    if not annotated:
        return "(no jobs to annotate)"
    return "\n\n".join(str(a) for a in annotated)
