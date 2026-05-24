"""Profiles cron jobs by estimating resource contention based on schedule density."""

from dataclasses import dataclass, field
from typing import List, Dict
from cronaudit.loader import CronJob
from cronaudit.conflict import _compute_time_slots


@dataclass
class ProfileResult:
    job: CronJob
    slots_per_day: int
    contention_score: float  # 0.0 (no contention) to 1.0 (max contention)
    peak_hours: List[int] = field(default_factory=list)

    def __str__(self) -> str:
        peaks = ", ".join(f"{h:02d}:xx" for h in self.peak_hours) or "none"
        return (
            f"{self.job.name}: {self.slots_per_day} slots/day, "
            f"contention={self.contention_score:.2f}, peaks=[{peaks}]"
        )


def _slots_per_day(job: CronJob) -> int:
    """Count how many times a job runs per day (minute-level granularity)."""
    slots = _compute_time_slots(job)
    return len(slots)


def _build_hourly_density(jobs: List[CronJob]) -> Dict[int, int]:
    """Count total job runs per hour across all jobs."""
    density: Dict[int, int] = {h: 0 for h in range(24)}
    for job in jobs:
        for (hour, _minute) in _compute_time_slots(job):
            density[hour] += 1
    return density


def _peak_hours_for_job(job: CronJob, density: Dict[int, int], threshold: float = 0.75) -> List[int]:
    """Return hours where the job runs and global density is above threshold."""
    if not density:
        return []
    max_density = max(density.values()) or 1
    cutoff = max_density * threshold
    peaks = []
    for (hour, _minute) in _compute_time_slots(job):
        if density.get(hour, 0) >= cutoff and hour not in peaks:
            peaks.append(hour)
    return sorted(peaks)


def profile_jobs(jobs: List[CronJob]) -> List[ProfileResult]:
    """Profile each job for schedule density and contention."""
    if not jobs:
        return []
    density = _build_hourly_density(jobs)
    max_density = max(density.values()) or 1
    results = []
    for job in jobs:
        spd = _slots_per_day(job)
        job_slots = _compute_time_slots(job)
        if job_slots:
            job_hours = {h for (h, _) in job_slots}
            avg_contention = sum(density[h] for h in job_hours) / (len(job_hours) * max_density)
        else:
            avg_contention = 0.0
        peaks = _peak_hours_for_job(job, density)
        results.append(ProfileResult(
            job=job,
            slots_per_day=spd,
            contention_score=round(min(avg_contention, 1.0), 4),
            peak_hours=peaks,
        ))
    results.sort(key=lambda r: r.contention_score, reverse=True)
    return results


def format_profile_report(results: List[ProfileResult]) -> str:
    """Render a human-readable profile report."""
    if not results:
        return "No jobs to profile."
    lines = ["=== Cron Job Profile Report ==="]
    for r in results:
        lines.append(f"  {r}")
    return "\n".join(lines)
