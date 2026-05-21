"""Detect conflicts and overlapping cron jobs."""

from dataclasses import dataclass, field
from typing import List, Tuple
from cronaudit.parser import CronSchedule


@dataclass
class Conflict:
    """Represents a detected conflict between two cron jobs."""
    job_a: str
    job_b: str
    overlapping_minutes: List[int]
    overlapping_hours: List[int]
    overlap_count: int

    def __str__(self) -> str:
        return (
            f"Conflict: '{self.job_a}' <-> '{self.job_b}' "
            f"| {self.overlap_count} overlapping time slot(s)"
        )


def _compute_time_slots(schedule: CronSchedule) -> set:
    """Compute all (hour, minute) slots for a schedule."""
    slots = set()
    for hour in schedule.hours:
        for minute in schedule.minutes:
            slots.add((hour, minute))
    return slots


def detect_conflicts(jobs: List[Tuple[str, CronSchedule]]) -> List[Conflict]:
    """
    Given a list of (name, CronSchedule) tuples, return all pairwise conflicts.

    Two jobs conflict if they share at least one (hour, minute) time slot.
    """
    conflicts = []
    indexed = [(name, sched, _compute_time_slots(sched)) for name, sched in jobs]

    for i in range(len(indexed)):
        for j in range(i + 1, len(indexed)):
            name_a, sched_a, slots_a = indexed[i]
            name_b, sched_b, slots_b = indexed[j]

            overlap = slots_a & slots_b
            if overlap:
                overlap_minutes = sorted({m for _, m in overlap})
                overlap_hours = sorted({h for h, _ in overlap})
                conflicts.append(
                    Conflict(
                        job_a=name_a,
                        job_b=name_b,
                        overlapping_minutes=overlap_minutes,
                        overlapping_hours=overlap_hours,
                        overlap_count=len(overlap),
                    )
                )
    return conflicts
