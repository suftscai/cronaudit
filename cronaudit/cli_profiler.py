"""CLI subcommand for profiling cron job schedule density and contention."""

import argparse
from cronaudit.loader import load_from_file
from cronaudit.profiler import profile_jobs, format_profile_report


def add_profiler_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'profile' subcommand onto an existing subparsers object."""
    parser = subparsers.add_parser(
        "profile",
        help="Profile job schedule density and resource contention.",
    )
    parser.add_argument(
        "crontab",
        metavar="CRONTAB",
        help="Path to the crontab file to profile.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        metavar="N",
        help="Show only the top N jobs by contention score.",
    )
    parser.add_argument(
        "--min-contention",
        type=float,
        default=0.0,
        metavar="SCORE",
        help="Only show jobs with contention score >= SCORE (0.0–1.0).",
    )
    parser.set_defaults(func=_run_profiler)


def _run_profiler(args: argparse.Namespace) -> int:
    """Execute the profile subcommand."""
    try:
        jobs = load_from_file(args.crontab)
    except (OSError, ValueError) as exc:
        print(f"Error loading crontab: {exc}")
        return 1

    results = profile_jobs(jobs)

    if args.min_contention > 0.0:
        results = [r for r in results if r.contention_score >= args.min_contention]

    if args.top is not None:
        results = results[: args.top]

    print(format_profile_report(results))
    return 0
