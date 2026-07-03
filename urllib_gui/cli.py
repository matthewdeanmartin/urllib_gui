"""Command-line entry point for urllib_gui."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from urllib_gui.__about__ import __version__
from urllib_gui.app import run
from urllib_gui.upgrade_integration import add_commands, run_command, should_handle_upgrade_command


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        prog="urllib_gui",
        description="A gui for urllib. Something between curl and postman and a browser. Almost all stdlib",
    )
    parser.add_argument("url", nargs="?", help="Optional URL to open immediately")
    parser.add_argument("--theme", choices=("light", "dark"), default="light", help="Initial app theme")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def build_update_parser() -> argparse.ArgumentParser:
    """Build the parser for integrated update subcommands."""
    parser = argparse.ArgumentParser(
        prog="urllib_gui",
        description="A gui for urllib. Something between curl and postman and a browser. Almost all stdlib",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_commands(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the urllib_gui CLI."""
    actual_argv = list(argv) if argv is not None else sys.argv[1:]
    if should_handle_upgrade_command(actual_argv):
        parser = build_update_parser()
        args = parser.parse_args(actual_argv)
        return run_command(args)
    parser = build_parser()
    args = parser.parse_args(actual_argv)
    run(initial_url=args.url, theme=args.theme)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
