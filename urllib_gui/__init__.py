"""A gui for urllib. Something between curl and postman and a browser. Almost all stdlib."""

from urllib_gui.__about__ import __version__

__all__ = ["__version__", "open_url", "run"]


def open_url(url: str) -> None:
    """Launch the app and open *url* in the first tab."""
    from urllib_gui.app import open_url as _open_url

    _open_url(url)


def run(**kwargs: object) -> None:
    """Launch the Tkinter application."""
    from urllib_gui.app import run as _run

    _run(**kwargs)  # type: ignore[arg-type]
