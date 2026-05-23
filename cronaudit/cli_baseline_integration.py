"""Integration helper: wire baseline subcommand into the main CLI.

This module is imported by cli.py to register the 'baseline' subcommand
alongside the other subcommands (agenda, heatmap, etc.).
"""
from __future__ import annotations

from cronaudit.cli_baseline import add_baseline_subcommand

__all__ = ["add_baseline_subcommand"]


def register(subparsers) -> None:  # type: ignore[type-arg]
    """Register the baseline subcommand with *subparsers*.

    Follows the same convention used by cli_agenda and cli_heatmap so that
    cli.py can discover and register all subcommands with a uniform call::

        from cronaudit.cli_baseline_integration import register as register_baseline
        register_baseline(subparsers)
    """
    add_baseline_subcommand(subparsers)
