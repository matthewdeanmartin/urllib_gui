"""A gui for urllib. Something between curl and postman and a browser. Almost all stdlib."""

from importlib import import_module
from typing import Protocol, cast

from urllib_gui.__about__ import __version__

__all__ = ["__version__", "open_url", "run"]


class AppModule(Protocol):
    """Typed subset of the application entrypoint module."""

    def open_url(self, url: str) -> None:
        """Launch the app and open a URL."""

    def run(self, *, initial_url: str | None = None, theme: str = "light") -> None:
        """Launch the Tkinter application."""


def load_app_module() -> AppModule:
    """Import the app module lazily to avoid Tk initialization at package import time."""
    return cast(AppModule, import_module("urllib_gui.app"))


def open_url(url: str) -> None:
    """Launch the app and open *url* in the first tab."""
    load_app_module().open_url(url)


def run(*, initial_url: str | None = None, theme: str = "light") -> None:
    """Launch the Tkinter application."""
    load_app_module().run(initial_url=initial_url, theme=theme)
