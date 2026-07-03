"""Helpers for embedding do_i_need_to_upgrade into urllib_gui."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from do_i_need_to_upgrade import add_check_command, add_upgrade_command, run_if_upgrade_command
from do_i_need_to_upgrade.api import check_for_updates
from do_i_need_to_upgrade.report import Report
from do_i_need_to_upgrade.settings import Settings

DIST_NAME = "urllib_gui"
CHECK_UPDATES_COMMAND = "check-updates"
UPGRADE_COMMAND = "upgrade"
UPGRADE_COMMANDS = frozenset({CHECK_UPDATES_COMMAND, UPGRADE_COMMAND})


def settings() -> Settings:
    """Return urllib_gui's embedded update-check settings."""
    return Settings(dist_name=DIST_NAME, position="start", notify="return-only")


def should_handle_upgrade_command(argv: Sequence[str]) -> bool:
    """Return True when argv selects an integrated update subcommand."""
    for token in argv:
        if token == "--":  # nosec
            return False
        if token.startswith("-"):
            continue
        return token in UPGRADE_COMMANDS
    return False


def add_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register integrated do_i_need_to_upgrade subcommands."""
    active_settings = settings()
    add_upgrade_command(subparsers, DIST_NAME, command=UPGRADE_COMMAND, settings=active_settings)
    add_check_command(subparsers, DIST_NAME, command=CHECK_UPDATES_COMMAND, settings=active_settings)


def startup_report() -> Report | None:
    """Kick off the background refresh and return the current cache-backed report."""
    report = check_for_updates(settings=settings())
    return report if report.is_empty is False else None


def exit_report() -> Report | None:
    """Read the refreshed cache on exit without doing more network I/O."""
    report = check_for_updates(settings=settings().replace(allow_network=False, notify="return-only"))
    return report if report.is_empty is False else None


def render_notice(report: Report | None) -> str:
    """Render a user-facing update notice for stderr."""
    if report is None:
        return ""
    return report.render_text(stream=sys.stderr)


def run_command(args: argparse.Namespace) -> int:
    """Dispatch an already-parsed integrated update-related subcommand."""
    result = run_if_upgrade_command(args)
    return 0 if result is None else result


__all__ = [
    "CHECK_UPDATES_COMMAND",
    "DIST_NAME",
    "UPGRADE_COMMAND",
    "UPGRADE_COMMANDS",
    "add_commands",
    "exit_report",
    "render_notice",
    "run_command",
    "settings",
    "should_handle_upgrade_command",
    "startup_report",
]
