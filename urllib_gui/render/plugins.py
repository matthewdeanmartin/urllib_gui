"""Optional third-party renderer plugin discovery."""

from __future__ import annotations

from importlib import import_module
from typing import Any, cast

from urllib_gui.model import RenderedDocument
from urllib_gui.render.base import RenderEngine, decode_bytes


def import_optional_module(module_name: str) -> Any | None:
    """Import an optional renderer dependency when available."""
    try:
        return import_module(module_name)
    except ImportError:
        return None


def _discover_plugins() -> list[RenderEngine]:
    plugins: list[RenderEngine] = []
    plugins.extend(_try_html2text())
    plugins.extend(_try_beautifulsoup())
    plugins.extend(_try_markdownify())
    plugins.extend(_try_inscriptis())
    return plugins


def _try_html2text() -> list[RenderEngine]:
    html2text = import_optional_module("html2text")
    if html2text is None:
        return []

    class Html2TextRenderer:
        name = "html2text"
        supports_links = False

        def render(
            self,
            html_bytes: bytes,
            *,
            base_url: str,
            content_type: str | None = None,
            encoding: str | None = None,
        ) -> RenderedDocument:
            text, _ = decode_bytes(html_bytes, encoding)
            h = cast(Any, html2text).HTML2Text()
            h.ignore_links = False
            h.baseurl = base_url
            result = h.handle(text)
            return RenderedDocument(title=None, text=result.strip())

    return [Html2TextRenderer()]


def _try_beautifulsoup() -> list[RenderEngine]:
    bs4 = import_optional_module("bs4")
    if bs4 is None:
        return []

    class BeautifulSoupRenderer:
        name = "beautifulsoup"
        supports_links = False

        def render(
            self,
            html_bytes: bytes,
            *,
            base_url: str,
            content_type: str | None = None,
            encoding: str | None = None,
        ) -> RenderedDocument:
            text, _ = decode_bytes(html_bytes, encoding)
            soup = cast(Any, bs4).BeautifulSoup(text, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None
            result = soup.get_text(separator="\n")
            return RenderedDocument(title=title, text=result.strip())

    return [BeautifulSoupRenderer()]


def _try_markdownify() -> list[RenderEngine]:
    markdownify = import_optional_module("markdownify")
    if markdownify is None:
        return []

    class MarkdownifyRenderer:
        name = "markdownify"
        supports_links = False

        def render(
            self,
            html_bytes: bytes,
            *,
            base_url: str,
            content_type: str | None = None,
            encoding: str | None = None,
        ) -> RenderedDocument:
            text, _ = decode_bytes(html_bytes, encoding)
            result = cast(Any, markdownify).markdownify(text)
            return RenderedDocument(title=None, text=result.strip())

    return [MarkdownifyRenderer()]


def _try_inscriptis() -> list[RenderEngine]:
    inscriptis = import_optional_module("inscriptis")
    if inscriptis is None:
        return []

    class InscriptisRenderer:
        name = "inscriptis"
        supports_links = False

        def render(
            self,
            html_bytes: bytes,
            *,
            base_url: str,
            content_type: str | None = None,
            encoding: str | None = None,
        ) -> RenderedDocument:
            text, _ = decode_bytes(html_bytes, encoding)
            result = cast(Any, inscriptis).get_text(text)
            return RenderedDocument(title=None, text=result.strip())

    return [InscriptisRenderer()]
