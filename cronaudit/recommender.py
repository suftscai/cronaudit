"""Recommends schedule adjustments to reduce conflicts and spread load."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronaudit.loader import CronJob
from cronaudit.conflict import detect_conflicts
from cronaudit.profiler import _slots_per_day


@dataclass
class Recommendation:
    job_name: str
    reason: str
    suggestion: str
    severity: str = "info"  # info | warning | critical

    def __str__(self) -> str:
        tag = f"[{self.severity.upper()}]"
        return f"{tag} {self.job_name}: {self.reason} -> {self.suggestion}"


@dataclass
class RecommendationReport:
    recommendations: List[Recommendation] = field(default_factory=list)

    def has_suggestions(self) -> bool:
        return len(self.recommendations) > 0

    def __str__(self) -> str:
        if not self.recommendations:
            return "No recommendations — schedules look healthy."
        lines = [f"Recommendations ({len(self.recommendations)}):"] + [
            f"  {r}" for r in self.recommendations
        ]
        return "\n".join(lines)


_HIGH_FREQUENCY_THRESHOLD = 48  # slots per day
_CONFLICT_SEVERITY = "warning"
_HIGH_FREQ_SEVERITY = "info"


def _recommend_for_conflicts(jobs: List[CronJob]) -> List[Recommendation]:
    recs: List[Recommendation] = []
    conflicts = detect_conflicts(jobs)
    seen_pairs: set = set()
    for conflict in conflicts:
        names = tuple(sorted(j.name for j in conflict.jobs))
        if names in seen_pairs:
            continue
        seen_pairs.add(names)
        label = " & ".join(names)
        recs.append(
            Recommendation(
                job_name=label,
                reason=f"Jobs share {conflict.slot_count} overlapping time slot(s)",
                suggestion="Stagger start times by at least 5 minutes to avoid resource contention",
                severity=_CONFLICT_SEVERITY,
            )
        )
    return recs


def _recommend_for_high_frequency(jobs: List[CronJob]) -> List[Recommendation]:
    recs: List[Recommendation] = []
    for job in jobs:
        slots = _slots_per_day(job.schedule)
        if slots >= _HIGH_FREQUENCY_THRESHOLD:
            recs.append(
                Recommendation(
                    job_name=job.name,
                    reason=f"Runs {slots} times per day (high frequency)",
                    suggestion="Consider batching work or increasing the interval to reduce system load",
                    severity=_HIGH_FREQ_SEVERITY,
                )
            )
    return recs


def recommend(jobs: List[CronJob]) -> RecommendationReport:
    """Analyse jobs and return a report of actionable recommendations."""
    recs: List[Recommendation] = []
    recs.extend(_recommend_for_conflicts(jobs))
    recs.extend(_recommend_for_high_frequency(jobs))
    return RecommendationReport(recommendations=recs)
