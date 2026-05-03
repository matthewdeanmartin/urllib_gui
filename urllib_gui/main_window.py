"""Main Tkinter window for urllib_gui."""

from __future__ import annotations

import time
import tkinter as tk
import webbrowser
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import suppress
from dataclasses import dataclass, replace
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import cast
from urllib.parse import urlparse

from urllib_gui.client import UrllibClient
from urllib_gui.export import generate_curl_command, generate_urllib_code
from urllib_gui.model import (
    RenderedDocument,
    RequestSpec,
    ResponseRecord,
    TabState,
    choose_tab_title,
    format_request_preview,
    history_entry_from_response,
    make_bookmark,
    normalize_url,
)
from urllib_gui.render import built_in_renderers, choose_default_engine_name
from urllib_gui.storage import AppConfig, BookmarkStore, HistoryStore, SavedRequest, SavedRequestStore
from urllib_gui.storage.saved_requests import json_to_spec, spec_to_json
from urllib_gui.ui import (
    BookmarksDialog,
    CookieJarDialog,
    HistoryDialog,
    HypertextViewer,
    PreferencesDialog,
    RequestDrawer,
    ScratchpadDialog,
)

VIEW_MODES = ("Rendered", "Source", "Headers", "Request")

THEMES = {
    "light": {
        "background": "#ffffff",
        "foreground": "#111111",
        "link": "#005cc5",
        "visited": "#800080",
    },
    "dark": {
        "background": "#1e1e1e",
        "foreground": "#dddddd",
        "link": "#6ab0ff",
        "visited": "#b48cff",
    },
}


@dataclass
class BrowserTab:
    """A notebook tab and its state."""

    frame: ttk.Frame
    viewer: HypertextViewer
    state: TabState


class MainWindow(tk.Tk):
    """Top-level urllib_gui application window."""

    def __init__(self, *, initial_url: str | None = None, theme: str | None = None) -> None:
        super().__init__()
        self.title("urllib_gui")
        self.geometry("1080x720")
        self.app_config = AppConfig()
        self.urllib_client = UrllibClient()
        self.history_store = HistoryStore()
        self.bookmark_store = BookmarkStore()
        self.saved_request_store = SavedRequestStore()
        self.renderers = built_in_renderers()
        self.tabs_by_id: dict[str, BrowserTab] = {}
        self.fetch_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="urllib_gui-fetch")
        self.spinner_after_id: str | None = None
        self.spinner_frame = 0
        self.status_var = tk.StringVar(value="Ready")
        self.url_var = tk.StringVar()
        self.view_mode_var = tk.StringVar(value="Rendered")
        effective_engine = self.app_config.default_engine
        self.engine_var = tk.StringVar(value=effective_engine)
        effective_theme = theme if theme in THEMES else self.app_config.theme
        if effective_theme not in THEMES:
            effective_theme = "light"
        self.theme_var = tk.StringVar(value=effective_theme)
        self.build_menu()
        self.build_toolbar()
        self.build_drawer()
        self.build_notebook()
        self.build_statusbar()
        self.bind_shortcuts()
        self.apply_theme()
        first_tab = self.new_tab()
        self.notebook.select(first_tab.frame)  # type: ignore[no-untyped-call]
        self.sync_toolbar_from_tab(first_tab)
        if initial_url:
            self.url_var.set(initial_url)
            self.open_url(initial_url)
        else:
            self.show_welcome(first_tab)

    @property
    def current_tab(self) -> BrowserTab:
        """Return the currently selected browser tab."""
        tab_id = cast(str, self.notebook.select())  # type: ignore[no-untyped-call]
        return self.tabs_by_id[tab_id]

    def destroy(self) -> None:
        """Shut down the fetch executor before tearing down the window."""
        # In-flight urllib.request calls cannot be cancelled mid-socket; cancel_futures
        # only drops queued work. Workers may keep running until the socket times out
        # or completes, but their results are ignored via the per-tab fetch_seq guard.
        # TODO: a real cancellation path would require switching to a custom opener
        # that exposes the underlying socket so we can shutdown(SHUT_RDWR) it.
        with suppress(RuntimeError):
            self.fetch_executor.shutdown(wait=False, cancel_futures=True)
        super().destroy()

    def build_menu(self) -> None:
        """Build the application menu bar."""
        menu_bar = tk.Menu(self)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New Tab", accelerator="Ctrl+T", command=self.new_tab)
        file_menu.add_command(label="Open URL", accelerator="Ctrl+L", command=self.focus_url_entry)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save Response Body As...", command=self.save_response_body)
        file_menu.add_command(label="Save Rendered Text As...", command=self.save_rendered_text)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", accelerator="Ctrl+W", command=self.close_current_tab)
        file_menu.add_command(label="Quit", command=self.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=False)
        edit_menu.add_command(label="Find…", accelerator="Ctrl+F", command=self.show_find_bar)
        edit_menu.add_separator()
        edit_menu.add_command(label="Encoding Override…", command=self.show_encoding_override)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menu_bar, tearoff=False)
        view_menu.add_command(label="Reload", accelerator="Ctrl+R", command=self.reload_current_tab)
        view_menu.add_command(label="Toggle Request Options", command=self._toggle_drawer)
        view_menu.add_separator()
        for mode in VIEW_MODES:
            view_menu.add_radiobutton(
                label=f"View {mode}", value=mode, variable=self.view_mode_var, command=self.refresh_view
            )
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", accelerator="Ctrl++", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", accelerator="Ctrl+-", command=self.zoom_out)
        view_menu.add_command(label="Reset Zoom", accelerator="Ctrl+0", command=self.zoom_reset)
        view_menu.add_separator()
        theme_menu = tk.Menu(view_menu, tearoff=False)
        for theme_name in THEMES:
            theme_menu.add_radiobutton(
                label=theme_name.title(), value=theme_name, variable=self.theme_var, command=self._on_theme_changed
            )
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        view_menu.add_command(label="Preferences…", command=self.show_preferences)
        menu_bar.add_cascade(label="View", menu=view_menu)

        history_menu = tk.Menu(menu_bar, tearoff=False)
        history_menu.add_command(label="Back", accelerator="Alt+Left", command=self.go_back)
        history_menu.add_command(label="Forward", accelerator="Alt+Right", command=self.go_forward)
        history_menu.add_separator()
        history_menu.add_command(label="Show History…", command=self.show_history_window)
        history_menu.add_command(label="Clear History", command=self.clear_history)
        menu_bar.add_cascade(label="History", menu=history_menu)

        bookmarks_menu = tk.Menu(menu_bar, tearoff=False)
        bookmarks_menu.add_command(label="Bookmark This Page", accelerator="Ctrl+D", command=self.bookmark_current_page)
        bookmarks_menu.add_command(label="Show Bookmarks…", command=self.show_bookmarks_window)
        bookmarks_menu.add_separator()
        bookmarks_menu.add_command(label="Import Bookmarks…", command=self._import_bookmarks)
        bookmarks_menu.add_command(label="Export Bookmarks…", command=self._export_bookmarks)
        menu_bar.add_cascade(label="Bookmarks", menu=bookmarks_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=False)
        tools_menu.add_command(label="Copy as urllib Code", command=self.copy_request_as_urllib)
        tools_menu.add_command(label="Copy as curl", command=self.copy_request_as_curl)
        tools_menu.add_separator()
        tools_menu.add_command(label="Request Scratchpad…", command=self.show_scratchpad)
        tools_menu.add_command(label="Save Request to Scratchpad…", command=self.save_request_to_scratchpad)
        tools_menu.add_separator()
        tools_menu.add_command(label="Save Request to File…", command=self.save_request_to_file)
        tools_menu.add_command(label="Open Request from File…", command=self.open_request_from_file)
        tools_menu.add_separator()
        tools_menu.add_command(label="Cookie Jar…", command=self.show_cookie_jar)
        tools_menu.add_separator()
        tools_menu.add_command(label="Open Current Page Externally", command=self.open_current_page_externally)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menu_bar, tearoff=False)
        help_menu.add_command(
            label="About urllib_gui",
            command=lambda: messagebox.showinfo(
                "About urllib_gui",
                "urllib_gui\n\nA tiny urllib-shaped text browser for Tkinter.",
            ),
        )
        menu_bar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menu_bar)

    def build_toolbar(self) -> None:
        """Build the main navigation toolbar."""
        toolbar = ttk.Frame(self, padding=(8, 8))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Back", command=self.go_back).pack(side="left")
        ttk.Button(toolbar, text="Forward", command=self.go_forward).pack(side="left", padx=(4, 0))
        ttk.Button(toolbar, text="Reload", command=self.reload_current_tab).pack(side="left", padx=(4, 8))
        self.method_label_var = tk.StringVar(value="GET")
        self.method_indicator = ttk.Label(
            toolbar, textvariable=self.method_label_var, width=7, anchor="center", foreground="#666666"
        )
        self.method_indicator.pack(side="left")
        self.url_entry = ttk.Entry(toolbar, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _event: self.open_url(self.url_var.get()))
        ttk.Button(toolbar, text="Go", command=lambda: self.open_url(self.url_var.get())).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Bookmark", command=self.bookmark_current_page).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Copy urllib", command=self.copy_request_as_urllib).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Copy curl", command=self.copy_request_as_curl).pack(side="left", padx=(4, 0))
        self.view_combo = ttk.Combobox(
            toolbar, values=VIEW_MODES, state="readonly", textvariable=self.view_mode_var, width=10
        )
        self.view_combo.pack(side="left", padx=(8, 0))
        self.view_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_view())
        engine_names = list(self.renderers.keys())
        self.engine_combo = ttk.Combobox(
            toolbar, values=engine_names, state="readonly", textvariable=self.engine_var, width=18
        )
        self.engine_combo.pack(side="left", padx=(8, 0))
        self.engine_combo.bind("<<ComboboxSelected>>", lambda _event: self.change_engine())

    def build_drawer(self) -> None:
        """Build the collapsible expanded request drawer."""
        self.request_drawer = RequestDrawer(self, on_submit=self._on_drawer_submit)
        self.request_drawer.pack(fill="x")

    def _on_drawer_submit(self, spec: RequestSpec) -> None:
        """Handle Send Request from the drawer."""
        tab = self.current_tab
        self.url_var.set(spec.url)
        method = spec.method.upper()
        self.method_label_var.set(method)
        self.method_indicator.configure(foreground="#cc3300" if method != "GET" else "#666666")
        self.load_request(tab, spec, push_history=True)

    def build_notebook(self) -> None:
        """Build the tabbed content area."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", lambda _event: self.on_tab_changed())

    def build_statusbar(self) -> None:
        """Build the status bar."""
        status_bar = ttk.Frame(self, padding=(0, 0))
        status_bar.pack(fill="x", side="bottom")
        status = ttk.Label(status_bar, textvariable=self.status_var, anchor="w", padding=(8, 4))
        status.pack(side="left", fill="x", expand=True)
        self.progress = ttk.Progressbar(status_bar, mode="indeterminate", length=120)
        self.progress.pack(side="right", padx=(0, 8), pady=4)

    def bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts for common actions."""
        self.bind("<Control-l>", lambda _event: self.focus_url_entry())
        self.bind("<Control-t>", lambda _event: self.new_tab())
        self.bind("<Control-w>", lambda _event: self.close_current_tab())
        self.bind("<Control-r>", lambda _event: self.reload_current_tab())
        self.bind("<Alt-Left>", lambda _event: self.go_back())
        self.bind("<Alt-Right>", lambda _event: self.go_forward())
        self.bind("<Control-d>", lambda _event: self.bookmark_current_page())
        self.bind("<Control-s>", lambda _event: self.save_response_body())
        self.bind("<Control-f>", lambda _event: self.show_find_bar())
        self.bind("<Control-equal>", lambda _event: self.zoom_in())
        self.bind("<Control-plus>", lambda _event: self.zoom_in())
        self.bind("<Control-minus>", lambda _event: self.zoom_out())
        self.bind("<Control-0>", lambda _event: self.zoom_reset())

    def apply_theme(self) -> None:
        """Apply the active color theme to the window."""
        colors = THEMES[self.theme_var.get()]
        self.configure(background=colors["background"])
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        for tab in self.tabs_by_id.values():
            tab.viewer.apply_theme(
                background=colors["background"],
                foreground=colors["foreground"],
                link_foreground=colors["link"],
                visited_foreground=colors.get("visited", "#800080"),
            )

    def _on_theme_changed(self) -> None:
        """Persist theme change and re-apply."""
        self.app_config.theme = self.theme_var.get()
        self.app_config.save()
        self.apply_theme()

    def new_tab(self, initial_request: RequestSpec | None = None) -> BrowserTab:
        """Create a new browser tab."""
        state = TabState(request=initial_request or RequestSpec(url=""))
        frame = ttk.Frame(self.notebook)
        frame.pack(fill="both", expand=True)
        viewer = HypertextViewer(frame, open_link_callback=self.open_link, status_callback=self.set_hover_status)
        viewer.pack(fill="both", expand=True)
        colors = THEMES[self.theme_var.get()]
        viewer.apply_theme(
            background=colors["background"],
            foreground=colors["foreground"],
            link_foreground=colors["link"],
            visited_foreground=colors.get("visited", "#800080"),
        )
        browser_tab = BrowserTab(frame=frame, viewer=viewer, state=state)
        self.notebook.add(frame, text="New Tab")
        self.tabs_by_id[str(frame)] = browser_tab
        self.notebook.select(frame)  # type: ignore[no-untyped-call]
        self.sync_toolbar_from_tab(browser_tab)
        return browser_tab

    def close_current_tab(self) -> None:
        """Close the current tab or quit when it is the last one."""
        if len(self.tabs_by_id) == 1:
            self.destroy()
            return
        tab_id = cast(str, self.notebook.select())  # type: ignore[no-untyped-call]
        self.notebook.forget(tab_id)
        self.tabs_by_id.pop(tab_id, None)
        self.on_tab_changed()

    def focus_url_entry(self) -> None:
        """Focus and select the URL entry."""
        self.url_entry.focus_set()
        self.url_entry.selection_range(0, "end")

    def open_url(self, value: str, *, new_tab: bool = False, push_history: bool = True) -> None:
        """Open a URL in the current tab or a new tab."""
        normalized = normalize_url(value)
        if not normalized:
            self.status_var.set("Enter a URL to fetch.")
            return
        parsed = urlparse(normalized)
        if parsed.scheme and parsed.scheme not in {"http", "https", "file"}:
            messagebox.showwarning("Unsupported scheme", f"Unsupported URL scheme: {parsed.scheme}")
            return
        tab = self.new_tab(RequestSpec(url=normalized)) if new_tab else self.current_tab
        if self.request_drawer._visible:
            self.request_drawer.url_var.set(normalized)
            request = self.request_drawer.build_request_spec()
        else:
            request = RequestSpec(url=normalized)
        self.load_request(tab, request, push_history=push_history)

    def open_link(self, href: str, new_tab: bool) -> None:
        """Open a rendered hyperlink and mark it visited in all tabs."""
        for bt in self.tabs_by_id.values():
            bt.viewer.mark_visited(href)
        self.open_url(href, new_tab=new_tab)

    def reload_current_tab(self) -> None:
        """Reload the current tab."""
        tab = self.current_tab
        self.load_request(tab, tab.state.request, push_history=False)

    def go_back(self) -> None:
        """Navigate to the previous request in tab history."""
        tab = self.current_tab
        if tab.state.history_index <= 0:
            return
        tab.state.history_index -= 1
        request = tab.state.local_history[tab.state.history_index]
        self.load_request(tab, request, push_history=False)

    def go_forward(self) -> None:
        """Navigate to the next request in tab history."""
        tab = self.current_tab
        if tab.state.history_index >= len(tab.state.local_history) - 1:
            return
        tab.state.history_index += 1
        request = tab.state.local_history[tab.state.history_index]
        self.load_request(tab, request, push_history=False)

    def change_engine(self) -> None:
        """Switch the active render engine."""
        tab = self.current_tab
        tab.state.render_engine_name = self.engine_var.get()
        tab.state.engine_locked = True
        self.render_current_response(tab)
        self.display_tab(tab)

    def refresh_view(self) -> None:
        """Refresh the visible representation of the current tab."""
        self.display_tab(self.current_tab)

    def bookmark_current_page(self) -> None:
        """Save the current page as a bookmark."""
        tab = self.current_tab
        response = tab.state.response
        url = response.final_url if response is not None else tab.state.request.normalized_url()
        bookmark = make_bookmark(tab.state.title, url)
        self.bookmark_store.add(bookmark)
        self.status_var.set(f"Bookmarked {bookmark.url}")

    def copy_request_as_urllib(self) -> None:
        """Copy the current request as urllib code."""
        code = generate_urllib_code(self.current_tab.state.request)
        self.clipboard_clear()
        self.clipboard_append(code)
        self.status_var.set("Copied request as urllib code.")

    def copy_request_as_curl(self) -> None:
        """Copy the current request as a curl command."""
        cmd = generate_curl_command(self.current_tab.state.request)
        self.clipboard_clear()
        self.clipboard_append(cmd)
        self.status_var.set("Copied request as curl command.")

    def show_cookie_jar(self) -> None:
        """Open the cookie jar inspection dialog."""
        CookieJarDialog(
            self,
            self.urllib_client.cookie_jar,
            on_changed=lambda: self.status_var.set("Cookie jar updated."),
        )

    def show_scratchpad(self) -> None:
        """Open the request scratchpad dialog."""
        tab = self.current_tab

        def load_spec(spec: RequestSpec) -> None:
            self.url_var.set(spec.url)
            if self.request_drawer._visible:
                self.request_drawer.populate_from_spec(spec)
            self.load_request(tab, spec, push_history=True)

        ScratchpadDialog(
            self,
            self.saved_request_store,
            on_load=load_spec,
            current_spec=tab.state.request if tab.state.request.url else None,
        )

    def save_request_to_scratchpad(self) -> None:
        """Save the current request to the scratchpad with a name prompt."""
        spec = self.current_tab.state.request
        if not spec.url:
            messagebox.showinfo("Save Request", "No active request to save.", parent=self)
            return
        name = simpledialog.askstring("Save to Scratchpad", "Name for this request:", parent=self)
        if not name or not name.strip():
            return
        self.saved_request_store.save(SavedRequest(name=name.strip(), spec=spec))
        self.status_var.set(f"Saved request as '{name.strip()}'.")

    def save_request_to_file(self) -> None:
        """Export the current request spec to a JSON file."""

        spec = self.current_tab.state.request
        if not spec.url:
            messagebox.showinfo("Save Request", "No active request to save.", parent=self)
            return
        target = filedialog.asksaveasfilename(
            parent=self,
            title="Save Request as JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not target:
            return
        Path(target).write_text(spec_to_json(spec), encoding="utf-8")
        self.status_var.set(f"Request saved to {target}")

    def open_request_from_file(self) -> None:
        """Load a previously exported request spec from a JSON file."""
        filename = filedialog.askopenfilename(
            parent=self,
            title="Open Request JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            text = Path(filename).read_text(encoding="utf-8")
            spec = json_to_spec(text)
        except (OSError, TypeError, ValueError, KeyError) as exc:
            messagebox.showerror("Open Request", f"Could not read request file:\n{exc}", parent=self)
            return
        tab = self.current_tab
        self.url_var.set(spec.url)
        if self.request_drawer._visible:
            self.request_drawer.populate_from_spec(spec)
        self.load_request(tab, spec, push_history=True)
        self.status_var.set(f"Loaded request from {filename}")

    def open_current_page_externally(self) -> None:
        """Open the current page in the default browser."""
        tab = self.current_tab
        if tab.state.response is None:
            return
        webbrowser.open(tab.state.response.final_url)

    def save_response_body(self) -> None:
        """Save the current response body to disk."""
        tab = self.current_tab
        response = tab.state.response
        if response is None:
            return
        target = filedialog.asksaveasfilename(parent=self, title="Save response body")
        if not target:
            return
        Path(target).write_bytes(response.body)
        self.status_var.set(f"Saved response body to {target}")

    def save_rendered_text(self) -> None:
        """Save the rendered document text to disk."""
        tab = self.current_tab
        document = tab.state.rendered
        if document is None:
            return
        target = filedialog.asksaveasfilename(parent=self, title="Save rendered text")
        if not target:
            return
        Path(target).write_text(document.text, encoding="utf-8")
        self.status_var.set(f"Saved rendered text to {target}")

    def open_file(self) -> None:
        """Open a local file in the browser."""
        filename = filedialog.askopenfilename(parent=self, title="Open local file")
        if not filename:
            return
        self.open_url(Path(filename).resolve().as_uri())

    def clear_history(self) -> None:
        """Clear the stored browsing history."""
        if not messagebox.askyesno("Clear history", "Delete all stored history entries?"):
            return
        self.history_store.clear()
        self.status_var.set("History cleared.")

    def _open_url_positional(self, url: str, new_tab: bool) -> None:
        """Adapter for dialog on_open callbacks that pass new_tab positionally."""
        self.open_url(url, new_tab=new_tab)

    def show_history_window(self) -> None:
        """Show the rich browsing history dialog."""
        HistoryDialog(
            self,
            self.history_store,
            on_open=self._open_url_positional,
            on_cleared=lambda: self.status_var.set("History cleared."),
        )

    def show_bookmarks_window(self) -> None:
        """Show the rich bookmarks management dialog."""
        BookmarksDialog(
            self,
            self.bookmark_store,
            on_open=self._open_url_positional,
        )

    def _import_bookmarks(self) -> None:
        """Open the bookmarks dialog focused on import."""
        dlg = BookmarksDialog(self, self.bookmark_store, on_open=self._open_url_positional)
        dlg._import()

    def _export_bookmarks(self) -> None:
        """Open the bookmarks dialog focused on export."""
        dlg = BookmarksDialog(self, self.bookmark_store, on_open=self._open_url_positional)
        dlg._export()

    def show_preferences(self) -> None:
        """Open the preferences dialog."""
        PreferencesDialog(self, self.app_config, on_apply=self._on_prefs_applied)

    def _on_prefs_applied(self, config: AppConfig) -> None:
        """React to preferences being saved — update live UI state."""
        new_theme = config.theme
        if new_theme in THEMES and new_theme != self.theme_var.get():
            self.theme_var.set(new_theme)
            self.apply_theme()
        new_engine = config.default_engine
        if new_engine in self.renderers:
            self.engine_var.set(new_engine)
        self.status_var.set("Preferences saved.")

    def load_request(self, tab: BrowserTab, request: RequestSpec, *, push_history: bool) -> None:
        """Load a request into a tab off the UI thread."""
        tab.state.request = request
        tab.state.fetch_seq += 1
        seq = tab.state.fetch_seq
        tab.state.loading = True
        if push_history:
            if tab.state.history_index < len(tab.state.local_history) - 1:
                tab.state.local_history = tab.state.local_history[: tab.state.history_index + 1]
            tab.state.local_history.append(request)
            tab.state.history_index = len(tab.state.local_history) - 1
        self.begin_loading_indicator(request.normalized_url())
        client = self.urllib_client
        started = time.perf_counter()
        future = self.fetch_executor.submit(client.fetch, request)

        # Marshal completion back to the Tk thread; the seq guard ignores stale results
        # from navigations the user has since superseded.
        def bounce(fut: Future[ResponseRecord]) -> None:
            with suppress(RuntimeError, tk.TclError):
                self.after(0, self.on_fetch_complete, tab, seq, request, push_history, started, fut)

        future.add_done_callback(bounce)

    def on_fetch_complete(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        tab: BrowserTab,
        seq: int,
        request: RequestSpec,
        push_history: bool,  # pylint: disable=unused-argument
        started: float,
        future: Future[ResponseRecord],
    ) -> None:
        """Apply a fetch result to a tab, ignoring stale completions."""
        if seq != tab.state.fetch_seq:
            # User started a newer navigation in this tab; drop the stale result.
            # NOTE: the worker thread cannot be cancelled mid-socket, so we just discard.
            return
        if str(tab.frame) not in self.tabs_by_id:
            # Tab was closed while the fetch was in flight.
            return
        tab.state.loading = False
        self.end_loading_indicator()
        try:
            response = future.result()
        except Exception as error:  # pylint: disable=broad-except
            elapsed = time.perf_counter() - started
            response = ResponseRecord(
                final_url=request.normalized_url(),
                status=None,
                reason=None,
                headers=[],
                body=b"",
                elapsed_seconds=elapsed,
                encoding=None,
                content_type=None,
                error=f"{type(error).__name__}: {error}",
            )
        tab.state.response = response
        if response.error:
            tab.state.source_text = response.error
            tab.state.rendered = self.build_error_document(request, response.error)
        else:
            if not tab.state.engine_locked or tab.state.render_engine_name not in self.renderers:
                tab.state.render_engine_name = choose_default_engine_name(response)
            source_renderer = self.renderers["html_source"]
            tab.state.source_text = source_renderer.render(
                response.body,
                base_url=response.final_url,
                content_type=response.content_type,
                encoding=response.encoding,
            ).text
            self.render_current_response(tab)
            entry = history_entry_from_response(request, response, title=tab.state.title)
            self.history_store.add_entry(entry)
        if tab is self.current_tab:
            final = response.final_url if response.final_url else request.normalized_url()
            self.url_var.set(final)
            if self.request_drawer._visible:
                self.request_drawer.url_var.set(final)
        self.display_tab(tab)
        status_code = response.status if response.status is not None else "ERR"
        content_type = response.content_type or "unknown"
        self.status_var.set(f"{status_code} {content_type} in {response.elapsed_seconds:.2f}s")

    def begin_loading_indicator(self, url: str) -> None:
        """Start the indeterminate progressbar and an animated status message."""
        try:
            self.progress.start(80)
        except tk.TclError:
            return
        self.spinner_frame = 0
        self.tick_spinner(url)

    def tick_spinner(self, url: str) -> None:
        frames = ("   ", ".  ", ".. ", "...")
        if not any(t.state.loading for t in self.tabs_by_id.values()):
            return
        self.status_var.set(f"Loading {url} {frames[self.spinner_frame % len(frames)]}")
        self.spinner_frame += 1
        self.spinner_after_id = self.after(200, self.tick_spinner, url)

    def end_loading_indicator(self) -> None:
        """Stop the progress animation if no tab is still loading."""
        if any(t.state.loading for t in self.tabs_by_id.values()):
            return
        with suppress(tk.TclError):
            self.progress.stop()
        if self.spinner_after_id is not None:
            with suppress(tk.TclError):
                self.after_cancel(self.spinner_after_id)
            self.spinner_after_id = None

    def build_error_document(self, request: RequestSpec, error_text: str) -> RenderedDocument:
        """Build a rendered document for request errors."""
        text = "\n".join(
            [
                "Request failed",
                "",
                f"URL: {request.normalized_url()}",
                "",
                f"Error: {error_text}",
            ]
        )
        return RenderedDocument(title="Request failed", text=text)

    def render_current_response(self, tab: BrowserTab) -> None:
        """Render the current response for a tab."""
        response = tab.state.response
        if response is None:
            return
        renderer = self.renderers[tab.state.render_engine_name]
        tab.state.rendered = renderer.render(
            response.body,
            base_url=response.final_url,
            content_type=response.content_type,
            encoding=response.encoding,
        )
        tab.state.title = choose_tab_title(tab.state.request, response, tab.state.rendered)
        tab_title = tab.state.title[:24] if tab.state.title else "Untitled"
        self.notebook.tab(tab.frame, text=tab_title)  # type: ignore[no-untyped-call]
        self.engine_var.set(tab.state.render_engine_name)

    def display_tab(self, tab: BrowserTab) -> None:
        """Display the current tab in the selected view mode."""
        mode = self.view_mode_var.get()
        if mode == "Rendered":
            if tab.state.rendered is not None:
                tab.viewer.set_document(tab.state.rendered)
            else:
                tab.viewer.set_plain_text("(nothing rendered yet)")
        elif mode == "Source":
            tab.viewer.set_plain_text(tab.state.source_text or "(empty response body)")
        elif mode == "Headers":
            tab.viewer.set_plain_text(self.format_headers_view(tab.state.response))
        else:
            tab.viewer.set_plain_text(format_request_preview(tab.state.request))

    def format_headers_view(self, response: ResponseRecord | None) -> str:
        """Format response headers for display."""
        if response is None:
            return "(no response)"
        status_line = f"Status: {response.status or '(none)'} {response.reason or ''}".rstrip()
        return "\n".join([status_line, "", response.headers_text()])

    def show_welcome(self, tab: BrowserTab) -> None:
        """Show the welcome text in a new tab."""
        welcome_text = "\n".join(
            [
                "urllib_gui",
                "",
                "A tiny urllib-shaped text browser for Tkinter.",
                "",
                "Enter a URL above to fetch a page, inspect headers, view source,",
                "follow text links, and save bookmarks.",
            ]
        )
        tab.viewer.set_plain_text(welcome_text)

    def on_tab_changed(self) -> None:
        """Update UI state after the selected tab changes."""
        if not self.tabs_by_id:
            return
        tab = self.current_tab
        self.sync_toolbar_from_tab(tab)
        self.display_tab(tab)

    def sync_toolbar_from_tab(self, tab: BrowserTab) -> None:
        """Sync toolbar controls from tab state."""
        self.url_var.set(tab.state.request.normalized_url())
        self.engine_var.set(tab.state.render_engine_name)
        method = tab.state.request.method.upper()
        self.method_label_var.set(method)
        self.method_indicator.configure(foreground="#cc3300" if method != "GET" else "#666666")
        if self.request_drawer._visible:
            self.request_drawer.populate_from_spec(tab.state.request)

    def _toggle_drawer(self) -> None:
        """Toggle the request options drawer."""
        if self.request_drawer._visible:
            self.request_drawer.hide()
        else:
            self.request_drawer.url_var.set(self.url_var.get())
            self.request_drawer.show()

    def set_hover_status(self, href: str | None) -> None:
        """Update the status bar while hovering links."""
        if href:
            self.status_var.set(href)
        elif self.current_tab.state.response is not None:
            response = self.current_tab.state.response
            status_code = response.status if response.status is not None else "ERR"
            content_type = response.content_type or "unknown"
            self.status_var.set(f"{status_code} {content_type} in {response.elapsed_seconds:.2f}s")

    # ------------------------------------------------------------------ zoom

    def zoom_in(self) -> None:
        """Increase font size in the current viewer."""
        self.current_tab.viewer.zoom_in()
        self.status_var.set(f"Zoom: {self.current_tab.viewer.current_font_size}pt")

    def zoom_out(self) -> None:
        """Decrease font size in the current viewer."""
        self.current_tab.viewer.zoom_out()
        self.status_var.set(f"Zoom: {self.current_tab.viewer.current_font_size}pt")

    def zoom_reset(self) -> None:
        """Reset font size in the current viewer."""
        self.current_tab.viewer.zoom_reset()
        self.status_var.set(f"Zoom: {self.current_tab.viewer.current_font_size}pt")

    # ------------------------------------------------------------------ find

    def show_find_bar(self) -> None:
        """Show the find-in-page bar on the current viewer."""
        self.current_tab.viewer.show_find_bar()

    # ------------------------------------------------------------------ encoding

    def show_encoding_override(self) -> None:
        """Prompt the user for an encoding and re-render the current response."""
        tab = self.current_tab
        if tab.state.response is None:
            self.status_var.set("No response to re-decode.")
            return
        current = tab.state.response.encoding or "utf-8"
        enc = simpledialog.askstring(
            "Encoding Override",
            f"Enter encoding (current: {current}):",
            initialvalue=current,
            parent=self,
        )
        if not enc or not enc.strip():
            return
        enc = enc.strip()
        try:
            b"test".decode(enc)
        except LookupError:
            messagebox.showerror("Encoding Override", f"Unknown encoding: {enc}", parent=self)
            return
        tab.state.response = replace(tab.state.response, encoding=enc)
        self.render_current_response(tab)
        self.display_tab(tab)
        self.status_var.set(f"Re-rendered with encoding: {enc}")
