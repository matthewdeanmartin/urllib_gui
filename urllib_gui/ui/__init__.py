"""UI widgets."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from urllib_gui.ui.bookmarks_dialog import BookmarksDialog
    from urllib_gui.ui.cookie_jar import CookieJarDialog
    from urllib_gui.ui.history_dialog import HistoryDialog
    from urllib_gui.ui.preferences import PreferencesDialog
    from urllib_gui.ui.request_panel import RequestDrawer
    from urllib_gui.ui.scratchpad import ScratchpadDialog
    from urllib_gui.ui.viewer import HypertextViewer

__all__ = [
    "BookmarksDialog",
    "CookieJarDialog",
    "HistoryDialog",
    "HypertextViewer",
    "PreferencesDialog",
    "RequestDrawer",
    "ScratchpadDialog",
]


def __getattr__(name: str) -> object:
    if name == "HypertextViewer":
        from urllib_gui.ui.viewer import HypertextViewer

        return HypertextViewer
    if name == "RequestDrawer":
        from urllib_gui.ui.request_panel import RequestDrawer

        return RequestDrawer
    if name == "CookieJarDialog":
        from urllib_gui.ui.cookie_jar import CookieJarDialog

        return CookieJarDialog
    if name == "ScratchpadDialog":
        from urllib_gui.ui.scratchpad import ScratchpadDialog

        return ScratchpadDialog
    if name == "BookmarksDialog":
        from urllib_gui.ui.bookmarks_dialog import BookmarksDialog

        return BookmarksDialog
    if name == "HistoryDialog":
        from urllib_gui.ui.history_dialog import HistoryDialog

        return HistoryDialog
    if name == "PreferencesDialog":
        from urllib_gui.ui.preferences import PreferencesDialog

        return PreferencesDialog
    raise AttributeError(name)
