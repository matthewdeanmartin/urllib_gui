"""Preferences dialog — UI, network, rendering, proxy, and auth defaults."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from collections.abc import Callable

from urllib_gui.storage.app_config import AppConfig

_THEMES = ["light", "dark"]
_AUTH_SCHEMES = ["None", "Basic", "Bearer", "Custom header"]
_PROXY_MODES = ["Environment", "No proxy", "Manual"]
_ENGINES = ["stdlib_html_links", "stdlib_html_text", "plain", "html_source"]
_FONT_SIZES = [str(n) for n in range(8, 25)]


class PreferencesDialog(tk.Toplevel):
    """Tabbed preferences editor backed by AppConfig."""

    def __init__(
        self,
        parent: tk.Misc,
        config: AppConfig,
        *,
        on_apply: Callable[[AppConfig], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Preferences")
        self.resizable(False, False)
        self._config = config
        self._on_apply = on_apply
        self._build()
        self._load_values()
        self.grab_set()

    def _build(self) -> None:
        notebook = ttk.Notebook(self, padding=4)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_ui_tab(notebook)
        self._build_network_tab(notebook)
        self._build_proxy_tab(notebook)
        self._build_auth_tab(notebook)
        self._build_rendering_tab(notebook)

        btn_row = ttk.Frame(self, padding=(8, 0, 8, 8))
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Apply & Close", command=self._apply).pack(side="left")
        ttk.Button(btn_row, text="Cancel", command=self.destroy).pack(side="left", padx=(8, 0))

    def _row(self, parent: tk.Misc, label: str, row: int) -> ttk.Label:
        lbl = ttk.Label(parent, text=label, anchor="e", width=22)
        lbl.grid(row=row, column=0, sticky="e", padx=(8, 4), pady=4)
        return lbl

    def _build_ui_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Appearance")

        self._theme_var = tk.StringVar()
        self._row(tab, "Theme:", 0)
        ttk.Combobox(tab, values=_THEMES, textvariable=self._theme_var, state="readonly", width=14).grid(
            row=0, column=1, sticky="w", pady=4
        )

        self._font_family_var = tk.StringVar()
        self._row(tab, "Font family:", 1)
        ttk.Entry(tab, textvariable=self._font_family_var, width=22).grid(row=1, column=1, sticky="w", pady=4)

        self._font_size_var = tk.StringVar()
        self._row(tab, "Font size:", 2)
        ttk.Combobox(tab, values=_FONT_SIZES, textvariable=self._font_size_var, width=6).grid(
            row=2, column=1, sticky="w", pady=4
        )

        self._new_tab_var = tk.BooleanVar()
        self._row(tab, "Open links in new tab:", 3)
        ttk.Checkbutton(tab, variable=self._new_tab_var).grid(row=3, column=1, sticky="w", pady=4)

    def _build_network_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Network")

        self._timeout_var = tk.StringVar()
        self._row(tab, "Default timeout (s):", 0)
        ttk.Entry(tab, textvariable=self._timeout_var, width=10).grid(row=0, column=1, sticky="w", pady=4)
        ttk.Label(tab, text="blank = no timeout").grid(row=0, column=2, sticky="w", padx=4)

        self._user_agent_var = tk.StringVar()
        self._row(tab, "Default User-Agent:", 1)
        ttk.Entry(tab, textvariable=self._user_agent_var, width=36).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=4
        )

        self._cookies_var = tk.BooleanVar()
        self._row(tab, "Enable cookies:", 2)
        ttk.Checkbutton(tab, variable=self._cookies_var).grid(row=2, column=1, sticky="w", pady=4)

        self._verify_tls_var = tk.BooleanVar()
        self._row(tab, "Verify TLS certificates:", 3)
        tls_frame = ttk.Frame(tab)
        tls_frame.grid(row=3, column=1, sticky="w", pady=4)
        ttk.Checkbutton(tls_frame, variable=self._verify_tls_var).pack(side="left")
        self._tls_warn = ttk.Label(tls_frame, text="(insecure!)", foreground="red")
        self._verify_tls_var.trace_add("write", lambda *_: self._on_tls_changed())

    def _on_tls_changed(self) -> None:
        if not self._verify_tls_var.get():
            self._tls_warn.pack(side="left", padx=(4, 0))
        else:
            self._tls_warn.pack_forget()

    def _build_proxy_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Proxy")

        self._proxy_mode_var = tk.StringVar()
        self._row(tab, "Proxy mode:", 0)
        ttk.Combobox(tab, values=_PROXY_MODES, textvariable=self._proxy_mode_var, state="readonly", width=16).grid(
            row=0, column=1, sticky="w", pady=4
        )
        self._proxy_mode_var.trace_add("write", lambda *_: self._on_proxy_mode_changed())

        self._proxy_url_var = tk.StringVar()
        self._proxy_url_label = self._row(tab, "Proxy URL:", 1)
        self._proxy_url_entry = ttk.Entry(tab, textvariable=self._proxy_url_var, width=36)
        self._proxy_url_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)
        self._proxy_hint = ttk.Label(tab, text="e.g. http://proxy.example.com:8080", foreground="gray")
        self._proxy_hint.grid(row=2, column=1, columnspan=2, sticky="w")

        self._proxy_url_label.grid_remove()
        self._proxy_url_entry.grid_remove()
        self._proxy_hint.grid_remove()

    def _on_proxy_mode_changed(self) -> None:
        if self._proxy_mode_var.get() == "Manual":
            self._proxy_url_label.grid()
            self._proxy_url_entry.grid()
            self._proxy_hint.grid()
        else:
            self._proxy_url_label.grid_remove()
            self._proxy_url_entry.grid_remove()
            self._proxy_hint.grid_remove()

    def _build_auth_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Auth Defaults")

        ttk.Label(tab, text="Default auth settings applied to new requests.", foreground="gray").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )

        self._auth_scheme_var = tk.StringVar()
        self._row(tab, "Auth scheme:", 1)
        ttk.Combobox(tab, values=_AUTH_SCHEMES, textvariable=self._auth_scheme_var, state="readonly", width=16).grid(
            row=1, column=1, sticky="w", pady=4
        )
        self._auth_scheme_var.trace_add("write", lambda *_: self._on_auth_changed())

        self._auth_username_var = tk.StringVar()
        self._auth_username_row_label = self._row(tab, "Username:", 2)
        self._auth_username_entry = ttk.Entry(tab, textvariable=self._auth_username_var, width=28)
        self._auth_username_entry.grid(row=2, column=1, sticky="w", pady=4)

        self._auth_token_var = tk.StringVar()
        self._auth_token_row_label = self._row(tab, "Token / header value:", 3)
        self._auth_token_entry = ttk.Entry(tab, textvariable=self._auth_token_var, width=36)
        self._auth_token_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=4)

        for w in (
            self._auth_username_row_label,
            self._auth_username_entry,
            self._auth_token_row_label,
            self._auth_token_entry,
        ):
            w.grid_remove()

    def _on_auth_changed(self) -> None:
        scheme = self._auth_scheme_var.get()
        for w in (self._auth_username_row_label, self._auth_username_entry):
            if scheme == "Basic":
                w.grid()
            else:
                w.grid_remove()
        for w in (self._auth_token_row_label, self._auth_token_entry):
            if scheme in ("Bearer", "Custom header"):
                w.grid()
            else:
                w.grid_remove()

    def _build_rendering_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Rendering")

        self._engine_var = tk.StringVar()
        self._row(tab, "Default render engine:", 0)
        ttk.Combobox(tab, values=_ENGINES, textvariable=self._engine_var, state="readonly", width=22).grid(
            row=0, column=1, sticky="w", pady=4
        )

        self._encoding_var = tk.StringVar()
        self._row(tab, "Default encoding:", 1)
        ttk.Entry(tab, textvariable=self._encoding_var, width=14).grid(row=1, column=1, sticky="w", pady=4)

    def _load_values(self) -> None:
        c = self._config
        self._theme_var.set(c.theme)
        self._font_family_var.set(c.font_family)
        self._font_size_var.set(str(c.font_size))
        self._new_tab_var.set(c.open_links_in_new_tab)
        self._timeout_var.set(c.get("network", "timeout"))
        self._user_agent_var.set(c.default_user_agent)
        self._cookies_var.set(c.cookies_enabled)
        self._verify_tls_var.set(c.verify_tls)
        self._proxy_mode_var.set(c.proxy_mode)
        self._proxy_url_var.set(c.proxy_url)
        self._on_proxy_mode_changed()
        self._on_tls_changed()
        self._auth_scheme_var.set(c.get("auth", "default_scheme"))
        self._auth_username_var.set(c.get("auth", "default_username"))
        self._auth_token_var.set(c.get("auth", "default_token"))
        self._on_auth_changed()
        self._engine_var.set(c.default_engine)
        self._encoding_var.set(c.get("rendering", "default_encoding"))

    def _apply(self) -> None:
        c = self._config
        c.theme = self._theme_var.get()
        c.font_family = self._font_family_var.get().strip() or "TkDefaultFont"
        try:
            c.font_size = int(self._font_size_var.get())
        except ValueError:
            messagebox.showwarning("Preferences", "Font size must be an integer.", parent=self)
            return
        c.set("ui", "open_links_in_new_tab", "true" if self._new_tab_var.get() else "false")
        timeout_str = self._timeout_var.get().strip()
        if timeout_str:
            try:
                float(timeout_str)
            except ValueError:
                messagebox.showwarning("Preferences", "Timeout must be a number.", parent=self)
                return
        c.set("network", "timeout", timeout_str or "30")
        c.set("network", "user_agent", self._user_agent_var.get().strip() or "urllib_gui/0.1")
        c.set("network", "cookies_enabled", "true" if self._cookies_var.get() else "false")
        c.set("network", "verify_tls", "true" if self._verify_tls_var.get() else "false")
        c.set("network", "proxy_mode", self._proxy_mode_var.get())
        c.set("network", "proxy_url", self._proxy_url_var.get().strip())
        c.set("auth", "default_scheme", self._auth_scheme_var.get())
        c.set("auth", "default_username", self._auth_username_var.get().strip())
        c.set("auth", "default_token", self._auth_token_var.get().strip())
        c.set("rendering", "default_engine", self._engine_var.get())
        c.set("rendering", "default_encoding", self._encoding_var.get().strip() or "utf-8")
        c.save()
        if self._on_apply:
            self._on_apply(c)
        self.destroy()
