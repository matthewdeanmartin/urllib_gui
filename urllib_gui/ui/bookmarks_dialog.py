"""Rich bookmark management dialog with tags, notes, import/export."""

from __future__ import annotations

import json
import tkinter as tk
from datetime import UTC, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from collections.abc import Callable

from urllib_gui.model import Bookmark
from urllib_gui.storage.bookmarks import BookmarkStore


class BookmarkEditDialog(tk.Toplevel):
    """Simple dialog for editing a single bookmark's title, tags, and notes."""

    def __init__(self, parent: tk.Misc, bookmark: Bookmark) -> None:
        super().__init__(parent)
        self.title("Edit Bookmark")
        self.resizable(False, False)
        self.result: Bookmark | None = None

        ttk.Label(self, text="Title:").grid(row=0, column=0, sticky="e", padx=8, pady=(12, 4))
        self._title_var = tk.StringVar(value=bookmark.title)
        ttk.Entry(self, textvariable=self._title_var, width=40).grid(row=0, column=1, padx=(0, 8), pady=(12, 4))

        ttk.Label(self, text="URL:").grid(row=1, column=0, sticky="e", padx=8, pady=4)
        self._url_var = tk.StringVar(value=bookmark.url)
        ttk.Entry(self, textvariable=self._url_var, width=40).grid(row=1, column=1, padx=(0, 8), pady=4)

        ttk.Label(self, text="Tags (comma-separated):").grid(row=2, column=0, sticky="e", padx=8, pady=4)
        self._tags_var = tk.StringVar(value=", ".join(bookmark.tags))
        ttk.Entry(self, textvariable=self._tags_var, width=40).grid(row=2, column=1, padx=(0, 8), pady=4)

        ttk.Label(self, text="Notes:").grid(row=3, column=0, sticky="ne", padx=8, pady=4)
        self._notes_text = tk.Text(self, width=40, height=4, wrap="word")
        self._notes_text.grid(row=3, column=1, padx=(0, 8), pady=4)
        if bookmark.notes:
            self._notes_text.insert("1.0", bookmark.notes)

        btn_row = ttk.Frame(self)
        btn_row.grid(row=4, column=0, columnspan=2, pady=(8, 12))
        ttk.Button(btn_row, text="Save", command=self._save).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="left", padx=4)

        self._original = bookmark
        self.grab_set()
        self.wait_window()

    def _save(self) -> None:
        title = self._title_var.get().strip()
        url = self._url_var.get().strip()
        if not title or not url:
            messagebox.showwarning("Edit Bookmark", "Title and URL are required.", parent=self)
            return
        tags = [t.strip() for t in self._tags_var.get().split(",") if t.strip()]
        notes_raw = self._notes_text.get("1.0", "end-1c").strip()
        self.result = Bookmark(
            title=title,
            url=url,
            created_at=self._original.created_at,
            tags=tags,
            notes=notes_raw or None,
        )
        self.destroy()


class BookmarksDialog(tk.Toplevel):
    """Full bookmark manager: view, edit, delete, import, export."""

    def __init__(
        self,
        parent: tk.Misc,
        store: BookmarkStore,
        *,
        on_open: Callable[[str, bool], None],
    ) -> None:
        super().__init__(parent)
        self.title("Bookmarks")
        self.geometry("820x480")
        self.resizable(True, True)
        self._store = store
        self._on_open = on_open
        self._build()
        self._populate()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Search:").pack(side="left")
        self._search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._search_var, width=28).pack(side="left", padx=(4, 0))
        self._search_var.trace_add("write", lambda *_: self._populate())

        tag_label = ttk.Label(top, text="Tag:")
        tag_label.pack(side="left", padx=(12, 0))
        self._tag_var = tk.StringVar()
        self._tag_combo = ttk.Combobox(top, textvariable=self._tag_var, width=14, state="readonly")
        self._tag_combo.pack(side="left", padx=(4, 0))
        self._tag_var.trace_add("write", lambda *_: self._populate())

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Import…", command=self._import).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Export…", command=self._export).pack(side="left", padx=2)

        cols = ("title", "url", "tags", "created")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("title", text="Title", command=lambda: self._sort("title"))
        self._tree.heading("url", text="URL", command=lambda: self._sort("url"))
        self._tree.heading("tags", text="Tags")
        self._tree.heading("created", text="Created", command=lambda: self._sort("created"))
        self._tree.column("title", width=200, minwidth=100)
        self._tree.column("url", width=280, minwidth=120)
        self._tree.column("tags", width=120, minwidth=60)
        self._tree.column("created", width=100, minwidth=80)
        sb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        sb.pack(side="left", fill="y", pady=(0, 8), padx=(0, 8))
        self._tree.bind("<Double-Button-1>", lambda _e: self._open_selected(new_tab=False))

        notes_frame = ttk.LabelFrame(self, text="Notes", padding=4)
        notes_frame.pack(fill="x", padx=8, pady=(0, 4))
        self._notes_label = ttk.Label(notes_frame, text="", wraplength=700, justify="left")
        self._notes_label.pack(anchor="w")
        self._tree.bind("<<TreeviewSelect>>", lambda _e: self._on_select())

        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Open", command=lambda: self._open_selected(new_tab=False)).pack(side="left")
        ttk.Button(bottom, text="Open in New Tab", command=lambda: self._open_selected(new_tab=True)).pack(
            side="left", padx=(4, 0)
        )
        ttk.Button(bottom, text="Edit…", command=self._edit_selected).pack(side="left", padx=(4, 0))
        ttk.Button(bottom, text="Delete", command=self._delete_selected).pack(side="left", padx=(4, 0))
        ttk.Button(bottom, text="Copy URL", command=self._copy_url).pack(side="left", padx=(4, 0))
        ttk.Button(bottom, text="Close", command=self.destroy).pack(side="right")

        self._sort_col = "title"
        self._sort_reverse = False

    def _populate(self) -> None:
        self._tree.delete(*self._tree.get_children())
        query = self._search_var.get()
        tag_filter = self._tag_var.get()
        bookmarks = self._store.list_bookmarks(search=query)
        all_tags: set[str] = set()
        for bm in self._store.list_bookmarks():
            all_tags.update(bm.tags)
        self._tag_combo["values"] = [""] + sorted(all_tags)

        if tag_filter:
            bookmarks = [b for b in bookmarks if tag_filter in b.tags]

        if self._sort_col == "created":
            bookmarks.sort(key=lambda b: b.created_at.isoformat(), reverse=self._sort_reverse)
        elif self._sort_col == "url":
            bookmarks.sort(key=lambda b: b.url.lower(), reverse=self._sort_reverse)
        else:
            bookmarks.sort(key=lambda b: b.title.lower(), reverse=self._sort_reverse)

        for bm in bookmarks:
            created = bm.created_at.strftime("%Y-%m-%d")
            tags_str = ", ".join(bm.tags)
            self._tree.insert("", "end", iid=bm.url, values=(bm.title, bm.url, tags_str, created))

    def _sort(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False
        self._populate()

    def _selected_url(self) -> str | None:
        sel = self._tree.selection()
        return sel[0] if sel else None

    def _on_select(self) -> None:
        url = self._selected_url()
        if not url:
            self._notes_label.configure(text="")
            return
        for bm in self._store.list_bookmarks():
            if bm.url == url:
                self._notes_label.configure(text=bm.notes or "")
                return

    def _open_selected(self, new_tab: bool) -> None:
        url = self._selected_url()
        if url:
            self._on_open(url, new_tab)
            self.destroy()

    def _edit_selected(self) -> None:
        url = self._selected_url()
        if not url:
            return
        for bm in self._store.list_bookmarks():
            if bm.url == url:
                dlg = BookmarkEditDialog(self, bm)
                if dlg.result is not None:
                    if dlg.result.url != bm.url:
                        self._store.remove(bm.url)
                    self._store.add(dlg.result)
                    self._populate()
                return

    def _delete_selected(self) -> None:
        url = self._selected_url()
        if not url:
            return
        if not messagebox.askyesno("Delete Bookmark", f"Delete bookmark for:\n{url}?", parent=self):
            return
        self._store.remove(url)
        self._populate()

    def _copy_url(self) -> None:
        url = self._selected_url()
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Bookmarks",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        bookmarks = self._store.list_bookmarks()
        data = [
            {
                "title": bm.title,
                "url": bm.url,
                "tags": bm.tags,
                "notes": bm.notes,
                "created_at": bm.created_at.isoformat(),
            }
            for bm in bookmarks
        ]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        messagebox.showinfo("Export", f"Exported {len(data)} bookmarks.", parent=self)

    def _import(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Import Bookmarks",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception as exc:
            messagebox.showerror("Import", f"Could not read file:\n{exc}", parent=self)
            return
        count = 0
        for entry in data:
            try:
                bm = Bookmark(
                    title=entry.get("title") or entry.get("url", ""),
                    url=entry["url"],
                    tags=entry.get("tags", []),
                    notes=entry.get("notes"),
                    created_at=(
                        datetime.fromisoformat(entry["created_at"]) if "created_at" in entry else datetime.now(UTC)
                    ),
                )
                self._store.add(bm)
                count += 1
            except Exception:  # pylint: disable=broad-except
                continue
        messagebox.showinfo("Import", f"Imported {count} bookmarks.", parent=self)
        self._populate()
