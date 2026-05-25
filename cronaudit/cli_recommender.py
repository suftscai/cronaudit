"""CLI sub-command: recommend — surface schedule improvement suggestions."""

from __future__ import annotations

import argparse
import sys
from typing import List

from cronaudit.loader import load_from_file
from cronaudit.recommender import recommend


def add_recommender_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *recommend* sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "recommend",
        help="Analyse schedules and print improvement recommendations",
    )
    parser.add_argument(
        "crontab",
        metavar="CRONTAB",
        help="Path to crontab file to analyse",
    )
    parser.add_argument(
        "--severity",
        choices=["info", "warning", "critical"],
        default=None,
        help="Only show recommendations at or above this severity",
    )
    parser.set_defaults(func=_run_recommender)


_SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}


def _run_recommender(args: argparse.Namespace) -> int:
    try:
        jobs = load_from_file(args.crontab)
    except (OSError, ValueError) as exc:
        print(f"Error loading crontab: {exc}", file=sys.stderr)
        return 1

    report = recommend(jobs)

    recs = report.recommendations
    if args.severity is not None:
        min_level = _SEVERITY_ORDER[args.severity]
        recs = [
            r for r in recs
            if _SEVERITY_ORDER.get(r.severity, 0) >= min_level
        ]

    if not recs:
        print("No recommendations — schedules look healthy.")
        return 0

    print(f"Recommendations ({len(recs)}):")
    for rec in recs:
        print(f"  {rec}")
    return 0
