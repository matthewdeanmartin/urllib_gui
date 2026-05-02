"""Main Tkinter window for urllib_gui."""

from __future__ import annotations

import tkinter as tk
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import cast
from urllib.parse import urlparse

from urllib_gui.client import UrllibClient
from urllib_gui.export import generate_urllib_code
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
from urllib_gui.storage import BookmarkStore, HistoryStore
from urllib_gui.ui import HypertextViewer

VIEW_MODES = ("Rendered", "Source", "Headers", "Request")

THEMES = {
    "light": {
        "background": "#ffffff",
        "foreground": "#111111",
        "link": "#005cc5",
    },
    "dark": {
        "background": "#1e1e1e",
        "foreground": "#dddddd",
        "link": "#6ab0ff",
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

    def __init__(self, *, initial_url: str | None = None, theme: str = "light") -> None:
        super().__init__()
        self.title("urllib_gui")
        self.geometry("1080x720")
        self.urllib_client = UrllibClient()
        self.history_store = HistoryStore()
        self.bookmark_store = BookmarkStore()
        self.renderers = built_in_renderers()
        self.tabs_by_id: dict[str, BrowserTab] = {}
        self.status_var = tk.StringVar(value="Ready")
        self.url_var = tk.StringVar()
        self.view_mode_var = tk.StringVar(value="Rendered")
        self.engine_var = tk.StringVar(value="stdlib_html_links")
        self.theme_var = tk.StringVar(value=theme if theme in THEMES else "light")
        self._build_menu()
        self._build_toolbar()
        self._build_notebook()
        self._build_statusbar()
        self._bind_shortcuts()
        self._apply_theme()
        first_tab = self.new_tab()
        self.notebook.select(first_tab.frame)  # type: ignore[no-untyped-call]
        self._sync_toolbar_from_tab(first_tab)
        if initial_url:
            self.url_var.set(initial_url)
            self.open_url(initial_url)
        else:
            self._show_welcome(first_tab)

    @property
    def current_tab(self) -> BrowserTab:
        """Return the currently selected browser tab."""
        tab_id = cast(str, self.notebook.select())  # type: ignore[no-untyped-call]
        return self.tabs_by_id[tab_id]

    def _build_menu(self) -> None:
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

        view_menu = tk.Menu(menu_bar, tearoff=False)
        view_menu.add_command(label="Reload", accelerator="Ctrl+R", command=self.reload_current_tab)
        view_menu.add_separator()
        for mode in VIEW_MODES:
            view_menu.add_radiobutton(
                label=f"View {mode}", value=mode, variable=self.view_mode_var, command=self.refresh_view
            )
        theme_menu = tk.Menu(view_menu, tearoff=False)
        for theme_name in THEMES:
            theme_menu.add_radiobutton(
                label=theme_name.title(), value=theme_name, variable=self.theme_var, command=self._apply_theme
            )
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        menu_bar.add_cascade(label="View", menu=view_menu)

        history_menu = tk.Menu(menu_bar, tearoff=False)
        history_menu.add_command(label="Back", accelerator="Alt+Left", command=self.go_back)
        history_menu.add_command(label="Forward", accelerator="Alt+Right", command=self.go_forward)
        history_menu.add_command(label="Show History", command=self.show_history_window)
        history_menu.add_command(label="Clear History", command=self.clear_history)
        menu_bar.add_cascade(label="History", menu=history_menu)

        bookmarks_menu = tk.Menu(menu_bar, tearoff=False)
        bookmarks_menu.add_command(label="Bookmark This Page", accelerator="Ctrl+D", command=self.bookmark_current_page)
        bookmarks_menu.add_command(label="Show Bookmarks", command=self.show_bookmarks_window)
        menu_bar.add_cascade(label="Bookmarks", menu=bookmarks_menu)

        tools_menu = tk.Menu(menu_bar, tearoff=False)
        tools_menu.add_command(label="Copy as urllib Code", command=self.copy_request_as_urllib)
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

    def _build_toolbar(self) -> None:
        """Build the main navigation toolbar."""
        toolbar = ttk.Frame(self, padding=(8, 8))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Back", command=self.go_back).pack(side="left")
        ttk.Button(toolbar, text="Forward", command=self.go_forward).pack(side="left", padx=(4, 0))
        ttk.Button(toolbar, text="Reload", command=self.reload_current_tab).pack(side="left", padx=(4, 8))
        self.url_entry = ttk.Entry(toolbar, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _event: self.open_url(self.url_var.get()))
        ttk.Button(toolbar, text="Go", command=lambda: self.open_url(self.url_var.get())).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Bookmark", command=self.bookmark_current_page).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Copy urllib", command=self.copy_request_as_urllib).pack(side="left", padx=(8, 0))
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

    def _build_notebook(self) -> None:
        """Build the tabbed content area."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", lambda _event: self._on_tab_changed())

    def _build_statusbar(self) -> None:
        """Build the status bar."""
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(8, 4))
        status.pack(fill="x", side="bottom")

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts for common actions."""
        self.bind("<Control-l>", lambda _event: self.focus_url_entry())
        self.bind("<Control-t>", lambda _event: self.new_tab())
        self.bind("<Control-w>", lambda _event: self.close_current_tab())
        self.bind("<Control-r>", lambda _event: self.reload_current_tab())
        self.bind("<Alt-Left>", lambda _event: self.go_back())
        self.bind("<Alt-Right>", lambda _event: self.go_forward())
        self.bind("<Control-d>", lambda _event: self.bookmark_current_page())
        self.bind("<Control-s>", lambda _event: self.save_response_body())

    def _apply_theme(self) -> None:
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
            )

    def new_tab(self, initial_request: RequestSpec | None = None) -> BrowserTab:
        """Create a new browser tab."""
        state = TabState(request=initial_request or RequestSpec(url=""))
        frame = ttk.Frame(self.notebook)
        frame.pack(fill="both", expand=True)
        viewer = HypertextViewer(frame, open_link_callback=self.open_link, status_callback=self._set_hover_status)
        viewer.pack(fill="both", expand=True)
        viewer.apply_theme(
            background=THEMES[self.theme_var.get()]["background"],
            foreground=THEMES[self.theme_var.get()]["foreground"],
            link_foreground=THEMES[self.theme_var.get()]["link"],
        )
        browser_tab = BrowserTab(frame=frame, viewer=viewer, state=state)
        self.notebook.add(frame, text="New Tab")
        self.tabs_by_id[str(frame)] = browser_tab
        self.notebook.select(frame)  # type: ignore[no-untyped-call]
        self._sync_toolbar_from_tab(browser_tab)
        return browser_tab

    def close_current_tab(self) -> None:
        """Close the current tab or quit when it is the last one."""
        if len(self.tabs_by_id) == 1:
            self.destroy()
            return
        tab_id = cast(str, self.notebook.select())  # type: ignore[no-untyped-call]
        self.notebook.forget(tab_id)
        self.tabs_by_id.pop(tab_id, None)
        self._on_tab_changed()

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
        request = RequestSpec(url=normalized)
        self._load_request(tab, request, push_history=push_history)

    def open_link(self, href: str, new_tab: bool) -> None:
        """Open a rendered hyperlink."""
        self.open_url(href, new_tab=new_tab)

    def reload_current_tab(self) -> None:
        """Reload the current tab."""
        tab = self.current_tab
        self._load_request(tab, tab.state.request, push_history=False)

    def go_back(self) -> None:
        """Navigate to the previous request in tab history."""
        tab = self.current_tab
        if tab.state.history_index <= 0:
            return
        tab.state.history_index -= 1
        request = tab.state.local_history[tab.state.history_index]
        self._load_request(tab, request, push_history=False)

    def go_forward(self) -> None:
        """Navigate to the next request in tab history."""
        tab = self.current_tab
        if tab.state.history_index >= len(tab.state.local_history) - 1:
            return
        tab.state.history_index += 1
        request = tab.state.local_history[tab.state.history_index]
        self._load_request(tab, request, push_history=False)

    def change_engine(self) -> None:
        """Switch the active render engine."""
        tab = self.current_tab
        tab.state.render_engine_name = self.engine_var.get()
        self._render_current_response(tab)

    def refresh_view(self) -> None:
        """Refresh the visible representation of the current tab."""
        self._display_tab(self.current_tab)

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

    def show_history_window(self) -> None:
        """Show the browsing history window."""
        self._show_url_list_window("History", [entry.url for entry in self.history_store.list_entries()])

    def show_bookmarks_window(self) -> None:
        """Show the bookmarks window."""
        self._show_url_list_window("Bookmarks", [bookmark.url for bookmark in self.bookmark_store.list_bookmarks()])

    def _show_url_list_window(self, title: str, urls: list[str]) -> None:
        """Show a searchable list of URLs."""
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("640x360")
        search_var = tk.StringVar()
        ttk.Label(window, text="Search").pack(anchor="w", padx=8, pady=(8, 0))
        search_entry = ttk.Entry(window, textvariable=search_var)
        search_entry.pack(fill="x", padx=8, pady=(0, 8))
        listbox = tk.Listbox(window)
        listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        def populate() -> None:
            query = search_var.get().lower()
            listbox.delete(0, "end")
            for url in urls:
                if not query or query in url.lower():
                    listbox.insert("end", url)

        def open_selected(*, in_new_tab: bool) -> None:
            selection = tuple(listbox.curselection())  # type: ignore[no-untyped-call]
            if not selection:
                return
            self.open_url(listbox.get(selection[0]), new_tab=in_new_tab)

        search_var.trace_add("write", lambda *_args: populate())
        listbox.bind("<Double-Button-1>", lambda _event: open_selected(in_new_tab=False))
        button_row = ttk.Frame(window)
        button_row.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(button_row, text="Open", command=lambda: open_selected(in_new_tab=False)).pack(side="left")
        ttk.Button(button_row, text="Open in New Tab", command=lambda: open_selected(in_new_tab=True)).pack(
            side="left", padx=(8, 0)
        )
        populate()

    def _load_request(self, tab: BrowserTab, request: RequestSpec, *, push_history: bool) -> None:
        """Load a request into a tab and update tab state."""
        self.status_var.set(f"Loading {request.normalized_url()} ...")
        self.update_idletasks()
        response = self.urllib_client.fetch(request)
        tab.state.request = request
        tab.state.response = response
        if push_history:
            if tab.state.history_index < len(tab.state.local_history) - 1:
                tab.state.local_history = tab.state.local_history[: tab.state.history_index + 1]
            tab.state.local_history.append(request)
            tab.state.history_index = len(tab.state.local_history) - 1
        if response.error:
            tab.state.source_text = response.error
            tab.state.rendered = self._build_error_document(request, response.error)
        else:
            default_engine = choose_default_engine_name(response)
            if tab.state.render_engine_name not in self.renderers or (
                default_engine == "plain" and tab.state.render_engine_name.startswith("stdlib_html")
            ):
                tab.state.render_engine_name = default_engine
            source_renderer = self.renderers["html_source"]
            tab.state.source_text = source_renderer.render(
                response.body,
                base_url=response.final_url,
                content_type=response.content_type,
                encoding=response.encoding,
            ).text
            self._render_current_response(tab)
            entry = history_entry_from_response(request, response, title=tab.state.title)
            self.history_store.add_entry(entry)
        self.url_var.set(response.final_url if response.final_url else request.normalized_url())
        self._display_tab(tab)
        status_code = response.status if response.status is not None else "ERR"
        content_type = response.content_type or "unknown"
        self.status_var.set(f"{status_code} {content_type} in {response.elapsed_seconds:.2f}s")

    def _build_error_document(self, request: RequestSpec, error_text: str) -> RenderedDocument:
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

    def _render_current_response(self, tab: BrowserTab) -> None:
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

    def _display_tab(self, tab: BrowserTab) -> None:
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
            tab.viewer.set_plain_text(self._format_headers_view(tab.state.response))
        else:
            tab.viewer.set_plain_text(format_request_preview(tab.state.request))

    def _format_headers_view(self, response: ResponseRecord | None) -> str:
        """Format response headers for display."""
        if response is None:
            return "(no response)"
        status_line = f"Status: {response.status or '(none)'} {response.reason or ''}".rstrip()
        return "\n".join([status_line, "", response.headers_text()])

    def _show_welcome(self, tab: BrowserTab) -> None:
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

    def _on_tab_changed(self) -> None:
        """Update UI state after the selected tab changes."""
        if not self.tabs_by_id:
            return
        tab = self.current_tab
        self._sync_toolbar_from_tab(tab)
        self._display_tab(tab)

    def _sync_toolbar_from_tab(self, tab: BrowserTab) -> None:
        """Sync toolbar controls from tab state."""
        self.url_var.set(tab.state.request.normalized_url())
        self.engine_var.set(tab.state.render_engine_name)

    def _set_hover_status(self, href: str | None) -> None:
        """Update the status bar while hovering links."""
        if href:
            self.status_var.set(href)
        elif self.current_tab.state.response is not None:
            response = self.current_tab.state.response
            status_code = response.status if response.status is not None else "ERR"
            content_type = response.content_type or "unknown"
            self.status_var.set(f"{status_code} {content_type} in {response.elapsed_seconds:.2f}s")
