"""A modest stdlib-only HTML-to-text renderer."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from urllib_gui.model import LinkRun, LinkSpan, RenderedDocument, RenderNode, TextRun
from urllib_gui.render.base import decode_bytes

BLOCK_ELEMENTS = {
    "article",
    "blockquote",
    "body",
    "div",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tr",
    "ul",
}
IGNORED_ELEMENTS = {"audio", "canvas", "embed", "iframe", "noscript", "object", "script", "style", "svg", "video"}


class DocumentBuilder(HTMLParser):
    """Convert a subset of HTML into readable text and link spans."""

    def __init__(self, *, base_url: str, track_links: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.track_links = track_links
        self.output: list[str] = []
        self.runs: list[RenderNode] = []
        self.links: list[LinkSpan] = []
        self.title_parts: list[str] = []
        self.ignored_depth = 0
        self.in_title = False
        self.in_pre = False
        self.list_stack: list[tuple[str, int]] = []
        self.active_link_href: str | None = None
        self.active_link_title: str | None = None
        self.active_link_start: int | None = None
        self.active_link_label: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle the opening of an HTML tag."""
        attr_map = {name: value or "" for name, value in attrs}
        if tag in IGNORED_ELEMENTS:
            self.ignored_depth += 1
        elif tag == "title":
            self.in_title = True
        elif self.ignored_depth:
            return
        elif tag == "br":
            self.ensure_newlines(1)
        elif tag == "hr":
            self.ensure_newlines(1)
            self.append_raw("----")
            self.ensure_newlines(1)
        elif tag in {"p", "div", "section", "article", "main", "header", "footer", "nav", "blockquote"} or tag in {
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        }:
            self.ensure_newlines(2)
        elif tag == "pre":
            self.ensure_newlines(2)
            self.in_pre = True
        elif tag == "ul":
            self.ensure_newlines(2)
            self.list_stack.append(("ul", 0))
        elif tag == "ol":
            self.ensure_newlines(2)
            self.list_stack.append(("ol", 0))
        elif tag == "li":
            self.ensure_newlines(1)
            indent = "  " * max(len(self.list_stack) - 1, 0)
            if self.list_stack:
                list_type, counter = self.list_stack[-1]
                if list_type == "ol":
                    counter += 1
                    self.list_stack[-1] = (list_type, counter)
                    bullet = f"{counter}. "
                else:
                    bullet = "• "
            else:
                bullet = "• "
            self.append_raw(f"{indent}{bullet}")
        elif tag == "a":
            href = attr_map.get("href", "")
            self.active_link_href = urljoin(self.base_url, href)
            self.active_link_title = attr_map.get("title") or None
            self.active_link_start = self.length
            self.active_link_label = []
        elif tag in {"td", "th"} and self.length and self.output[-1] not in {" ", "\n", "\t"}:
            self.append_raw("  ")

    def handle_endtag(self, tag: str) -> None:
        if tag in IGNORED_ELEMENTS:
            self.ignored_depth = max(self.ignored_depth - 1, 0)
            return
        if tag == "title":
            self.in_title = False
            return
        if self.ignored_depth:
            return
        if tag == "a":
            self.finish_link()
            return
        if tag == "pre":
            self.in_pre = False
            self.ensure_newlines(2)
            return
        if tag in {"li", "tr"}:
            self.ensure_newlines(1)
            return
        if tag in BLOCK_ELEMENTS:
            self.ensure_newlines(2 if tag not in {"li", "tr"} else 1)
        if tag in {"ul", "ol"} and self.list_stack:
            self.list_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
            return
        if self.ignored_depth:
            return
        if self.in_pre:
            self.append(data)
            return
        for token in re.findall(r"\S+|\s+", data):
            if token.isspace():
                self.append_space()
            else:
                self.append(token)

    @property
    def length(self) -> int:
        return sum(len(part) for part in self.output)

    def append(self, text: str) -> None:
        self.append_raw(text)
        if self.active_link_href:
            self.active_link_label.append(text)

    def append_raw(self, text: str) -> None:
        if not text:
            return
        self.output.append(text)

    def append_space(self) -> None:
        if not self.output:
            return
        if self.output[-1].endswith((" ", "\n", "\t")):
            return
        self.append_raw(" ")
        if self.active_link_href:
            self.active_link_label.append(" ")

    def ensure_newlines(self, count: int) -> None:
        if not self.output:
            return
        while self.output and self.output[-1].endswith(" "):
            self.output[-1] = self.output[-1][:-1]
            if not self.output[-1]:
                self.output.pop()
        current = 0
        for character in reversed("".join(self.output[-count - 2 :])):
            if character == "\n":
                current += 1
            elif character == " ":
                continue
            else:
                break
        if current >= count:
            return
        self.output.append("\n" * (count - current))

    def finish_link(self) -> None:
        href = self.active_link_href
        start = self.active_link_start
        if href is None or start is None:
            self.active_link_href = None
            self.active_link_title = None
            self.active_link_start = None
            self.active_link_label = []
            return
        end = self.length
        label = "".join(self.active_link_label).strip() or href
        if self.track_links and end > start:
            self.links.append(
                LinkSpan(
                    start_offset=start,
                    end_offset=end,
                    href=href,
                    label=label,
                    title=self.active_link_title,
                )
            )
            self.runs.append(LinkRun(text=label, href=href, title=self.active_link_title))
        elif label:
            self.runs.append(TextRun(text=label))
        self.active_link_href = None
        self.active_link_title = None
        self.active_link_start = None
        self.active_link_label = []

    def finalize(self) -> RenderedDocument:
        """Build the final rendered document."""
        raw_text = "".join(self.output)
        leading_trim = len(raw_text) - len(raw_text.lstrip())
        text = raw_text.strip()
        adjusted_links: list[LinkSpan] = []
        for link in self.links:
            start_offset = max(link.start_offset - leading_trim, 0)
            end_offset = max(link.end_offset - leading_trim, 0)
            if start_offset < end_offset <= len(text):
                adjusted_links.append(
                    LinkSpan(
                        start_offset=start_offset,
                        end_offset=end_offset,
                        href=link.href,
                        label=link.label,
                        title=link.title,
                    )
                )
        title = " ".join(part.strip() for part in self.title_parts if part.strip()) or None
        return RenderedDocument(
            title=title,
            text=text,
            links=adjusted_links,
            metadata={"base_url": self.base_url},
            runs=list(self.runs),
        )


class BaseStdlibHtmlRenderer:
    """Base class for stdlib HTML rendering."""

    supports_links = False

    def __init__(self, *, track_links: bool) -> None:
        self.track_links = track_links

    def render(
        self,
        html_bytes: bytes,
        *,
        base_url: str,
        content_type: str | None = None,
        encoding: str | None = None,
    ) -> RenderedDocument:
        """Render HTML bytes into a text document."""
        text, used_encoding = decode_bytes(html_bytes, encoding)
        builder = DocumentBuilder(base_url=base_url, track_links=self.track_links)
        builder.feed(text)
        builder.close()
        document = builder.finalize()
        metadata = dict(document.metadata)
        metadata["content_type"] = content_type or ""
        metadata["encoding"] = used_encoding
        return RenderedDocument(
            title=document.title,
            text=document.text,
            links=document.links,
            metadata=metadata,
            runs=document.runs,
        )


class StdlibHtmlTextRenderer(BaseStdlibHtmlRenderer):
    """HTML-to-text renderer without clickable links."""

    name = "stdlib_html_text"

    def __init__(self) -> None:
        super().__init__(track_links=False)


class StdlibHtmlLinksRenderer(BaseStdlibHtmlRenderer):
    """HTML-to-text renderer that preserves link spans."""

    name = "stdlib_html_links"
    supports_links = True

    def __init__(self) -> None:
        super().__init__(track_links=True)
