"""Export helper tests."""

from urllib_gui.export import generate_urllib_code
from urllib_gui.model import RequestSpec


def test_generate_urllib_code_includes_core_request_fields() -> None:
    """Generated code should reflect the current request."""
    code = generate_urllib_code(
        RequestSpec(
            url="example.com/api",
            method="POST",
            headers=[("Accept", "application/json")],
            body=b'{"name": "Matt"}',
        )
    )

    assert "urllib.request.Request" in code
    assert "'https://example.com/api'" in code
    assert '"Accept"' in code or "'Accept'" in code
    assert "'POST'" in code
    assert '{"name": "Matt"}' in code
