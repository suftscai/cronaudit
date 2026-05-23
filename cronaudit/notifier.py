"""Notification rules: flag jobs that match user-defined alert criteria."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronaudit.loader import CronJob
from cronaudit.summarizer import _classify_frequency


@dataclass
class NotificationRule:
    """A rule that triggers an alert when matched by a cron job."""
    name: str
    frequency: Optional[str] = None   # e.g. 'every_minute', 'every_hour'
    command_contains: Optional[str] = None

    def matches(self, job: CronJob) -> bool:
        if self.command_contains and self.command_contains not in job.command:
            return False
        if self.frequency:
            freq = _classify_frequency(job.schedule)
            if freq != self.frequency:
                return False
        return True


@dataclass
class Notification:
    """An alert produced when a job matches a rule."""
    rule_name: str
    job: CronJob

    def __str__(self) -> str:
        return f"[{self.rule_name}] {self.job.name} ({self.job.expression})"


def evaluate_rules(
    jobs: List[CronJob],
    rules: List[NotificationRule],
) -> List[Notification]:
    """Return a Notification for every (job, rule) pair that matches."""
    notifications: List[Notification] = []
    for job in jobs:
        for rule in rules:
            if rule.matches(job):
                notifications.append(Notification(rule_name=rule.name, job=job))
    return notifications


def format_notification_report(notifications: List[Notification]) -> str:
    """Render a human-readable report of all notifications."""
    if not notifications:
        return "No notifications triggered."
    lines = [f"Notifications ({len(notifications)} triggered):", ""]
    for n in notifications:
        lines.append(f"  {n}")
    return "\n".join(lines)
