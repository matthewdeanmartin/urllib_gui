"""Export helpers for generated urllib code."""

from __future__ import annotations

from pprint import pformat

from urllib_gui.model import RequestSpec


def generate_urllib_code(spec: RequestSpec) -> str:
    """Generate a Python snippet approximating *spec*."""
    headers = {name: value for name, value in spec.effective_headers()}
    lines = [
        "import urllib.request",
        "",
        f"url = {spec.normalized_url()!r}",
        "",
        f"headers = {pformat(headers)}",
    ]
    if spec.body is not None:
        body_text = spec.body.decode("utf-8", errors="replace")
        lines.extend(["", f"data = {body_text!r}.encode('utf-8')"])
    else:
        lines.extend(["", "data = None"])
    lines.extend(
        [
            "",
            "request = urllib.request.Request(",
            "    url,",
            "    headers=headers,",
            f"    method={spec.normalized_method()!r},",
            "    data=data,",
            ")",
            "",
            f"with urllib.request.urlopen(request, timeout={spec.effective_timeout()!r}) as response:",
            "    body = response.read()",
            "    print(getattr(response, 'status', None))",
            "    print(response.headers)",
            "    print(body.decode('utf-8', errors='replace'))",
        ]
    )
    return "\n".join(lines)
