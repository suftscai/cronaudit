"""Format conflict reports for display."""

from typing import List
from cronaudit.conflict import Conflict


def _pluralize(count: int, word: str) -> str:
    return f"{count} {word}{'s' if count != 1 else ''}"


def format_conflict(conflict: Conflict) -> str:
    """Return a human-readable single-conflict summary."""
    hours_str = ", ".join(str(h) for h in conflict.overlapping_hours)
    minutes_str = ", ".join(str(m) for m in conflict.overlapping_minutes)
    return (
        f"  ⚠  {conflict.job_a!r} conflicts with {conflict.job_b!r}\n"
        f"     Overlap: {_pluralize(conflict.overlap_count, 'slot')} "
        f"| hours=[{hours_str}] minutes=[{minutes_str}]"
    )


def format_report(conflicts: List[Conflict], total_jobs: int) -> str:
    """Return a full conflict report as a printable string."""
    lines = [
        "=" * 60,
        "CronAudit Conflict Report",
        "=" * 60,
        f"Jobs analysed : {total_jobs}",
        f"Conflicts found: {len(conflicts)}",
        "-" * 60,
    ]
    if not conflicts:
        lines.append("  ✓ No conflicts detected.")
    else:
        for conflict in conflicts:
            lines.append(format_conflict(conflict))
            lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def print_report(conflicts: List[Conflict], total_jobs: int) -> None:
    """Print the conflict report to stdout."""
    print(format_report(conflicts, total_jobs))
