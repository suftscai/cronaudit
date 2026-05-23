"""Generates a day-of-week × hour heatmap showing job activity density."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronaudit.loader import CronJob

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOURS = list(range(24))

# cron dow: 0=Sun,1=Mon,...,6=Sat (also 7=Sun)
_CRON_TO_INDEX = {0: 6, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}


@dataclass
class Heatmap:
    """7-day × 24-hour activity matrix."""

    grid: List[List[int]] = field(
        default_factory=lambda: [[0] * 24 for _ in range(7)]
    )

    def increment(self, day_index: int, hour: int) -> None:
        self.grid[day_index][hour] += 1

    def max_value(self) -> int:
        return max(v for row in self.grid for v in row)


def build_heatmap(jobs: List[CronJob]) -> Heatmap:
    """Populate a Heatmap from a list of CronJob objects."""
    hm = Heatmap()
    for job in jobs:
        schedule = job.schedule
        for dow_cron in schedule.day_of_week:
            day_idx = _CRON_TO_INDEX.get(dow_cron % 8, dow_cron % 7)
            for hour in schedule.hours:
                hm.increment(day_idx, hour)
    return hm


def render_heatmap(jobs: List[CronJob]) -> str:
    """Return a text heatmap string."""
    if not jobs:
        return "(no jobs to display)"

    hm = build_heatmap(jobs)
    max_val = hm.max_value() or 1
    shades = " ░▒▓█"

    hour_header = "     " + "".join(f"{h:02d} " for h in HOURS)
    sep = "     " + "---" * 24
    lines = [hour_header, sep]

    for day_idx, day_name in enumerate(DAYS):
        row_parts = []
        for hour in HOURS:
            count = hm.grid[day_idx][hour]
            shade_idx = int(count / max_val * (len(shades) - 1))
            row_parts.append(f" {shades[shade_idx]} ")
        lines.append(f"{day_name}  {''.join(row_parts)}")

    return "\n".join(lines)


def print_heatmap(jobs: List[CronJob]) -> None:
    """Print the heatmap to stdout."""
    print(render_heatmap(jobs))
