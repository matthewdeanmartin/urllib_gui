"""Plain-text renderers."""

from __future__ import annotations

from urllib_gui.model import RenderedDocument
from urllib_gui.render.base import decode_bytes


class PlainTextRenderer:
    """Decode content without HTML interpretation."""

    name = "plain"
    supports_links = False

    def render(
        self,
        html_bytes: bytes,
        *,
        base_url: str,
        content_type: str | None = None,
        encoding: str | None = None,
    ) -> RenderedDocument:
        """Render bytes as plain decoded text."""
        text, used_encoding = decode_bytes(html_bytes, encoding)
        return RenderedDocument(
            title=None,
            text=text,
            metadata={"base_url": base_url, "content_type": content_type or "", "encoding": used_encoding},
        )
