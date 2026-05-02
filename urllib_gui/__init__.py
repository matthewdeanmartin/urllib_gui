"""A gui for urllib. Something between curl and postman and a browser. Almost all stdlib."""

from urllib_gui.__about__ import __version__
from urllib_gui.app import open_url, run

__all__ = ["__version__", "open_url", "run"]
