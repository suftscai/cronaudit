"""Export cron audit results to various formats (JSON, CSV)."""

import csv
import json
import io
from typing import List

from cronaudit.loader import CronJob
from cronaudit.conflict import Conflict


def jobs_to_dict(jobs: List[CronJob]) -> List[dict]:
    """Convert a list of CronJob objects to serializable dicts."""
    return [
        {
            "name": job.name,
            "expression": job.schedule.expression,
            "command": job.command,
        }
        for job in jobs
    ]


def conflicts_to_dict(conflicts: List[Conflict]) -> List[dict]:
    """Convert a list of Conflict objects to serializable dicts."""
    return [
        {
            "job_a": c.job_a.name,
            "job_b": c.job_b.name,
            "overlapping_slots": len(c.overlapping_slots),
        }
        for c in conflicts
    ]


def export_json(jobs: List[CronJob], conflicts: List[Conflict]) -> str:
    """Export jobs and conflicts as a JSON string."""
    payload = {
        "jobs": jobs_to_dict(jobs),
        "conflicts": conflicts_to_dict(conflicts),
    }
    return json.dumps(payload, indent=2)


def export_csv(jobs: List[CronJob], conflicts: List[Conflict]) -> str:
    """Export conflicts as a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["job_a", "job_b", "overlapping_slots"])
    for row in conflicts_to_dict(conflicts):
        writer.writerow([row["job_a"], row["job_b"], row["overlapping_slots"]])
    return output.getvalue()


def write_export(path: str, jobs: List[CronJob], conflicts: List[Conflict]) -> None:
    """Write export to a file; format inferred from extension (.json or .csv)."""
    if path.endswith(".json"):
        content = export_json(jobs, conflicts)
    elif path.endswith(".csv"):
        content = export_csv(jobs, conflicts)
    else:
        raise ValueError(f"Unsupported export format for path: {path}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
