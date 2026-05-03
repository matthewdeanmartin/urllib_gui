"""UI widgets."""

from __future__ import annotations

from importlib import import_module
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

UI_MODULES = {
    "HypertextViewer": "urllib_gui.ui.viewer",
    "RequestDrawer": "urllib_gui.ui.request_panel",
    "CookieJarDialog": "urllib_gui.ui.cookie_jar",
    "ScratchpadDialog": "urllib_gui.ui.scratchpad",
    "BookmarksDialog": "urllib_gui.ui.bookmarks_dialog",
    "HistoryDialog": "urllib_gui.ui.history_dialog",
    "PreferencesDialog": "urllib_gui.ui.preferences",
}


def __getattr__(name: str) -> object:
    module_name = UI_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(module_name)
    if hasattr(module, name):
        return getattr(module, name)
    raise AttributeError(name)
