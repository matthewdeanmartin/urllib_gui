"""Smoke tests for the CLI entry point."""

from typing import Protocol


class MonkeyPatchLike(Protocol):
    """Minimal protocol for the pytest monkeypatch fixture used here."""

    def setattr(self, target: object, name: str, value: object) -> None:
        """Set an attribute during the test."""


def test_import() -> None:
    """Package can be imported."""
    import urllib_gui  # noqa: F401


def test_version() -> None:
    """Package exposes a version string."""
    from urllib_gui.__about__ import __version__

    assert isinstance(__version__, str)
    assert __version__


def test_main_launches_app(monkeypatch: MonkeyPatchLike) -> None:
    """CLI should hand parsed options to the GUI runner."""
    from urllib_gui import cli

    captured: dict[str, str | None] = {}

    def fake_run(*, initial_url: str | None = None, theme: str = "light") -> None:
        captured["initial_url"] = initial_url
        captured["theme"] = theme

    monkeypatch.setattr(cli, "run", fake_run)
    cli.main(["https://example.com", "--theme", "dark"])

    assert captured == {"initial_url": "https://example.com", "theme": "dark"}
