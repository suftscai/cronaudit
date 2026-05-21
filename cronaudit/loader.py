"""Load cron job definitions from a crontab-style file or string."""

from typing import List, Tuple
from cronaudit.parser import CronSchedule, parse_cron_expression


class CronJob:
    """Represents a single cron job entry."""

    def __init__(self, name: str, expression: str, command: str):
        self.name = name
        self.expression = expression
        self.command = command
        self.schedule: CronSchedule = parse_cron_expression(expression)

    def __repr__(self) -> str:
        return f"CronJob(name={self.name!r}, expression={self.expression!r})"


def load_from_string(content: str) -> List[CronJob]:
    """
    Parse cron jobs from a multi-line string.

    Each non-comment, non-empty line is expected in the format:
        <minute> <hour> <dom> <month> <dow> <command>

    The job name is derived from the command (first token).
    Lines starting with '#' are treated as comments.
    """
    jobs = []
    for lineno, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            raise ValueError(
                f"Line {lineno}: expected 5 schedule fields + command, got: {line!r}"
            )
        expression = " ".join(parts[:5])
        command = parts[5]
        name = command.split()[0].split("/")[-1]  # basename of command
        jobs.append(CronJob(name=name, expression=expression, command=command))
    return jobs


def load_from_file(path: str) -> List[CronJob]:
    """Load cron jobs from a crontab file on disk."""
    with open(path, "r", encoding="utf-8") as fh:
        return load_from_string(fh.read())


def jobs_to_schedule_pairs(jobs: List[CronJob]) -> List[Tuple[str, "CronSchedule"]]:
    """Convert a list of CronJob objects to (name, CronSchedule) pairs."""
    return [(job.name, job.schedule) for job in jobs]
