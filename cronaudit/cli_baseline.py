"""CLI subcommand: baseline – snapshot and compare cron schedules."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronaudit.loader import load_from_file
from cronaudit.baseline import (
    snapshot_from_jobs,
    save_baseline,
    load_baseline,
    compare_to_baseline,
)


def add_baseline_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'baseline' subcommand."""
    parser = subparsers.add_parser(
        "baseline",
        help="Save or compare a crontab baseline snapshot.",
    )
    parser.add_argument("crontab", help="Path to the crontab file.")
    parser.add_argument(
        "--save",
        metavar="FILE",
        help="Save current jobs as a baseline snapshot to FILE.",
    )
    parser.add_argument(
        "--compare",
        metavar="FILE",
        help="Compare current jobs against a saved baseline FILE.",
    )
    parser.add_argument(
        "--label",
        default="snapshot",
        help="Label for the snapshot (default: 'snapshot').",
    )
    parser.set_defaults(func=_run_baseline)


def _run_baseline(args: argparse.Namespace) -> int:
    """Execute the baseline subcommand."""
    try:
        jobs = load_from_file(args.crontab)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading crontab: {exc}", file=sys.stderr)
        return 1

    if args.save:
        snap = snapshot_from_jobs(args.label, jobs)
        save_baseline(snap, args.save)
        print(f"Baseline saved to '{args.save}' with label '{args.label}' ({len(jobs)} jobs).")
        return 0

    if args.compare:
        try:
            snap = load_baseline(args.compare)
        except (FileNotFoundError, json.JSONDecodeError) as exc:  # type: ignore[name-defined]
            print(f"Error loading baseline: {exc}", file=sys.stderr)
            return 1
        diff = compare_to_baseline(jobs, snap)
        if diff.has_changes:
            print(f"Changes detected vs baseline '{snap.label}':\n{diff}")
        else:
            print(f"No changes detected vs baseline '{snap.label}'.")
        return 0

    print("Specify --save FILE or --compare FILE.", file=sys.stderr)
    return 1
