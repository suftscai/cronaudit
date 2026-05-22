"""Command-line interface for cronaudit."""

import argparse
import sys

from cronaudit.loader import load_from_file
from cronaudit.conflict import detect_conflicts
from cronaudit.report import print_report
from cronaudit.visualizer import print_timeline
from cronaudit.exporter import write_export


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronaudit",
        description="Parse and audit cron schedules for conflicts.",
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
        metavar="FILE",
        default=None,
        help="Export results to FILE (.json or .csv).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable colored output.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        jobs = load_from_file(args.crontab)
    except FileNotFoundError:
        print(f"Error: file not found: {args.crontab}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error parsing crontab: {exc}", file=sys.stderr)
        return 1

    conflicts = detect_conflicts(jobs)
    print_report(jobs, conflicts)

    if args.timeline:
        print_timeline(jobs)

    if args.export:
        try:
            write_export(args.export, jobs, conflicts)
            print(f"Results exported to {args.export}")
        except ValueError as exc:
            print(f"Export error: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
