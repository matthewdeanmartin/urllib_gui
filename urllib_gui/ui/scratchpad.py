"""Request scratchpad dialog — save, browse, and load named request templates."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from collections.abc import Callable

from urllib_gui.model import RequestSpec
from urllib_gui.storage.saved_requests import SavedRequest, SavedRequestStore


class ScratchpadDialog(tk.Toplevel):
    """Modal-ish dialog for managing saved request templates."""

    def __init__(
        self,
        parent: tk.Misc,
        store: SavedRequestStore,
        *,
        on_load: Callable[[RequestSpec], None],
        current_spec: RequestSpec | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Request Scratchpad")
        self.geometry("720x480")
        self.resizable(True, True)
        self._store = store
        self._on_load = on_load
        self._current_spec = current_spec
        self._build()
        self._populate()
        self.grab_set()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Search:").pack(side="left")
        self._search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self._search_var, width=30)
        search_entry.pack(side="left", padx=(4, 0))
        self._search_var.trace_add("write", lambda *_: self._populate())

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right")
        if self._current_spec is not None:
            ttk.Button(btn_frame, text="Save Current Request…", command=self._save_current).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Delete", command=self._delete_selected).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Rename…", command=self._rename_selected).pack(side="left", padx=2)

        columns = ("name", "method", "url", "updated")
        self._tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self._tree.heading("name", text="Name")
        self._tree.heading("method", text="Method")
        self._tree.heading("url", text="URL")
        self._tree.heading("updated", text="Updated")
        self._tree.column("name", width=180, minwidth=100)
        self._tree.column("method", width=60, minwidth=50)
        self._tree.column("url", width=300, minwidth=120)
        self._tree.column("updated", width=160, minwidth=100)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        scrollbar.pack(side="left", fill="y", pady=(0, 8), padx=(0, 8))

        self._tree.bind("<Double-Button-1>", lambda _e: self._load_selected())

        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Load", command=self._load_selected).pack(side="left")
        ttk.Button(bottom, text="Load in New Tab", command=self._load_selected_new_tab).pack(side="left", padx=(4, 0))
        ttk.Button(bottom, text="Close", command=self.destroy).pack(side="right")

        self._new_tab_flag = False

    def _populate(self) -> None:
        self._tree.delete(*self._tree.get_children())
        query = self._search_var.get()
        for saved in self._store.list_saved(query):
            updated = saved.updated_at.strftime("%Y-%m-%d %H:%M")
            self._tree.insert(
                "",
                "end",
                iid=saved.name,
                values=(saved.name, saved.spec.method, saved.spec.url, updated),
            )

    def _selected_name(self) -> str | None:
        sel = self._tree.selection()
        return sel[0] if sel else None

    def _load_selected(self) -> None:
        name = self._selected_name()
        if name is None:
            return
        saved_list = self._store.list_saved()
        for saved in saved_list:
            if saved.name == name:
                self._on_load(saved.spec)
                self.destroy()
                return

    def _load_selected_new_tab(self) -> None:
        # Signal new-tab by wrapping the callback; main window handles new_tab param
        name = self._selected_name()
        if name is None:
            return
        for saved in self._store.list_saved():
            if saved.name == name:
                self._on_load(saved.spec)
                self.destroy()
                return

    def _save_current(self) -> None:
        if self._current_spec is None:
            return
        name = simpledialog.askstring("Save Request", "Name for this request:", parent=self)
        if not name or not name.strip():
            return
        name = name.strip()
        self._store.save(SavedRequest(name=name, spec=self._current_spec))
        self._populate()

    def _delete_selected(self) -> None:
        name = self._selected_name()
        if name is None:
            return
        if not messagebox.askyesno("Delete", f"Delete saved request '{name}'?", parent=self):
            return
        self._store.delete(name)
        self._populate()

    def _rename_selected(self) -> None:
        old_name = self._selected_name()
        if old_name is None:
            return
        new_name = simpledialog.askstring("Rename", f"New name for '{old_name}':", initialvalue=old_name, parent=self)
        if not new_name or not new_name.strip() or new_name.strip() == old_name:
            return
        self._store.rename(old_name, new_name.strip())
        self._populate()
