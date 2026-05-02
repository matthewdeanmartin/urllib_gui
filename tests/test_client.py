"""Networking client tests."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from urllib_gui.client import UrllibClient
from urllib_gui.model import RequestSpec


class _Handler(BaseHTTPRequestHandler):
    """Small test server handler."""

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        """Serve test responses for the in-process HTTP server."""
        if self.path == "/missing":
            body = b"not found"
            self.send_response(404, "Not Found")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        body = b"<html><head><title>Home</title></head><body><a href='/next'>Next</a></body></html>"
        self.send_response(200, "OK")
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, message_format: str, *args: object) -> None:  # pylint: disable=arguments-differ
        """Suppress request logging during tests."""
        _ = (message_format, args)


def test_client_fetches_success_and_http_errors() -> None:
    """The urllib client should preserve normal and HTTP-error responses."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = UrllibClient()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        success = client.fetch(RequestSpec(url=f"{base_url}/"))
        missing = client.fetch(RequestSpec(url=f"{base_url}/missing"))
    finally:
        server.shutdown()
        thread.join()
        server.server_close()

    assert success.status == 200
    assert success.content_type == "text/html"
    assert b"Next" in success.body

    assert missing.status == 404
    assert missing.reason == "Not Found"
    assert missing.error is None
    assert missing.body == b"not found"
