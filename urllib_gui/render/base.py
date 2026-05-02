"""Render engine interfaces and shared helpers."""

from __future__ import annotations

from typing import Protocol

from urllib_gui.model import RenderedDocument, ResponseRecord


class RenderEngine(Protocol):
    """Protocol implemented by all render engines."""

    name: str
    supports_links: bool

    def render(
        self,
        html_bytes: bytes,
        *,
        base_url: str,
        content_type: str | None = None,
        encoding: str | None = None,
    ) -> RenderedDocument:
        """Render bytes into a text document."""


def decode_bytes(body: bytes, encoding: str | None = None) -> tuple[str, str]:
    """Decode response bytes with a conservative fallback strategy."""
    candidates = [candidate for candidate in (encoding, "utf-8", "latin-1", "utf-8") if candidate]
    for candidate in candidates:
        try:
            if candidate == "utf-8" and candidate == candidates[-1]:
                return body.decode(candidate, errors="replace"), candidate
            return body.decode(candidate), candidate
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace"), "utf-8"


def choose_default_engine_name(response: ResponseRecord) -> str:
    """Choose the default render engine for a response."""
    if response.content_type and "html" in response.content_type:
        return "stdlib_html_links"
    if looks_like_html(response.body):
        return "stdlib_html_links"
    return "plain"


def looks_like_html(body: bytes) -> bool:
    """Sniff the first non-whitespace bytes for an HTML signature."""
    head = body.lstrip()[:512].lower()
    return head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"<html" in head[:256]
