"""UI widgets."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from urllib_gui.ui.request_panel import RequestDrawer
    from urllib_gui.ui.viewer import HypertextViewer

__all__ = ["HypertextViewer", "RequestDrawer"]


def __getattr__(name: str) -> object:
    if name == "HypertextViewer":
        from urllib_gui.ui.viewer import HypertextViewer

        return HypertextViewer
    if name == "RequestDrawer":
        from urllib_gui.ui.request_panel import RequestDrawer

        return RequestDrawer
    raise AttributeError(name)
