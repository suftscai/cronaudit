"""Detect and represent dependencies between cron jobs based on shared resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Set

from cronaudit.loader import CronJob


@dataclass
class JobDependency:
    """Represents a suspected dependency between two cron jobs."""

    source: CronJob
    target: CronJob
    shared_tokens: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tokens = ", ".join(self.shared_tokens) if self.shared_tokens else "(none)"
        return (
            f"{self.source.name} -> {self.target.name} "
            f"[shared: {tokens}]"
        )


def _tokenize_command(command: str) -> Set[str]:
    """Extract meaningful tokens from a command string."""
    skip = {"", "&&", "||", "|", ";", ">", ">>", "<", "2>&1"}
    tokens: Set[str] = set()
    for part in command.replace(";", " ").replace("&&", " ").replace("||", " ").split():
        cleaned = part.strip("/").lstrip("-")
        if cleaned and cleaned not in skip and len(cleaned) > 2:
            tokens.add(cleaned.lower())
    return tokens


def find_dependencies(jobs: List[CronJob]) -> List[JobDependency]:
    """Find pairs of jobs that share command tokens, suggesting a dependency."""
    token_map: Dict[int, Set[str]] = {
        i: _tokenize_command(job.command) for i, job in enumerate(jobs)
    }
    dependencies: List[JobDependency] = []
    for i in range(len(jobs)):
        for j in range(i + 1, len(jobs)):
            shared = token_map[i] & token_map[j]
            if shared:
                dependencies.append(
                    JobDependency(
                        source=jobs[i],
                        target=jobs[j],
                        shared_tokens=sorted(shared),
                    )
                )
    return dependencies


def format_dependency_report(dependencies: List[JobDependency]) -> str:
    """Render a human-readable dependency report."""
    if not dependencies:
        return "No suspected dependencies found."
    lines = [f"Suspected dependencies ({len(dependencies)} pair(s)):"]
    for dep in dependencies:
        lines.append(f"  {dep}")
    return "\n".join(lines)
