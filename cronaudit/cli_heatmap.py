"""CLI subcommand: heatmap — show a day-of-week × hour activity heatmap."""

from __future__ import annotations

import argparse
import sys
from typing import List

from cronaudit.loader import load_from_file, CronJob
from cronaudit.heatmap import print_heatmap


def add_heatmap_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'heatmap' subcommand on an existing subparsers object."""
    parser = subparsers.add_parser(
        "heatmap",
        help="Display a day-of-week × hour heatmap of job activity.",
    )
    parser.add_argument(
        "crontab",
        metavar="FILE",
        help="Path to the crontab file to visualise.",
    )
    parser.set_defaults(func=_run_heatmap)


def _run_heatmap(args: argparse.Namespace) -> int:
    """Entry point for the heatmap subcommand."""
    try:
        jobs: List[CronJob] = load_from_file(args.crontab)
    except FileNotFoundError:
        print(f"cronaudit: error: file not found: {args.crontab}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"cronaudit: error: {exc}", file=sys.stderr)
        return 1

    if not jobs:
        print("No jobs found in crontab.")
        return 0

    print(f"Heatmap for {len(jobs)} job(s) — shading: ' ' none  '░' low  '▒' mid  '▓▌█' high\n")
    print_heatmap(jobs)
    return 0
