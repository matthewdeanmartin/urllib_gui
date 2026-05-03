"""Cookie jar inspection and management dialog."""

from __future__ import annotations

import time
import tkinter as tk
from collections.abc import Callable
from http.cookiejar import CookieJar
from tkinter import messagebox, ttk


class CookieJarDialog(tk.Toplevel):
    """Dialog for inspecting and clearing cookies from the active CookieJar."""

    def __init__(
        self,
        parent: tk.Misc,
        cookie_jar: CookieJar,
        *,
        on_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Cookie Jar")
        self.geometry("860x400")
        self.resizable(True, True)
        self._jar = cookie_jar
        self._on_changed = on_changed
        self._build()
        self._populate()
        self.grab_set()

    def _build(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Filter domain:").pack(side="left")
        self._filter_var = tk.StringVar()
        filter_entry = ttk.Entry(top, textvariable=self._filter_var, width=24)
        filter_entry.pack(side="left", padx=(4, 0))
        self._filter_var.trace_add("write", lambda *_: self._populate())

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="Delete Selected", command=self._delete_selected).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear All", command=self._clear_all).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self._populate).pack(side="left", padx=2)

        cols = ("domain", "name", "value", "path", "secure", "expires")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", selectmode="extended")
        self._tree.heading("domain", text="Domain")
        self._tree.heading("name", text="Name")
        self._tree.heading("value", text="Value")
        self._tree.heading("path", text="Path")
        self._tree.heading("secure", text="Secure")
        self._tree.heading("expires", text="Expires")
        self._tree.column("domain", width=180, minwidth=100)
        self._tree.column("name", width=140, minwidth=80)
        self._tree.column("value", width=200, minwidth=80)
        self._tree.column("path", width=80, minwidth=40)
        self._tree.column("secure", width=55, minwidth=40)
        self._tree.column("expires", width=110, minwidth=80)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        scrollbar.pack(side="left", fill="y", pady=(0, 8), padx=(0, 8))

        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.pack(fill="x")
        self._count_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=self._count_var).pack(side="left")
        ttk.Button(bottom, text="Close", command=self.destroy).pack(side="right")

    def _populate(self) -> None:
        self._tree.delete(*self._tree.get_children())
        query = self._filter_var.get().lower()
        count = 0
        for cookie in self._jar:
            domain = cookie.domain or ""
            if query and query not in domain.lower():
                continue
            expires_str = ""
            if cookie.expires is not None:
                try:
                    expires_str = time.strftime("%Y-%m-%d", time.gmtime(cookie.expires))
                except (OSError, OverflowError):
                    expires_str = str(cookie.expires)
            self._tree.insert(
                "",
                "end",
                values=(
                    domain,
                    cookie.name,
                    cookie.value or "",
                    cookie.path or "/",
                    "yes" if cookie.secure else "no",
                    expires_str,
                ),
            )
            count += 1
        noun = "cookie" if count == 1 else "cookies"
        self._count_var.set(f"{count} {noun}")

    def _delete_selected(self) -> None:
        selected = self._tree.selection()
        if not selected:
            return
        to_remove = []
        for item in selected:
            vals = self._tree.item(item, "values")
            domain, name, _value, path = vals[0], vals[1], vals[2], vals[3]
            to_remove.append((domain, name, path))

        remaining = []
        for cookie in self._jar:
            key = (cookie.domain or "", cookie.name, cookie.path or "/")
            if key not in to_remove:
                remaining.append(cookie)
        self._jar.clear()
        for cookie in remaining:
            self._jar.set_cookie(cookie)
        if self._on_changed:
            self._on_changed()
        self._populate()

    def _clear_all(self) -> None:
        if not messagebox.askyesno("Clear Cookies", "Delete all cookies from the jar?", parent=self):
            return
        self._jar.clear()
        if self._on_changed:
            self._on_changed()
        self._populate()
