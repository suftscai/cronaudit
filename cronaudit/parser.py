"""Cron expression parser module.

Parses standard 5-field cron expressions into structured schedule objects.
Supports wildcards (*), ranges (1-5), steps (*/2), and lists (1,3,5).
"""

from dataclasses import dataclass, field
from typing import List, Optional


FIELD_NAMES = ["minute", "hour", "day_of_month", "month", "day_of_week"]
FIELD_RANGES = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 6),
}


@dataclass
class CronSchedule:
    """Represents a parsed cron schedule."""

    expression: str
    command: str
    minute: List[int] = field(default_factory=list)
    hour: List[int] = field(default_factory=list)
    day_of_month: List[int] = field(default_factory=list)
    month: List[int] = field(default_factory=list)
    day_of_week: List[int] = field(default_factory=list)

    def __str__(self) -> str:
        return f"CronSchedule({self.expression!r}, command={self.command!r})"


def _expand_field(value: str, field_name: str) -> List[int]:
    """Expand a single cron field into a sorted list of integers."""
    min_val, max_val = FIELD_RANGES[field_name]
    result = set()

    for part in value.split(","):
        if "/" in part:
            range_part, step_str = part.split("/", 1)
            step = int(step_str)
            if range_part == "*":
                start, end = min_val, max_val
            elif "-" in range_part:
                start, end = map(int, range_part.split("-", 1))
            else:
                start = end = int(range_part)
            result.update(range(start, end + 1, step))
        elif part == "*":
            result.update(range(min_val, max_val + 1))
        elif "-" in part:
            start, end = map(int, part.split("-", 1))
            result.update(range(start, end + 1))
        else:
            result.add(int(part))

    return sorted(result)


def parse_cron_expression(expression: str, command: Optional[str] = "") -> CronSchedule:
    """Parse a cron expression string into a CronSchedule object.

    Args:
        expression: A standard 5-field cron expression (e.g. '*/5 * * * *').
        command: Optional command string associated with this schedule.

    Returns:
        A CronSchedule with expanded field lists.

    Raises:
        ValueError: If the expression does not have exactly 5 fields.
    """
    fields = expression.strip().split()
    if len(fields) != 5:
        raise ValueError(
            f"Invalid cron expression {expression!r}: expected 5 fields, got {len(fields)}"
        )

    schedule = CronSchedule(expression=expression, command=command or "")
    for field_name, value in zip(FIELD_NAMES, fields):
        setattr(schedule, field_name, _expand_field(value, field_name))

    return schedule
