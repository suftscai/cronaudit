"""Command-line interface for cronaudit."""

import argparse
import sys
from cronaudit.loader import load_from_file
from cronaudit.conflict import detect_conflicts
from cronaudit.report import print_report
from cronaudit.visualizer import print_timeline
from cronaudit.exporter import write_export
from cronaudit.differ import diff_crontabs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronaudit",
        description="Parse and audit cron schedules for conflicts.",
    )
    parser.add_argument("file", help="Path to crontab file")
    parser.add_argument(
        "--timeline", action="store_true", help="Render an ASCII timeline"
    )
    parser.add_argument(
        "--export", choices=["json", "csv"], help="Export results in given format"
    )
    parser.add_argument(
        "--output", default="cronaudit_export", help="Output filename base (no extension)"
    )
    parser.add_argument(
        "--diff", metavar="OTHER_FILE", help="Diff this crontab against another file"
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        jobs = load_from_file(args.file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.diff:
        try:
            other_jobs = load_from_file(args.diff)
        except (FileNotFoundError, ValueError) as exc:
            print(f"Error loading diff target: {exc}", file=sys.stderr)
            return 1
        from cronaudit.differ import diff_crontabs
        result = diff_crontabs(jobs, other_jobs)
        print(str(result))
        return 0

    conflicts = detect_conflicts(jobs)
    print_report(jobs, conflicts)

    if args.timeline:
        print_timeline(jobs)

    if args.export:
        path = write_export(jobs, conflicts, fmt=args.export, base_name=args.output)
        print(f"Exported to {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
