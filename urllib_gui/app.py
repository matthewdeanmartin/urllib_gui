"""Application entrypoints."""

from __future__ import annotations

import sys
import tkinter as tk

from urllib_gui.main_window import MainWindow
from urllib_gui.upgrade_integration import exit_report, render_notice, startup_report


def run(*, initial_url: str | None = None, theme: str = "light") -> None:
    """Launch the Tkinter application."""
    initial_notice = render_notice(startup_report())
    if initial_notice:
        print(initial_notice, file=sys.stderr)
    try:
        window = MainWindow(initial_url=initial_url, theme=theme)
    except tk.TclError as error:
        raise RuntimeError("Unable to start the Tkinter UI in this environment.") from error
    try:
        window.mainloop()
    finally:
        final_notice = render_notice(exit_report())
        if final_notice and final_notice != initial_notice:
            print(final_notice, file=sys.stderr)


def open_url(url: str) -> None:
    """Launch the app and open *url* in the first tab."""
    run(initial_url=url)
