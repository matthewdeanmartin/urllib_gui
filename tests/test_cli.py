"""Smoke tests for the CLI entry point."""

import argparse
import importlib
from typing import Protocol

import pytest

import urllib_gui
from urllib_gui import app, cli, upgrade_integration
from urllib_gui.__about__ import __version__

tkinter = pytest.importorskip("tkinter", reason="tkinter not available")


class MonkeyPatchLike(Protocol):
    """Minimal protocol for the pytest monkeypatch fixture used here."""

    def setattr(self, target: object, name: str, value: object) -> None:
        """Set an attribute during the test."""


class SubparsersLike(Protocol):
    """Minimal protocol for the subparser collection used in tests."""

    def add_parser(self, name: str) -> argparse.ArgumentParser:
        """Add and return a named subparser."""


def test_import() -> None:
    """Package can be imported."""
    assert urllib_gui.__name__ == "urllib_gui"


def test_viewer_module_imports() -> None:
    """The viewer module should import without evaluating unsupported tkinter generics."""
    viewer_module = importlib.import_module("urllib_gui.ui.viewer")
    assert viewer_module.HypertextViewer.__name__ == "HypertextViewer"


def test_version() -> None:
    """Package exposes a version string."""
    assert isinstance(__version__, str)
    assert __version__


def test_main_launches_app(monkeypatch: MonkeyPatchLike) -> None:
    """CLI should hand parsed options to the GUI runner."""
    captured: dict[str, str | None] = {}

    def fake_run(*, initial_url: str | None = None, theme: str = "light") -> None:
        captured["initial_url"] = initial_url
        captured["theme"] = theme

    monkeypatch.setattr(cli, "run", fake_run)
    rc = cli.main(["https://example.com", "--theme", "dark"])

    assert rc == 0
    assert captured == {"initial_url": "https://example.com", "theme": "dark"}


def test_main_dispatches_upgrade_subcommand(monkeypatch: MonkeyPatchLike) -> None:
    """CLI should route update subcommands through the integrated dispatcher."""
    captured: dict[str, str] = {}

    def fake_add_commands(subparsers: SubparsersLike) -> None:
        command_subparsers = subparsers.add_parser("upgrade")
        command_subparsers.add_argument("--check", action="store_true")

    def fake_run_command(args: object) -> int:
        command = getattr(args, "command", "")
        captured["command"] = str(command)
        return 10

    monkeypatch.setattr(cli, "should_handle_upgrade_command", lambda argv: True)
    monkeypatch.setattr(cli, "add_commands", fake_add_commands)
    monkeypatch.setattr(cli, "run_command", fake_run_command)

    rc = cli.main(["upgrade", "--check"])

    assert rc == 10
    assert captured == {"command": "upgrade"}


def test_missing_upgrade_extra_quietly_skips(monkeypatch: MonkeyPatchLike) -> None:
    """Without the optional extra, update support should quietly disable itself."""
    monkeypatch.setattr(upgrade_integration, "HAS_UPGRADE_SUPPORT", False)

    parser = cli.build_update_parser()

    assert upgrade_integration.should_handle_upgrade_command(["upgrade"]) is False
    assert parser.parse_args([]).command is None
    assert upgrade_integration.startup_report() is None
    assert upgrade_integration.exit_report() is None
    assert upgrade_integration.run_command(parser.parse_args([])) == 0


def test_app_run_prints_distinct_startup_and_exit_notices(
    monkeypatch: MonkeyPatchLike, capsys: pytest.CaptureFixture[str]
) -> None:
    """The GUI lifecycle should surface update notices at startup and shutdown."""
    startup_marker = object()
    exit_marker = object()

    class FakeWindow:
        """Minimal stand-in for the Tkinter main window."""

        def __init__(self, *, initial_url: str | None = None, theme: str = "light") -> None:
            del initial_url, theme

        def mainloop(self) -> None:
            """Pretend the GUI ran and then closed."""

    def fake_render_notice(report: object | None) -> str:
        if report is startup_marker:
            return "startup notice"
        if report is exit_marker:
            return "exit notice"
        return ""

    monkeypatch.setattr(app, "MainWindow", FakeWindow)
    monkeypatch.setattr(app, "startup_report", lambda: startup_marker)
    monkeypatch.setattr(app, "exit_report", lambda: exit_marker)
    monkeypatch.setattr(app, "render_notice", fake_render_notice)

    app.run()

    assert capsys.readouterr().err == "startup notice\nexit notice\n"
