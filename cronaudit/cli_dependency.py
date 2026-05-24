"""CLI subcommand for detecting job dependencies."""

from __future__ import annotations

import argparse
from typing import List

from cronaudit.loader import load_from_file, CronJob
from cronaudit.dependency import find_dependencies, format_dependency_report


def add_dependency_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'dependency' subcommand on an existing subparser group."""
    parser = subparsers.add_parser(
        "dependency",
        help="Detect suspected dependencies between cron jobs based on shared command tokens.",
    )
    parser.add_argument(
        "crontab",
        metavar="CRONTAB",
        help="Path to the crontab file to analyse.",
    )
    parser.add_argument(
        "--min-shared",
        type=int,
        default=1,
        metavar="N",
        help="Minimum number of shared tokens to report a dependency (default: 1).",
    )
    parser.set_defaults(func=_run_dependency)


def _run_dependency(args: argparse.Namespace) -> int:
    """Execute the dependency subcommand."""
    try:
        jobs: List[CronJob] = load_from_file(args.crontab)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    dependencies = find_dependencies(jobs)

    if args.min_shared > 1:
        dependencies = [
            d for d in dependencies if len(d.shared_tokens) >= args.min_shared
        ]

    print(format_dependency_report(dependencies))
    return 0
