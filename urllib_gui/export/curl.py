"""Export helpers for curl command generation."""

from __future__ import annotations

import shlex

from urllib_gui.model import RequestSpec


def _q(value: str) -> str:
    """Quote a curl argument only if it contains shell-special characters."""
    if not value:
        return "''"
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./~:@?=&%+#,")
    if all(c in safe for c in value):
        return value
    return shlex.quote(value)


def generate_curl_command(spec: RequestSpec) -> str:
    """Generate a best-effort curl equivalent for *spec*."""
    segments: list[str] = ["curl"]
    method = spec.normalized_method()
    if method != "GET":
        segments.append(f"-X {method}")
    for name, value in spec.effective_headers():
        segments.append(f"-H {_q(name + ': ' + value)}")
    if spec.body is not None:
        try:
            body_text = spec.body.decode("utf-8")
        except UnicodeDecodeError:
            body_text = spec.body.decode("latin-1")
        segments.append(f"--data-raw {_q(body_text)}")
    if not spec.verify_tls:
        segments.append("-k")
    if spec.proxy:
        segments.append(f"--proxy {_q(spec.proxy)}")
    timeout = spec.effective_timeout()
    if timeout is not None:
        segments.append(f"--max-time {int(timeout)}")
    segments.append(_q(spec.normalized_url()))
    return " \\\n  ".join(segments)
