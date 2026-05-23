"""CLI subcommand: notify — evaluate notification rules against a crontab."""

import argparse
from cronaudit.loader import load_from_file
from cronaudit.notifier import NotificationRule, evaluate_rules, format_notification_report


def add_notifier_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "notify",
        help="Evaluate notification rules against a crontab file.",
    )
    p.add_argument("crontab", help="Path to crontab file")
    p.add_argument(
        "--command-contains",
        metavar="TEXT",
        help="Alert when a job command contains TEXT",
    )
    p.add_argument(
        "--frequency",
        metavar="FREQ",
        help="Alert when a job matches this frequency class (e.g. every_minute)",
    )
    p.add_argument(
        "--rule-name",
        default="user-rule",
        help="Label for the notification rule (default: user-rule)",
    )
    p.set_defaults(func=_run_notifier)


def _run_notifier(args: argparse.Namespace) -> int:
    jobs = load_from_file(args.crontab)

    if not args.command_contains and not args.frequency:
        print("Error: at least one of --command-contains or --frequency is required.")
        return 1

    rule = NotificationRule(
        name=args.rule_name,
        frequency=getattr(args, "frequency", None),
        command_contains=getattr(args, "command_contains", None),
    )

    notifications = evaluate_rules(jobs, [rule])
    print(format_notification_report(notifications))
    return 0
