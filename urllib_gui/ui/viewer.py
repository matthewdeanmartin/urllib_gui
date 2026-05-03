"""Hypertext viewer widget built on top of Tkinter Text."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from collections.abc import Callable
from contextlib import suppress
from tkinter import ttk
from typing import TYPE_CHECKING

from urllib_gui.model import LinkSpan, RenderedDocument

LinkOpener = Callable[[str, bool], None]
StatusUpdater = Callable[[str | None], None]
if TYPE_CHECKING:
    type EventHandler = Callable[[tk.Event[tk.Misc]], None]
else:
    type EventHandler = Callable[[tk.Event], None]

_MIN_FONT_SIZE = 6
_MAX_FONT_SIZE = 48
_DEFAULT_FONT_SIZE = 12


class HypertextViewer(ttk.Frame):  # pylint: disable=too-many-ancestors
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
        self.link_targets: dict[str, str] = {}
        self.visited_hrefs: set[str] = set()
        self._font_size = _DEFAULT_FONT_SIZE
        self._font_family = "TkDefaultFont"
        self._link_foreground = "#005cc5"
        self._visited_foreground = "#800080"
        self.text = tk.Text(self, wrap="word", undo=False, font=(self._font_family, self._font_size))
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.text.tag_configure("link", foreground="#005cc5", underline=True)
        self.text.tag_configure("visited_link", foreground="#800080", underline=True)
        self.text.tag_configure("body", spacing1=2, spacing3=2)
        self.text.tag_configure("find_highlight", background="#ffff00", foreground="#000000")
        self.text.configure(state="disabled")
        # Find bar (hidden until Ctrl+F)
        self._find_bar: ttk.Frame | None = None
        self._find_var = tk.StringVar()
        self._find_match_count = 0
        self._find_current = 0

    def apply_theme(
        self,
        *,
        background: str,
        foreground: str,
        link_foreground: str,
        visited_foreground: str = "#800080",
        font_family: str | None = None,
        font_size: int | None = None,
    ) -> None:
        """Apply colors and font to the text widget."""
        self._link_foreground = link_foreground
        self._visited_foreground = visited_foreground
        if font_family is not None:
            self._font_family = font_family
        if font_size is not None:
            self._font_size = font_size
        self.text.configure(
            background=background,
            foreground=foreground,
            insertbackground=foreground,
            font=(self._font_family, self._font_size),
        )
        self.text.tag_configure("link", foreground=link_foreground, underline=True)
        self.text.tag_configure("visited_link", foreground=visited_foreground, underline=True)

    def zoom_in(self) -> None:
        """Increase font size by one point."""
        self._font_size = min(self._font_size + 1, _MAX_FONT_SIZE)
        self.text.configure(font=(self._font_family, self._font_size))

    def zoom_out(self) -> None:
        """Decrease font size by one point."""
        self._font_size = max(self._font_size - 1, _MIN_FONT_SIZE)
        self.text.configure(font=(self._font_family, self._font_size))

    def zoom_reset(self) -> None:
        """Reset font size to the default."""
        self._font_size = _DEFAULT_FONT_SIZE
        self.text.configure(font=(self._font_family, self._font_size))

    @property
    def current_font_size(self) -> int:
        return self._font_size

    def set_plain_text(self, text: str) -> None:
        """Display plain text without link tagging."""
        self.replace_text(text)

    def set_document(self, document: RenderedDocument) -> None:
        """Display a rendered document and tag links."""
        self.replace_text(document.text)
        for index, link in enumerate(document.links):
            self.add_link_tag(index, link)

    def replace_text(self, text: str) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", text or "(empty document)", ("body",))
        self.text.configure(state="disabled")
        self.link_targets = {}
        self._clear_find_highlights()

    def add_link_tag(self, index: int, link: LinkSpan) -> None:
        tag_name = f"link_{index}"
        start = f"1.0 + {link.start_offset} chars"
        end = f"1.0 + {link.end_offset} chars"
        self.link_targets[tag_name] = link.href
        is_visited = link.href in self.visited_hrefs
        base_tag = "visited_link" if is_visited else "link"
        self.text.tag_add(base_tag, start, end)
        self.text.tag_add(tag_name, start, end)
        self.text.tag_bind(tag_name, "<Enter>", self.hover_handler(link.href))
        self.text.tag_bind(tag_name, "<Leave>", self.hover_handler(None))
        self.text.tag_bind(tag_name, "<Button-1>", self.open_handler(link.href, False))
        self.text.tag_bind(tag_name, "<Control-Button-1>", self.open_handler(link.href, True))
        self.text.tag_bind(tag_name, "<Button-2>", self.open_handler(link.href, True))
        self.text.tag_bind(tag_name, "<Button-3>", self.context_handler(link.href))

    def mark_visited(self, href: str) -> None:
        """Record a visited URL and restyle any matching link tags."""
        self.visited_hrefs.add(href)
        for tag_name, target in self.link_targets.items():
            if target == href:
                start = self.text.tag_ranges(tag_name)
                if start:
                    self.text.tag_remove("link", start[0], start[1])
                    self.text.tag_add("visited_link", start[0], start[1])

    def hover_handler(self, href: str | None) -> EventHandler:
        def callback(_event: tk.Event[tk.Misc]) -> None:
            self.on_hover(href)

        return callback

    def open_handler(self, href: str, new_tab: bool) -> EventHandler:
        def callback(_event: tk.Event[tk.Misc]) -> None:
            self.open_link(href, new_tab)

        return callback

    def context_handler(self, href: str) -> EventHandler:
        def callback(event: tk.Event[tk.Misc]) -> None:
            self.show_context_menu(event, href)

        return callback

    def on_hover(self, href: str | None) -> None:
        self.text.configure(cursor="hand2" if href else "xterm")
        if self.status_callback is not None:
            self.status_callback(href)

    def open_link(self, href: str, new_tab: bool) -> None:
        if self.open_link_callback is not None:
            self.open_link_callback(href, new_tab)

    def show_context_menu(self, event: tk.Event[tk.Misc], href: str) -> None:
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Open Link", command=lambda: self.open_link(href, False))
        menu.add_command(label="Open Link in New Tab", command=lambda: self.open_link(href, True))
        menu.add_command(label="Copy Link URL", command=lambda: self.copy_text(href))
        menu.add_command(label="Open Link in External Browser", command=lambda: webbrowser.open(href))
        menu.tk_popup(event.x_root, event.y_root)

    def copy_text(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)

    # ------------------------------------------------------------------ find

    def show_find_bar(self) -> None:
        """Show the find-in-page bar."""
        if self._find_bar is None:
            self._find_bar = ttk.Frame(self)
            self._find_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
            ttk.Label(self._find_bar, text="Find:").pack(side="left", padx=(4, 2))
            entry = ttk.Entry(self._find_bar, textvariable=self._find_var, width=30)
            entry.pack(side="left")
            entry.bind("<Return>", lambda _e: self.find_next())
            entry.bind("<Shift-Return>", lambda _e: self.find_prev())
            entry.bind("<KeyRelease>", lambda _e: self._run_find())
            ttk.Button(self._find_bar, text="▲", width=2, command=self.find_prev).pack(side="left", padx=(4, 0))
            ttk.Button(self._find_bar, text="▼", width=2, command=self.find_next).pack(side="left", padx=(2, 0))
            self._find_count_label = ttk.Label(self._find_bar, text="")
            self._find_count_label.pack(side="left", padx=(6, 0))
            ttk.Button(self._find_bar, text="✕", width=2, command=self.hide_find_bar).pack(side="right", padx=(0, 4))
            entry.focus_set()
        else:
            self._find_bar.grid()
            for child in self._find_bar.winfo_children():
                if isinstance(child, ttk.Entry):
                    child.focus_set()
                    break

    def hide_find_bar(self) -> None:
        """Hide the find bar and clear highlights."""
        if self._find_bar is not None:
            self._find_bar.grid_remove()
        self._clear_find_highlights()
        self._find_var.set("")

    def _clear_find_highlights(self) -> None:
        with suppress(tk.TclError):
            self.text.tag_remove("find_highlight", "1.0", "end")
        self._find_match_count = 0
        self._find_current = 0

    def _run_find(self) -> None:
        self._clear_find_highlights()
        query = self._find_var.get()
        if not query:
            if hasattr(self, "_find_count_label"):
                self._find_count_label.configure(text="")
            return
        count = 0
        start = "1.0"
        while True:
            pos = self.text.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos} + {len(query)} chars"
            self.text.tag_add("find_highlight", pos, end)
            count += 1
            start = end
        self._find_match_count = count
        self._find_current = 1 if count else 0
        label = f"{self._find_current}/{count}" if count else "not found"
        if hasattr(self, "_find_count_label"):
            self._find_count_label.configure(text=label)
        if count:
            self._scroll_to_find_match(self._find_current)

    def _scroll_to_find_match(self, n: int) -> None:
        """Scroll to the nth (1-based) find highlight."""
        ranges = self.text.tag_ranges("find_highlight")
        idx = (n - 1) * 2
        if idx < len(ranges):
            self.text.see(str(ranges[idx]))

    def find_next(self) -> None:
        if self._find_match_count == 0:
            return
        self._find_current = (self._find_current % self._find_match_count) + 1
        if hasattr(self, "_find_count_label"):
            self._find_count_label.configure(text=f"{self._find_current}/{self._find_match_count}")
        self._scroll_to_find_match(self._find_current)

    def find_prev(self) -> None:
        if self._find_match_count == 0:
            return
        self._find_current = ((self._find_current - 2) % self._find_match_count) + 1
        if hasattr(self, "_find_count_label"):
            self._find_count_label.configure(text=f"{self._find_current}/{self._find_match_count}")
        self._scroll_to_find_match(self._find_current)
