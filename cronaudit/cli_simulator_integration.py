"""Integration registration for the simulator subcommand."""

from cronaudit.cli_simulator import add_simulator_subcommand


def register(subparsers) -> None:
    """Register the simulate subcommand with the given subparsers action."""
    add_simulator_subcommand(subparsers)
