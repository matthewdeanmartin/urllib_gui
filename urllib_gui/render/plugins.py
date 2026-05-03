"""Optional third-party renderer plugin discovery."""

from __future__ import annotations

from urllib_gui.model import RenderedDocument
from urllib_gui.render.base import RenderEngine, decode_bytes


def _discover_plugins() -> list[RenderEngine]:
    plugins: list[RenderEngine] = []
    plugins.extend(_try_html2text())
    plugins.extend(_try_beautifulsoup())
    plugins.extend(_try_markdownify())
    plugins.extend(_try_inscriptis())
    return plugins


def _try_html2text() -> list[RenderEngine]:
    try:
        import html2text as _h2t  # type: ignore[import-untyped]
    except ImportError:
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
            h = _h2t.HTML2Text()
            h.ignore_links = False
            h.baseurl = base_url
            result = h.handle(text)
            return RenderedDocument(title=None, text=result.strip())

    return [Html2TextRenderer()]


def _try_beautifulsoup() -> list[RenderEngine]:
    try:
        from bs4 import BeautifulSoup  # type: ignore[import-untyped]
    except ImportError:
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
            text, used_enc = decode_bytes(html_bytes, encoding)
            soup = BeautifulSoup(text, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None
            result = soup.get_text(separator="\n")
            return RenderedDocument(title=title, text=result.strip())

    return [BeautifulSoupRenderer()]


def _try_markdownify() -> list[RenderEngine]:
    try:
        import markdownify as _md  # type: ignore[import-untyped]
    except ImportError:
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
            result = _md.markdownify(text)
            return RenderedDocument(title=None, text=result.strip())

    return [MarkdownifyRenderer()]


def _try_inscriptis() -> list[RenderEngine]:
    try:
        from inscriptis import get_text  # type: ignore[import-untyped]
    except ImportError:
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
            result = get_text(text)
            return RenderedDocument(title=None, text=result.strip())

    return [InscriptisRenderer()]
