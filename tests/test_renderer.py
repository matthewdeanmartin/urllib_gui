"""Renderer tests."""

from urllib_gui.render.stdlib_html import StdlibHtmlLinksRenderer


def test_html_renderer_extracts_text_title_and_links() -> None:
    """The stdlib renderer should produce readable text and resolved links."""
    renderer = StdlibHtmlLinksRenderer()
    document = renderer.render(
        b"""
        <html>
          <head><title>Example Domain</title><style>.hidden { display: none; }</style></head>
          <body>
            <h1>Example Domain</h1>
            <p>This domain is for use in examples.</p>
            <p><a href="/more">More information</a></p>
            <script>alert("nope")</script>
          </body>
        </html>
        """,
        base_url="https://example.com/docs/page.html",
        content_type="text/html",
        encoding="utf-8",
    )

    assert document.title == "Example Domain"
    assert "Example Domain" in document.text
    assert "This domain is for use in examples." in document.text
    assert "alert" not in document.text
    assert len(document.links) == 1
    assert document.links[0].href == "https://example.com/more"
    assert document.links[0].label == "More information"
