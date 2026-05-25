"""CLI subcommand: cronaudit retention.

Analyses a crontab file for retention issues such as duplicate schedules
or excessively high-frequency jobs.
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from cronaudit.loader import load_from_file
from cronaudit.retention import analyze_retention, print_retention_report


def add_retention_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the *retention* subcommand on *subparsers*."""
    parser = subparsers.add_parser(
        "retention",
        help="Detect duplicate or excessively frequent cron jobs.",
    )
    parser.add_argument(
        "crontab",
        metavar="CRONTAB",
        help="Path to the crontab file to analyse.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=12.0,
        metavar="N",
        help=(
            "Number of runs per hour above which a job is flagged as "
            "high-frequency (default: 12)."
        ),
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        default=False,
        help="Exit with code 1 only when warnings or errors are present.",
    )
    parser.set_defaults(func=_run_retention)


def _run_retention(args: argparse.Namespace) -> int:
    """Execute the retention analysis and print the report."""
    try:
        jobs = load_from_file(args.crontab)
    except FileNotFoundError:
        print(f"cronaudit retention: file not found: {args.crontab}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"cronaudit retention: error loading file: {exc}", file=sys.stderr)
        return 2

    report = analyze_retention(jobs, high_freq_threshold=args.threshold)
    print_retention_report(report)

    if args.warn_only and report.has_warnings():
        return 1
    return 0
