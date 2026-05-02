"""Built-in render engines."""

from __future__ import annotations

from urllib_gui.render.base import RenderEngine, choose_default_engine_name
from urllib_gui.render.plain import PlainTextRenderer
from urllib_gui.render.source import HtmlSourceRenderer
from urllib_gui.render.stdlib_html import StdlibHtmlLinksRenderer, StdlibHtmlTextRenderer


def built_in_renderers() -> dict[str, RenderEngine]:
    """Return the built-in stdlib render engines."""
    renderers: list[RenderEngine] = [
        PlainTextRenderer(),
        StdlibHtmlTextRenderer(),
        StdlibHtmlLinksRenderer(),
        HtmlSourceRenderer(),
    ]
    return {renderer.name: renderer for renderer in renderers}


__all__ = ["RenderEngine", "built_in_renderers", "choose_default_engine_name"]
