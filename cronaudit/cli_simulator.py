"""CLI subcommand for running the cron job simulator."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from cronaudit.loader import load_from_file
from cronaudit.simulator import format_simulation_report, simulate

_DT_FORMAT = "%Y-%m-%dT%H:%M"


def add_simulator_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "simulate",
        help="Simulate job execution over a time window",
    )
    parser.add_argument("crontab", help="Path to crontab file")
    parser.add_argument(
        "--start",
        default=None,
        help=f"Window start datetime ({_DT_FORMAT}), default: now",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Number of hours to simulate (default: 24)",
    )
    parser.set_defaults(func=_run_simulator)


def _run_simulator(args: argparse.Namespace) -> int:
    jobs = load_from_file(args.crontab)
    if args.start:
        start = datetime.strptime(args.start, _DT_FORMAT)
    else:
        now = datetime.now()
        start = now.replace(second=0, microsecond=0)
    end = start + timedelta(hours=args.hours)
    result = simulate(jobs, start, end)
    print(format_simulation_report(result))
    return 0
