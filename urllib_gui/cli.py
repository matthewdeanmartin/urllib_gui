"""Command-line entry point for urllib_gui."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from urllib_gui.__about__ import __version__


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


def main(argv: Sequence[str] | None = None) -> None:
    """Run the urllib_gui CLI."""
    from urllib_gui.app import run

    parser = build_parser()
    args = parser.parse_args(argv)
    run(initial_url=args.url, theme=args.theme)


if __name__ == "__main__":
    main()
