"""Built-in render engines."""

from __future__ import annotations

from urllib_gui.render.base import RenderEngine, choose_default_engine_name
from urllib_gui.render.plain import PlainTextRenderer
from urllib_gui.render.plugins import _discover_plugins
from urllib_gui.render.source import HtmlSourceRenderer
from urllib_gui.render.stdlib_html import StdlibHtmlLinksRenderer, StdlibHtmlTextRenderer


def built_in_renderers() -> dict[str, RenderEngine]:
    """Return all available render engines: built-in plus any installed plugins."""
    renderers: list[RenderEngine] = [
        PlainTextRenderer(),
        StdlibHtmlTextRenderer(),
        StdlibHtmlLinksRenderer(),
        HtmlSourceRenderer(),
    ]
    renderers.extend(_discover_plugins())
    return {renderer.name: renderer for renderer in renderers}


__all__ = ["RenderEngine", "built_in_renderers", "choose_default_engine_name"]
