"""Hypertext viewer widget built on top of Tkinter Text."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from collections.abc import Callable
from tkinter import ttk

from urllib_gui.model import LinkSpan, RenderedDocument

LinkOpener = Callable[[str, bool], None]
StatusUpdater = Callable[[str | None], None]
EventHandler = Callable[[tk.Event[tk.Misc]], None]


class HypertextViewer(ttk.Frame):
    """Text viewer that can tag and open hyperlinks."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        open_link_callback: LinkOpener | None = None,
        status_callback: StatusUpdater | None = None,
    ) -> None:
        super().__init__(master)
        self.open_link_callback = open_link_callback
        self.status_callback = status_callback
        self._link_targets: dict[str, str] = {}
        self.text = tk.Text(self, wrap="word", undo=False)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.text.tag_configure("link", foreground="#005cc5", underline=True)
        self.text.tag_configure("body", spacing1=2, spacing3=2)
        self.text.configure(state="disabled")

    def apply_theme(self, *, background: str, foreground: str, link_foreground: str) -> None:
        """Apply colors to the text widget."""
        self.text.configure(background=background, foreground=foreground, insertbackground=foreground)
        self.text.tag_configure("link", foreground=link_foreground, underline=True)

    def set_plain_text(self, text: str) -> None:
        """Display plain text without link tagging."""
        self._replace_text(text)

    def set_document(self, document: RenderedDocument) -> None:
        """Display a rendered document and tag links."""
        self._replace_text(document.text)
        for index, link in enumerate(document.links):
            self._add_link_tag(index, link)

    def _replace_text(self, text: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text or "(empty document)", ("body",))
        self.text.configure(state="disabled")
        self._link_targets = {}

    def _add_link_tag(self, index: int, link: LinkSpan) -> None:
        tag_name = f"link_{index}"
        start = f"1.0 + {link.start_offset} chars"
        end = f"1.0 + {link.end_offset} chars"
        self._link_targets[tag_name] = link.href
        self.text.tag_add("link", start, end)
        self.text.tag_add(tag_name, start, end)
        self.text.tag_bind(tag_name, "<Enter>", self._hover_handler(link.href))
        self.text.tag_bind(tag_name, "<Leave>", self._hover_handler(None))
        self.text.tag_bind(tag_name, "<Button-1>", self._open_handler(link.href, False))
        self.text.tag_bind(tag_name, "<Control-Button-1>", self._open_handler(link.href, True))
        self.text.tag_bind(tag_name, "<Button-2>", self._open_handler(link.href, True))
        self.text.tag_bind(tag_name, "<Button-3>", self._context_handler(link.href))

    def _hover_handler(self, href: str | None) -> EventHandler:
        def callback(_event: tk.Event[tk.Misc]) -> None:
            self._on_hover(href)

        return callback

    def _open_handler(self, href: str, new_tab: bool) -> EventHandler:
        def callback(_event: tk.Event[tk.Misc]) -> None:
            self._open_link(href, new_tab)

        return callback

    def _context_handler(self, href: str) -> EventHandler:
        def callback(event: tk.Event[tk.Misc]) -> None:
            self._show_context_menu(event, href)

        return callback

    def _on_hover(self, href: str | None) -> None:
        self.text.configure(cursor="hand2" if href else "xterm")
        if self.status_callback is not None:
            self.status_callback(href)

    def _open_link(self, href: str, new_tab: bool) -> None:
        if self.open_link_callback is not None:
            self.open_link_callback(href, new_tab)

    def _show_context_menu(self, event: tk.Event[tk.Misc], href: str) -> None:
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Open Link", command=lambda: self._open_link(href, False))
        menu.add_command(label="Open Link in New Tab", command=lambda: self._open_link(href, True))
        menu.add_command(label="Copy Link URL", command=lambda: self._copy_text(href))
        menu.add_command(label="Open Link in External Browser", command=lambda: webbrowser.open(href))
        menu.tk_popup(event.x_root, event.y_root)

    def _copy_text(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)
