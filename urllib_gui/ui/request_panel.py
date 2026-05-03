"""Expanded request drawer for urllib_gui."""

from __future__ import annotations

import tkinter as tk
import urllib.parse
from collections.abc import Callable
from functools import partial
from tkinter import ttk

from urllib_gui.model import AuthSpec, RequestSpec, format_request_preview

HTTP_METHODS = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "Custom..."]

HEADER_PRESETS: dict[str, list[tuple[str, str]]] = {
    "Browser-ish": [
        ("User-Agent", "Mozilla/5.0 (compatible; urllib_gui/0.1)"),
        ("Accept", "text/html,application/xhtml+xml,*/*;q=0.8"),
        ("Accept-Language", "en-US,en;q=0.5"),
    ],
    "urllib default": [
        ("User-Agent", "Python-urllib/3.x"),
        ("Accept", "*/*"),
    ],
    "JSON API": [
        ("Accept", "application/json"),
        ("Content-Type", "application/json"),
    ],
    "Plain text": [
        ("Accept", "text/plain"),
    ],
    "HTML only": [
        ("Accept", "text/html"),
    ],
    "No cache": [
        ("Cache-Control", "no-cache"),
        ("Pragma", "no-cache"),
    ],
}

BODY_TYPES = ["raw", "form-urlencoded", "json"]

REDIRECT_OPTIONS = ["Follow redirects", "Do not follow"]

AUTH_SCHEMES = ["None", "Basic", "Bearer", "Custom header"]


class HeadersEditor(ttk.Frame):  # pylint: disable=too-many-ancestors
    """Editable table of request headers with enable/disable checkboxes."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self._rows: list[tuple[tk.BooleanVar, tk.StringVar, tk.StringVar]] = []
        self._row_frames: list[ttk.Frame] = []

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 4))
        ttk.Label(top, text="Headers", font=("TkDefaultFont", 9, "bold")).pack(side="left")
        ttk.Button(top, text="+ Add", command=self.add_row).pack(side="right")

        presets_menu_btn = ttk.Menubutton(top, text="Presets")
        presets_menu_btn.pack(side="right", padx=(0, 4))
        presets_menu = tk.Menu(presets_menu_btn, tearoff=False)
        for preset_name in HEADER_PRESETS:
            presets_menu.add_command(
                label=preset_name,
                command=partial(self.apply_preset, preset_name),
            )
        presets_menu.add_separator()
        presets_menu.add_command(label="Clear all", command=self.clear_rows)
        presets_menu_btn["menu"] = presets_menu

        col_header = ttk.Frame(self)
        col_header.pack(fill="x")
        ttk.Label(col_header, text="On", width=3, anchor="center").pack(side="left")
        ttk.Label(col_header, text="Name", width=20).pack(side="left", padx=(4, 0))
        ttk.Label(col_header, text="Value").pack(side="left", padx=(4, 0), fill="x", expand=True)
        ttk.Label(col_header, text="", width=3).pack(side="left")

        self.rows_frame = ttk.Frame(self)
        self.rows_frame.pack(fill="x")

    def add_row(
        self,
        *,
        enabled: bool = True,
        name: str = "",
        value: str = "",
    ) -> None:
        enabled_var = tk.BooleanVar(value=enabled)
        name_var = tk.StringVar(value=name)
        value_var = tk.StringVar(value=value)
        idx = len(self._rows)
        self._rows.append((enabled_var, name_var, value_var))

        row_frame = ttk.Frame(self.rows_frame)
        row_frame.pack(fill="x", pady=1)
        self._row_frames.append(row_frame)

        ttk.Checkbutton(row_frame, variable=enabled_var).pack(side="left")
        ttk.Entry(row_frame, textvariable=name_var, width=20).pack(side="left", padx=(4, 0))
        ttk.Entry(row_frame, textvariable=value_var).pack(side="left", padx=(4, 0), fill="x", expand=True)
        ttk.Button(
            row_frame,
            text="x",
            width=2,
            command=partial(self.remove_row, idx),
        ).pack(side="left", padx=(4, 0))

    def remove_row(self, index: int) -> None:
        if index >= len(self._row_frames):
            return
        self._row_frames[index].destroy()
        self._row_frames[index] = ttk.Frame(self.rows_frame)  # placeholder
        self._rows[index] = (tk.BooleanVar(value=False), tk.StringVar(value="__removed__"), tk.StringVar())

    def clear_rows(self) -> None:
        for frame in self._row_frames:
            frame.destroy()
        self._rows.clear()
        self._row_frames.clear()

    def apply_preset(self, preset_name: str) -> None:
        self.clear_rows()
        for name, value in HEADER_PRESETS[preset_name]:
            self.add_row(enabled=True, name=name, value=value)

    def get_headers(self) -> list[tuple[str, str]]:
        result = []
        for enabled_var, name_var, value_var in self._rows:
            name = name_var.get().strip()
            if name == "__removed__" or not name:
                continue
            if enabled_var.get():
                result.append((name, value_var.get()))
        return result

    def set_headers(self, headers: list[tuple[str, str]]) -> None:
        self.clear_rows()
        for name, value in headers:
            self.add_row(enabled=True, name=name, value=value)


class BodyEditor(ttk.Frame):  # pylint: disable=too-many-ancestors
    """Body editor with type selector and text area."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.body_type_var = tk.StringVar(value="raw")

        top = ttk.Frame(self)
        ttk.Label(top, text="Body", font=("TkDefaultFont", 9, "bold")).pack(side="left")
        ttk.Label(top, text="Type:").pack(side="left", padx=(8, 2))
        ttk.Combobox(
            top,
            values=BODY_TYPES,
            textvariable=self.body_type_var,
            state="readonly",
            width=18,
        ).pack(side="left")

        self.text = tk.Text(self, height=4, wrap="none", undo=True)
        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scroll_y.set)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self.text.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def get_body(self) -> bytes | None:
        raw = self.text.get("1.0", "end-1c").strip()
        if not raw:
            return None
        body_type = self.body_type_var.get()
        if body_type == "form-urlencoded":
            pairs = urllib.parse.parse_qsl(raw, keep_blank_values=True)
            return urllib.parse.urlencode(pairs).encode()
        return raw.encode("utf-8", errors="replace")

    def get_content_type_header(self) -> tuple[str, str] | None:
        body_type = self.body_type_var.get()
        if body_type == "form-urlencoded":
            return ("Content-Type", "application/x-www-form-urlencoded")
        if body_type == "json":
            return ("Content-Type", "application/json")
        return None

    def set_body(self, body: bytes | None) -> None:
        self.text.delete("1.0", "end")
        if body:
            self.text.insert("1.0", body.decode("utf-8", errors="replace"))


class RequestDrawer(ttk.Frame):  # pylint: disable=too-many-ancestors
    """Collapsible expanded request configuration panel."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        on_submit: Callable[[RequestSpec], None] | None = None,
    ) -> None:
        super().__init__(master)
        self.on_submit = on_submit
        self._visible = False

        self.toggle_var = tk.BooleanVar(value=False)
        self.toggle_btn = ttk.Checkbutton(
            self,
            text="Request Options",
            variable=self.toggle_var,
            command=self._toggle,
            style="Toolbutton",
        )
        self.toggle_btn.pack(anchor="w", padx=8, pady=(4, 0))

        self._panel = ttk.Frame(self, relief="sunken", borderwidth=1)

        self._build_panel()

    def _build_panel(self) -> None:
        panel = self._panel
        notebook = ttk.Notebook(panel)
        notebook.pack(fill="both", expand=True, padx=4, pady=4)

        self._build_basic_tab(notebook)
        self._build_headers_tab(notebook)
        self._build_body_tab(notebook)
        self._build_network_tab(notebook)
        self._build_auth_tab(notebook)
        self._build_preview_tab(notebook)

        btn_row = ttk.Frame(panel)
        btn_row.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(btn_row, text="Send Request", command=self._send).pack(side="left")
        ttk.Button(btn_row, text="Refresh Preview", command=self._refresh_preview).pack(side="left", padx=(8, 0))
        ttk.Button(btn_row, text="Reset", command=self._reset).pack(side="right")

    def _build_basic_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Basic")

        self.method_var = tk.StringVar(value="GET")
        self.custom_method_var = tk.StringVar(value="")
        self.url_var = tk.StringVar(value="")

        method_row = ttk.Frame(tab)
        method_row.pack(fill="x", pady=(0, 4))
        ttk.Label(method_row, text="Method:", width=10, anchor="e").pack(side="left")
        self.method_combo = ttk.Combobox(
            method_row,
            values=HTTP_METHODS,
            textvariable=self.method_var,
            state="readonly",
            width=14,
        )
        self.method_combo.pack(side="left", padx=(4, 0))
        self.custom_method_entry = ttk.Entry(method_row, textvariable=self.custom_method_var, width=14)
        self.method_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_method_changed())

        url_row = ttk.Frame(tab)
        url_row.pack(fill="x", pady=(0, 4))
        ttk.Label(url_row, text="URL:", width=10, anchor="e").pack(side="left")
        ttk.Entry(url_row, textvariable=self.url_var).pack(side="left", padx=(4, 0), fill="x", expand=True)

        self.redirect_var = tk.StringVar(value="Follow redirects")
        redirect_row = ttk.Frame(tab)
        redirect_row.pack(fill="x", pady=(0, 4))
        ttk.Label(redirect_row, text="Redirects:", width=10, anchor="e").pack(side="left")
        ttk.Combobox(
            redirect_row,
            values=REDIRECT_OPTIONS,
            textvariable=self.redirect_var,
            state="readonly",
            width=20,
        ).pack(side="left", padx=(4, 0))

        self.user_agent_var = tk.StringVar(value="urllib_gui/0.1")
        ua_row = ttk.Frame(tab)
        ua_row.pack(fill="x", pady=(0, 4))
        ttk.Label(ua_row, text="User-Agent:", width=10, anchor="e").pack(side="left")
        ttk.Entry(ua_row, textvariable=self.user_agent_var).pack(side="left", padx=(4, 0), fill="x", expand=True)

    def _on_method_changed(self) -> None:
        if self.method_var.get() == "Custom...":
            self.custom_method_entry.pack(side="left", padx=(4, 0))
            self.custom_method_entry.focus_set()
        else:
            self.custom_method_entry.pack_forget()

    def _build_headers_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Headers")
        self.headers_editor = HeadersEditor(tab)
        self.headers_editor.pack(fill="both", expand=True)

    def _build_body_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Body")
        self.body_editor = BodyEditor(tab)
        self.body_editor.pack(fill="both", expand=True)

    def _build_network_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Network")

        self.timeout_var = tk.StringVar(value="30")
        timeout_row = ttk.Frame(tab)
        timeout_row.pack(fill="x", pady=(0, 6))
        ttk.Label(timeout_row, text="Timeout (s):", width=16, anchor="e").pack(side="left")
        ttk.Entry(timeout_row, textvariable=self.timeout_var, width=10).pack(side="left", padx=(4, 0))
        ttk.Label(timeout_row, text="(blank = no timeout)").pack(side="left", padx=(8, 0))

        self.proxy_mode_var = tk.StringVar(value="Environment")
        proxy_row = ttk.Frame(tab)
        proxy_row.pack(fill="x", pady=(0, 4))
        ttk.Label(proxy_row, text="Proxy:", width=16, anchor="e").pack(side="left")
        ttk.Combobox(
            proxy_row,
            values=["No proxy", "Environment", "Manual"],
            textvariable=self.proxy_mode_var,
            state="readonly",
            width=14,
        ).pack(side="left", padx=(4, 0))
        self.proxy_mode_var.trace_add("write", lambda *_: self._on_proxy_mode_changed())

        self.proxy_url_var = tk.StringVar(value="")
        self.proxy_url_row = ttk.Frame(tab)
        ttk.Label(self.proxy_url_row, text="Proxy URL:", width=16, anchor="e").pack(side="left")
        ttk.Entry(self.proxy_url_row, textvariable=self.proxy_url_var).pack(
            side="left", padx=(4, 0), fill="x", expand=True
        )

        self.verify_tls_var = tk.BooleanVar(value=True)
        tls_row = ttk.Frame(tab)
        tls_row.pack(fill="x", pady=(6, 4))
        ttk.Checkbutton(tls_row, text="Verify TLS certificates", variable=self.verify_tls_var).pack(side="left")
        self.tls_warning = ttk.Label(tls_row, text="(insecure!)", foreground="red")
        self.verify_tls_var.trace_add("write", lambda *_: self._on_tls_changed())

        self.cookies_var = tk.BooleanVar(value=True)
        cookie_row = ttk.Frame(tab)
        cookie_row.pack(fill="x", pady=(0, 4))
        ttk.Checkbutton(cookie_row, text="Enable cookies", variable=self.cookies_var).pack(side="left")

    def _on_proxy_mode_changed(self) -> None:
        if self.proxy_mode_var.get() == "Manual":
            self.proxy_url_row.pack(fill="x", pady=(0, 4))
        else:
            self.proxy_url_row.pack_forget()

    def _on_tls_changed(self) -> None:
        if not self.verify_tls_var.get():
            self.tls_warning.pack(side="left", padx=(4, 0))
        else:
            self.tls_warning.pack_forget()

    def _build_auth_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Auth")

        self.auth_scheme_var = tk.StringVar(value="None")
        scheme_row = ttk.Frame(tab)
        scheme_row.pack(fill="x", pady=(0, 8))
        ttk.Label(scheme_row, text="Auth type:", width=16, anchor="e").pack(side="left")
        ttk.Combobox(
            scheme_row,
            values=AUTH_SCHEMES,
            textvariable=self.auth_scheme_var,
            state="readonly",
            width=18,
        ).pack(side="left", padx=(4, 0))
        self.auth_scheme_var.trace_add("write", lambda *_: self._on_auth_changed())

        self.auth_username_var = tk.StringVar(value="")
        self.auth_password_var = tk.StringVar(value="")
        self.auth_token_var = tk.StringVar(value="")
        self.auth_header_var = tk.StringVar(value="")

        self.auth_basic_frame = ttk.Frame(tab)
        ttk.Label(self.auth_basic_frame, text="Username:", width=16, anchor="e").pack(side="left")
        ttk.Entry(self.auth_basic_frame, textvariable=self.auth_username_var, width=24).pack(side="left", padx=(4, 0))
        ttk.Label(self.auth_basic_frame, text="Password:").pack(side="left", padx=(8, 0))
        ttk.Entry(self.auth_basic_frame, textvariable=self.auth_password_var, width=24, show="*").pack(
            side="left", padx=(4, 0)
        )

        self.auth_bearer_frame = ttk.Frame(tab)
        ttk.Label(self.auth_bearer_frame, text="Token:", width=16, anchor="e").pack(side="left")
        ttk.Entry(self.auth_bearer_frame, textvariable=self.auth_token_var).pack(
            side="left", padx=(4, 0), fill="x", expand=True
        )

        self.auth_header_frame = ttk.Frame(tab)
        ttk.Label(self.auth_header_frame, text="Authorization:", width=16, anchor="e").pack(side="left")
        ttk.Entry(self.auth_header_frame, textvariable=self.auth_header_var).pack(
            side="left", padx=(4, 0), fill="x", expand=True
        )

    def _on_auth_changed(self) -> None:
        for frame in (self.auth_basic_frame, self.auth_bearer_frame, self.auth_header_frame):
            frame.pack_forget()
        scheme = self.auth_scheme_var.get()
        if scheme == "Basic":
            self.auth_basic_frame.pack(fill="x")
        elif scheme == "Bearer":
            self.auth_bearer_frame.pack(fill="x")
        elif scheme == "Custom header":
            self.auth_header_frame.pack(fill="x")

    def _build_preview_tab(self, notebook: ttk.Notebook) -> None:
        tab = ttk.Frame(notebook, padding=8)
        notebook.add(tab, text="Preview")
        self.preview_text = tk.Text(tab, state="disabled", wrap="none", height=8)
        scroll_y = ttk.Scrollbar(tab, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scroll_y.set)
        self.preview_text.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)

    def _refresh_preview(self) -> None:
        spec = self.build_request_spec()
        preview = format_request_preview(spec)
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", preview)
        self.preview_text.configure(state="disabled")

    def _send(self) -> None:
        if self.on_submit:
            spec = self.build_request_spec()
            self.on_submit(spec)

    def _reset(self) -> None:
        self.method_var.set("GET")
        self.custom_method_var.set("")
        self.custom_method_entry.pack_forget()
        self.redirect_var.set("Follow redirects")
        self.user_agent_var.set("urllib_gui/0.1")
        self.headers_editor.clear_rows()
        self.body_editor.set_body(None)
        self.body_editor.body_type_var.set("raw")
        self.timeout_var.set("30")
        self.proxy_mode_var.set("Environment")
        self.proxy_url_var.set("")
        self.verify_tls_var.set(True)
        self.cookies_var.set(True)
        self.auth_scheme_var.set("None")
        self.auth_username_var.set("")
        self.auth_password_var.set("")
        self.auth_token_var.set("")
        self.auth_header_var.set("")

    def _toggle(self) -> None:
        if self.toggle_var.get():
            self._panel.pack(fill="x", padx=4, pady=(0, 4))
            self._visible = True
        else:
            self._panel.pack_forget()
            self._visible = False

    def show(self) -> None:
        """Programmatically open the drawer."""
        self.toggle_var.set(True)
        self._toggle()

    def hide(self) -> None:
        """Programmatically close the drawer."""
        self.toggle_var.set(False)
        self._toggle()

    def build_request_spec(self) -> RequestSpec:
        """Build a RequestSpec from the current drawer state."""
        url = self.url_var.get().strip()

        method = self.method_var.get()
        if method == "Custom...":
            method = self.custom_method_var.get().strip().upper() or "GET"

        headers = self.headers_editor.get_headers()
        ct_header = self.body_editor.get_content_type_header()
        if ct_header:
            header_names_lower = {n.lower() for n, _ in headers}
            if "content-type" not in header_names_lower:
                headers.append(ct_header)

        body = self.body_editor.get_body() if method not in ("GET", "HEAD") else None

        timeout_str = self.timeout_var.get().strip()
        try:
            timeout: float | None = float(timeout_str) if timeout_str else None
        except ValueError:
            timeout = 30.0

        proxy_mode = self.proxy_mode_var.get()
        proxy: str | None = None
        if proxy_mode == "Manual":
            proxy = self.proxy_url_var.get().strip() or None
        elif proxy_mode == "No proxy":
            proxy = ""  # empty string signals no proxy in client

        follow_redirects = self.redirect_var.get() == "Follow redirects"
        verify_tls = self.verify_tls_var.get()
        cookies_enabled = self.cookies_var.get()
        user_agent = self.user_agent_var.get().strip() or None

        auth: AuthSpec | None = None
        scheme = self.auth_scheme_var.get()
        if scheme == "Basic":
            auth = AuthSpec(
                scheme="basic",
                username=self.auth_username_var.get(),
                password=self.auth_password_var.get(),
            )
        elif scheme == "Bearer":
            auth = AuthSpec(scheme="bearer", token=self.auth_token_var.get())
        elif scheme == "Custom header":
            auth = AuthSpec(scheme="header", header_value=self.auth_header_var.get())

        return RequestSpec(
            url=url,
            method=method,
            headers=headers,
            body=body,
            timeout=timeout,
            follow_redirects=follow_redirects,
            verify_tls=verify_tls,
            proxy=proxy if proxy else None,
            user_agent=user_agent,
            cookies_enabled=cookies_enabled,
            auth=auth,
        )

    def populate_from_spec(self, spec: RequestSpec) -> None:
        """Load drawer fields from an existing RequestSpec."""
        self.url_var.set(spec.url)
        method = spec.method.upper()
        if method in HTTP_METHODS:
            self.method_var.set(method)
        else:
            self.method_var.set("Custom...")
            self.custom_method_var.set(method)
            self._on_method_changed()

        self.redirect_var.set("Follow redirects" if spec.follow_redirects else "Do not follow")
        self.user_agent_var.set(spec.user_agent or "urllib_gui/0.1")
        self.headers_editor.set_headers(spec.headers)
        self.body_editor.set_body(spec.body)
        if spec.timeout is not None:
            self.timeout_var.set(str(spec.timeout))
        else:
            self.timeout_var.set("")
        self.verify_tls_var.set(spec.verify_tls)
        self.cookies_var.set(spec.cookies_enabled)

        if spec.proxy:
            self.proxy_mode_var.set("Manual")
            self.proxy_url_var.set(spec.proxy)
        else:
            self.proxy_mode_var.set("Environment")

        if spec.auth is None:
            self.auth_scheme_var.set("None")
        elif spec.auth.scheme == "basic":
            self.auth_scheme_var.set("Basic")
            self.auth_username_var.set(spec.auth.username or "")
            self.auth_password_var.set(spec.auth.password or "")
        elif spec.auth.scheme == "bearer":
            self.auth_scheme_var.set("Bearer")
            self.auth_token_var.set(spec.auth.token or "")
        elif spec.auth.scheme == "header":
            self.auth_scheme_var.set("Custom header")
            self.auth_header_var.set(spec.auth.header_value or "")
