"""Smoke tests for the CLI entry point."""

from typing import Protocol

import urllib_gui
from urllib_gui import cli
from urllib_gui.__about__ import __version__
from urllib_gui.ui.viewer import HypertextViewer


class MonkeyPatchLike(Protocol):
    """Minimal protocol for the pytest monkeypatch fixture used here."""

    def setattr(self, target: object, name: str, value: object) -> None:
        """Set an attribute during the test."""


def test_import() -> None:
    """Package can be imported."""
    assert urllib_gui.__name__ == "urllib_gui"


def test_viewer_module_imports() -> None:
    """The viewer module should import without evaluating unsupported tkinter generics."""
    assert HypertextViewer.__name__ == "HypertextViewer"


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
    cli.main(["https://example.com", "--theme", "dark"])

    assert captured == {"initial_url": "https://example.com", "theme": "dark"}
