"""urllib-based networking client."""

from __future__ import annotations

import ssl
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from typing import Any

from urllib_gui.model import RequestSpec, ResponseRecord


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that leaves 30x responses untouched."""

    def redirect_request(
        self,
        req: Any,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        _ = (req, fp, code, msg, headers, newurl)


class UrllibClient:
    """Small wrapper around urllib opener configuration."""

    def __init__(self) -> None:
        """Initialize client state."""
        self.cookie_jar = CookieJar()

    def fetch(self, spec: RequestSpec) -> ResponseRecord:
        """Fetch a resource described by *spec*."""
        opener = self.build_opener(spec)
        request = urllib.request.Request(
            spec.normalized_url(),
            data=spec.body,
            method=spec.normalized_method(),
        )
        for name, value in spec.effective_headers():
            request.add_header(name, value)

        start = time.perf_counter()
        try:
            response = opener.open(request, timeout=spec.effective_timeout())
        except urllib.error.HTTPError as error:
            elapsed = time.perf_counter() - start
            return self.record_from_stream(error, elapsed)
        except urllib.error.URLError as error:
            elapsed = time.perf_counter() - start
            return ResponseRecord(
                final_url=spec.normalized_url(),
                status=None,
                reason=None,
                headers=[],
                body=b"",
                elapsed_seconds=elapsed,
                encoding=None,
                content_type=None,
                error=f"{type(error).__name__}: {error}",
            )

        with response:
            elapsed = time.perf_counter() - start
            return self.record_from_stream(response, elapsed)

    def build_opener(self, spec: RequestSpec) -> urllib.request.OpenerDirector:
        handlers: list[urllib.request.BaseHandler] = []
        if spec.cookies_enabled:
            handlers.append(urllib.request.HTTPCookieProcessor(self.cookie_jar))
        if spec.proxy is not None:
            handlers.append(urllib.request.ProxyHandler({"http": spec.proxy, "https": spec.proxy}))
        if not spec.follow_redirects:
            handlers.append(NoRedirectHandler())
        if spec.auth is not None:
            username, password = spec.auth.basic_credentials()
            if username and password:
                password_manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                password_manager.add_password(None, spec.normalized_url(), username, password)
                handlers.append(urllib.request.HTTPBasicAuthHandler(password_manager))
        handlers.append(urllib.request.HTTPSHandler(context=self.ssl_context(spec)))
        return urllib.request.build_opener(*handlers)

    @staticmethod
    def ssl_context(spec: RequestSpec) -> ssl.SSLContext:
        """Build the TLS context for a request."""
        if spec.verify_tls:
            return ssl.create_default_context()
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    @staticmethod
    def record_from_stream(stream: Any, elapsed: float) -> ResponseRecord:
        """Build a response record from a urllib response stream."""
        message = stream.info()
        body = stream.read()
        encoding = detect_encoding(body, message.get_content_charset())
        status = getattr(stream, "status", None)
        reason = getattr(stream, "reason", None)
        return ResponseRecord(
            final_url=stream.geturl(),
            status=status,
            reason=str(reason) if reason is not None else None,
            headers=list(message.items()),
            body=body,
            elapsed_seconds=elapsed,
            encoding=encoding,
            content_type=message.get_content_type(),
        )


def detect_encoding(body: bytes, declared_encoding: str | None) -> str:
    """Guess an encoding using a simple stdlib-friendly fallback sequence."""
    if declared_encoding:
        return declared_encoding
    if body.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if body.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16"
    for candidate in ("utf-8", "latin-1"):
        try:
            body.decode(candidate)
            return candidate
        except UnicodeDecodeError:
            continue
    return "utf-8"
