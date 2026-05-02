"""Core models and helpers for urllib_gui."""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_USER_AGENT = "urllib_gui/0.1"
SUPPORTED_SCHEMES = frozenset({"http", "https", "file"})


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(UTC)


def normalize_url(value: str) -> str:
    """Normalize a user-entered URL into a supported absolute URL."""
    candidate = value.strip()
    if not candidate:
        return candidate

    if "://" not in candidate and not candidate.startswith("file:"):
        path_candidate = Path(candidate)
        if path_candidate.exists():
            return path_candidate.resolve().as_uri()
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    if parsed.scheme and parsed.scheme not in SUPPORTED_SCHEMES:
        return candidate
    return candidate


@dataclass(frozen=True)
class AuthSpec:
    """Authentication settings for a request."""

    scheme: str
    username: str | None = None
    password: str | None = None
    token: str | None = None
    header_value: str | None = None

    def authorization_header(self) -> str | None:
        """Build an Authorization header for a supported auth spec."""
        scheme = self.scheme.lower().strip()
        if scheme == "basic" and self.username is not None and self.password is not None:
            return _basic_auth_header(self.username, self.password)
        if scheme == "bearer" and self.token:
            return f"Bearer {self.token}"
        if scheme == "header":
            return self.header_value
        return None

    def basic_credentials(self) -> tuple[str | None, str | None]:
        """Return username and password for basic auth flows."""
        return self.username, self.password


@dataclass(frozen=True)
class RequestSpec:
    """A high-level description of an urllib request."""

    url: str
    method: str = "GET"
    headers: list[tuple[str, str]] = field(default_factory=list)
    body: bytes | None = None
    timeout: float | None = None
    follow_redirects: bool = True
    verify_tls: bool = True
    proxy: str | None = None
    user_agent: str | None = None
    cookies_enabled: bool = True
    auth: AuthSpec | None = None

    def normalized_url(self) -> str:
        """Return the normalized request URL."""
        return normalize_url(self.url)

    def normalized_method(self) -> str:
        """Return the uppercased HTTP method."""
        return self.method.upper().strip() or "GET"

    def effective_timeout(self) -> float | None:
        """Return the timeout that should be used by the client."""
        return self.timeout if self.timeout is not None else DEFAULT_TIMEOUT_SECONDS

    def effective_headers(self) -> list[tuple[str, str]]:
        """Return headers after user-agent and auth defaults are applied."""
        headers = list(self.headers)
        header_names = {name.lower() for name, _ in headers}
        user_agent = self.user_agent or DEFAULT_USER_AGENT
        if user_agent and "user-agent" not in header_names:
            headers.append(("User-Agent", user_agent))
        if self.auth is not None:
            authorization = self.auth.authorization_header()
            if authorization is not None and "authorization" not in header_names:
                headers.append(("Authorization", authorization))
        return headers


@dataclass(frozen=True)
class ResponseRecord:
    """A completed response or transport error."""

    final_url: str
    status: int | None
    reason: str | None
    headers: list[tuple[str, str]]
    body: bytes
    elapsed_seconds: float
    encoding: str | None
    content_type: str | None
    error: str | None = None

    def headers_text(self) -> str:
        """Return response headers as readable text."""
        if not self.headers:
            return "(no response headers)"
        return "\n".join(f"{name}: {value}" for name, value in self.headers)


@dataclass(frozen=True)
class LinkSpan:
    """A hyperlink span in a rendered document, expressed in character offsets."""

    start_offset: int
    end_offset: int
    href: str
    label: str
    title: str | None = None


@dataclass(frozen=True)
class TextRun:
    """Plain rendered text."""

    text: str


@dataclass(frozen=True)
class LinkRun:
    """Rendered text that links somewhere."""

    text: str
    href: str
    title: str | None = None


type RenderNode = TextRun | LinkRun


@dataclass(frozen=True)
class RenderedDocument:
    """Rendered text plus metadata and hyperlink offsets."""

    title: str | None
    text: str
    links: list[LinkSpan] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    runs: list[RenderNode] = field(default_factory=list)


@dataclass(frozen=True)
class HistoryEntry:
    """A stored history record."""

    url: str
    title: str | None
    visited_at: datetime
    method: str
    status: int | None
    content_type: str | None


@dataclass(frozen=True)
class Bookmark:
    """A saved bookmark."""

    title: str
    url: str
    created_at: datetime
    tags: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass
class TabState:
    """State for a single open tab."""

    request: RequestSpec
    response: ResponseRecord | None = None
    rendered: RenderedDocument | None = None
    history_index: int = -1
    local_history: list[RequestSpec] = field(default_factory=list)
    render_engine_name: str = "stdlib_html_links"
    engine_locked: bool = False
    title: str | None = None
    loading: bool = False
    source_text: str = ""
    fetch_seq: int = 0


def history_entry_from_response(
    request: RequestSpec,
    response: ResponseRecord,
    *,
    title: str | None = None,
) -> HistoryEntry:
    """Build a history entry from a request/response pair."""
    return HistoryEntry(
        url=response.final_url,
        title=title,
        visited_at=utc_now(),
        method=request.normalized_method(),
        status=response.status,
        content_type=response.content_type,
    )


def choose_tab_title(request: RequestSpec, response: ResponseRecord | None, document: RenderedDocument | None) -> str:
    """Choose the most useful tab title available."""
    if document is not None and document.title:
        return document.title
    if response is not None:
        parsed = urlparse(response.final_url)
        if parsed.netloc:
            return parsed.netloc
    parsed_request = urlparse(request.normalized_url())
    if parsed_request.netloc:
        return parsed_request.netloc
    if request.url:
        return request.url
    return "Untitled"


def format_request_preview(spec: RequestSpec) -> str:
    """Return a human-readable preview of the current request."""
    normalized_url = spec.normalized_url()
    parsed = urlparse(normalized_url)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    host = parsed.netloc
    lines = [f"{spec.normalized_method()} {path} HTTP/1.1"]
    if host:
        lines.append(f"Host: {host}")
    for name, value in spec.effective_headers():
        lines.append(f"{name}: {value}")
    if spec.body:
        lines.extend(["", spec.body.decode("utf-8", errors="replace")])
    return "\n".join(lines)


def make_bookmark(title: str | None, url: str) -> Bookmark:
    """Create a bookmark from the current tab."""
    return Bookmark(title=title or url, url=url, created_at=utc_now())


def _basic_auth_header(username: str, password: str) -> str:
    """Return a basic auth header value."""
    token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return f"Basic {token}"
