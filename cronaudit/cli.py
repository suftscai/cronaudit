"""Command-line interface for cronaudit."""

import argparse
import sys

from cronaudit.loader import load_from_file
from cronaudit.conflict import detect_conflicts
from cronaudit.report import print_report
from cronaudit.visualizer import print_timeline
from cronaudit.exporter import write_export
from cronaudit.summarizer import print_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronaudit",
        description="Parse and visualize cron schedules to detect conflicts.",
    )
    parser.add_argument(
        "crontab",
        help="Path to the crontab file to analyse.",
    )
    parser.add_argument(
        "--timeline",
        action="store_true",
        default=False,
        help="Render an ASCII timeline of job activity.",
    )
    parser.add_argument(
        "--export",
        metavar="FORMAT",
        choices=["json", "csv"],
        default=None,
        help="Export results in the given format (json or csv).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write export output to FILE instead of stdout.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a statistical summary of the cron schedule.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        jobs = load_from_file(args.crontab)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    conflicts = detect_conflicts(jobs)
    print_report(jobs, conflicts)

    if args.timeline:
        print_timeline(jobs)

    if args.summary:
        print_summary(jobs)

    if args.export:
        write_export(jobs, conflicts, fmt=args.export, path=args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
