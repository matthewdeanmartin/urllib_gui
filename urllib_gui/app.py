"""Application entrypoints."""

from __future__ import annotations

import tkinter as tk

from urllib_gui.main_window import MainWindow


def run(*, initial_url: str | None = None, theme: str = "light") -> None:
    """Launch the Tkinter application."""
    try:
        window = MainWindow(initial_url=initial_url, theme=theme)
    except tk.TclError as error:
        raise RuntimeError("Unable to start the Tkinter UI in this environment.") from error
    window.mainloop()


def open_url(url: str) -> None:
    """Launch the app and open *url* in the first tab."""
    run(initial_url=url)
