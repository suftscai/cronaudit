"""Baseline snapshot: save and compare cron job sets over time."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict

from cronaudit.loader import CronJob


@dataclass
class BaselineSnapshot:
    """A saved snapshot of cron jobs at a point in time."""
    label: str
    jobs: List[Dict[str, str]] = field(default_factory=list)

    def __str__(self) -> str:
        count = len(self.jobs)
        return f"BaselineSnapshot('{self.label}', {count} job{'s' if count != 1 else ''})"


def snapshot_from_jobs(label: str, jobs: List[CronJob]) -> BaselineSnapshot:
    """Create a BaselineSnapshot from a list of CronJob instances."""
    return BaselineSnapshot(
        label=label,
        jobs=[{"name": j.name, "expression": j.schedule.expression} for j in jobs],
    )


def save_baseline(snapshot: BaselineSnapshot, path: str | Path) -> None:
    """Persist a snapshot to a JSON file."""
    data = {"label": snapshot.label, "jobs": snapshot.jobs}
    Path(path).write_text(json.dumps(data, indent=2))


def load_baseline(path: str | Path) -> BaselineSnapshot:
    """Load a previously saved snapshot from a JSON file."""
    raw = json.loads(Path(path).read_text())
    return BaselineSnapshot(label=raw["label"], jobs=raw["jobs"])


@dataclass
class BaselineDiff:
    """Differences between the current job list and a saved baseline."""
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def __str__(self) -> str:
        if not self.has_changes:
            return "No changes from baseline."
        lines = []
        for name in self.added:
            lines.append(f"  + {name} (added)")
        for name in self.removed:
            lines.append(f"  - {name} (removed)")
        for name in self.changed:
            lines.append(f"  ~ {name} (changed)")
        return "\n".join(lines)


def compare_to_baseline(
    jobs: List[CronJob], snapshot: BaselineSnapshot
) -> BaselineDiff:
    """Compare current jobs against a saved baseline snapshot."""
    current = {j.name: j.schedule.expression for j in jobs}
    baseline = {entry["name"]: entry["expression"] for entry in snapshot.jobs}

    added = [name for name in current if name not in baseline]
    removed = [name for name in baseline if name not in current]
    changed = [
        name
        for name in current
        if name in baseline and current[name] != baseline[name]
    ]
    return BaselineDiff(added=added, removed=removed, changed=changed)
