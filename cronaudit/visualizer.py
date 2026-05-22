"""ASCII timeline visualizer for cron job schedules."""

from typing import List
from cronaudit.loader import CronJob
from cronaudit.conflict import _compute_time_slots

HOURS = list(range(24))
BAR_CHAR = "█"
EMPTY_CHAR = "░"


def _job_active_hours(job: CronJob) -> set:
    """Return the set of hours (0-23) during which a job runs at least once."""
    slots = _compute_time_slots(job)
    return {hour for hour, _minute in slots}


def render_timeline(jobs: List[CronJob]) -> str:
    """Render a 24-hour ASCII timeline grid for the given jobs.

    Each row represents one job; each column represents one hour (0-23).
    Active hours are filled with BAR_CHAR, inactive with EMPTY_CHAR.

    Returns the timeline as a multi-line string.
    """
    if not jobs:
        return "(no jobs to display)"

    label_width = max(len(job.name) for job in jobs)
    header_labels = "".join(f"{h:02d}" for h in HOURS)
    header = " " * (label_width + 2) + header_labels

    lines = [header]
    separator = " " * (label_width + 2) + "--" * 24
    lines.append(separator)

    for job in jobs:
        active = _job_active_hours(job)
        bar = "".join(
            BAR_CHAR * 2 if h in active else EMPTY_CHAR * 2 for h in HOURS
        )
        label = job.name.ljust(label_width)
        lines.append(f"{label}  {bar}")

    return "\n".join(lines)


def print_timeline(jobs: List[CronJob]) -> None:
    """Print the 24-hour timeline to stdout."""
    print(render_timeline(jobs))
