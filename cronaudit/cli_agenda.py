"""CLI sub-command helpers for the 'agenda' feature.

Integrates with the existing ``cronaudit.cli`` build_parser / main pipeline.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import List

from cronaudit.loader import load_from_file
from cronaudit.scheduler import next_runs
from cronaudit.agenda import format_agenda


def add_agenda_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *agenda* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "agenda",
        help="Show the next N upcoming cron runs across all jobs.",
    )
    p.add_argument("file", help="Path to crontab file")
    p.add_argument(
        "-n",
        "--count",
        type=int,
        default=10,
        metavar="N",
        help="Number of upcoming runs to display (default: 10)",
    )
    p.add_argument(
        "--after",
        type=lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M"),
        default=None,
        metavar="DATETIME",
        help="Start from this datetime (ISO format: YYYY-MM-DDTHH:MM)",
    )
    p.set_defaults(func=_run_agenda)


def _run_agenda(args: argparse.Namespace) -> int:
    """Handler called when the *agenda* sub-command is invoked."""
    jobs = load_from_file(args.file)
    runs = next_runs(jobs, after=args.after, count=args.count)
    print(format_agenda(runs))
    return 0
