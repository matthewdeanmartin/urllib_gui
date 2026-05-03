"""Rich history viewer dialog with search, delete, copy, and open actions."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from urllib_gui.model import HistoryEntry
from urllib_gui.storage.history import HistoryStore


class HistoryDialog(tk.Toplevel):
    """Searchable history list with per-entry delete and open actions."""

    def __init__(
        self,
        parent: tk.Misc,
        store: HistoryStore,
        *,
        on_open: Callable[[str, bool], None],
        on_cleared: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("History")
        self.geometry("820x480")
        self.resizable(True, True)
        self._store = store
        self._on_open = on_open
        self._on_cleared = on_cleared
        self._build()
        self._populate()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Search:").pack(side="left")
        self._search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._search_var, width=32).pack(side="left", padx=(4, 0))
        self._search_var.trace_add("write", lambda *_: self._populate())

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Clear All…", command=self._clear_all).pack(side="left", padx=2)

        cols = ("visited", "method", "status", "title", "url", "content_type")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("visited", text="Visited", command=lambda: self._sort("visited"))
        self._tree.heading("method", text="Method")
        self._tree.heading("status", text="Status")
        self._tree.heading("title", text="Title")
        self._tree.heading("url", text="URL", command=lambda: self._sort("url"))
        self._tree.heading("content_type", text="Content-Type")
        self._tree.column("visited", width=135, minwidth=100)
        self._tree.column("method", width=55, minwidth=45)
        self._tree.column("status", width=50, minwidth=40)
        self._tree.column("title", width=160, minwidth=80)
        self._tree.column("url", width=260, minwidth=120)
        self._tree.column("content_type", width=120, minwidth=80)

        sb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        sb.pack(side="left", fill="y", pady=(0, 8), padx=(0, 8))
        self._tree.bind("<Double-Button-1>", lambda _e: self._open_selected(new_tab=False))

        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Open", command=lambda: self._open_selected(new_tab=False)).pack(side="left")
        ttk.Button(bottom, text="Open in New Tab", command=lambda: self._open_selected(new_tab=True)).pack(
            side="left", padx=(4, 0)
        )
        ttk.Button(bottom, text="Copy URL", command=self._copy_url).pack(side="left", padx=(4, 0))
        ttk.Button(bottom, text="Delete Entry", command=self._delete_selected).pack(side="left", padx=(4, 0))
        self._count_var = tk.StringVar()
        ttk.Label(bottom, textvariable=self._count_var).pack(side="left", padx=(12, 0))
        ttk.Button(bottom, text="Close", command=self.destroy).pack(side="right")

        self._sort_col = "visited"
        self._sort_reverse = True
        self._entries: list[HistoryEntry] = []

    def _populate(self) -> None:
        self._tree.delete(*self._tree.get_children())
        query = self._search_var.get()
        self._entries = self._store.list_entries(search=query, limit=500)

        if self._sort_col == "url":
            self._entries.sort(key=lambda e: e.url.lower(), reverse=self._sort_reverse)
        else:
            self._entries.sort(key=lambda e: e.visited_at.isoformat(), reverse=self._sort_reverse)

        for i, entry in enumerate(self._entries):
            visited = entry.visited_at.strftime("%Y-%m-%d %H:%M:%S")
            self._tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    visited,
                    entry.method,
                    entry.status or "",
                    entry.title or "",
                    entry.url,
                    entry.content_type or "",
                ),
            )
        n = len(self._entries)
        self._count_var.set(f"{n} {'entry' if n == 1 else 'entries'}")

    def _sort(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = col == "visited"
        self._populate()

    def _selected_index(self) -> int | None:
        sel = self._tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def _open_selected(self, new_tab: bool) -> None:
        idx = self._selected_index()
        if idx is not None:
            self._on_open(self._entries[idx].url, new_tab)
            self.destroy()

    def _copy_url(self) -> None:
        idx = self._selected_index()
        if idx is not None:
            self.clipboard_clear()
            self.clipboard_append(self._entries[idx].url)

    def _delete_selected(self) -> None:
        idx = self._selected_index()
        if idx is None:
            return
        entry = self._entries[idx]
        self._store.delete_entry(entry.url, entry.visited_at)
        self._populate()

    def _clear_all(self) -> None:
        if not messagebox.askyesno("Clear History", "Delete all history entries?", parent=self):
            return
        self._store.clear()
        if self._on_cleared:
            self._on_cleared()
        self._populate()
