# `urllib_gui` Specification

## 1. Summary

`urllib_gui` is a lightweight, Tkinter-based desktop application for browsing and inspecting web resources using Python’s standard-library `urllib` stack.

It is **not** a modern web browser. It is closer to:

> “A graphical, urllib-shaped web client with hypertext-aware text viewing.”

The primary interface is a tabbed text viewer with clickable links, a powerful request/location bar, history, bookmarks, request configuration forms, and pluggable HTML-to-text engines.

`urllib_gui` should feel like what might plausibly exist in the Python standard library if Tkinter, `urllib`, `html.parser`, `webbrowser`, and `configparser` had been composed into a small but useful hypertext utility.

---

# 2. Design Philosophy

## 2.1 Almost stdlib

The default implementation should depend only on Python’s standard library:

```text
tkinter
urllib.request
urllib.parse
urllib.error
http.cookiejar
html.parser
html
email.message
ssl
json
configparser
sqlite3
webbrowser
dataclasses
typing
```

Optional dependencies may be supported through plugins, but the core app must work without them.

## 2.2 `urllib`-shaped

The app should expose concepts that map clearly to `urllib`, not hide them behind browser metaphors.

For example, the request editor should expose:

```text
URL
method
headers
data/body
timeout
redirect policy
proxy settings
SSL verification
cookies
auth
User-Agent
```

Rather than only having a browser-style address bar.

The user should gradually learn `urllib` concepts by using the app.

## 2.3 Hypertext minimum viable product

The viewer should support:

```text
plain text
HTML converted to readable text
clickable links when the selected engine supports them
basic title detection
status, headers, and errors
```

The viewer should not attempt browser layout.

## 2.4 Honest rendering

`urllib_gui` should never pretend to be displaying a faithful browser rendering.

HTML pages should be shown as extracted text with optional hyperlinks. The app should make the rendering engine visible and switchable.

---

# 3. Goals

## 3.1 Primary goals

`urllib_gui` should provide:

1. A Tkinter GUI for making HTTP/HTTPS/file requests through `urllib`.
2. A tabbed interface for multiple pages or requests.
3. A location bar with request options beyond a normal browser address bar.
4. Plain-text and HTML-to-text viewing.
5. Clickable links in the text viewer when possible.
6. Request/response inspection.
7. History.
8. Bookmarks.
9. Basic theming.
10. A plugin interface for alternate HTML-to-text engines.

## 3.2 Secondary goals

The app should also support:

1. Saving responses to disk.
2. Copying request as Python `urllib` code.
3. Copying request as `curl`, where reasonable.
4. Viewing headers.
5. Viewing source.
6. Opening links externally in the system browser.
7. Basic cookie handling.
8. Basic proxy configuration.
9. Basic authentication helpers.
10. Import/export bookmarks.

---

# 4. Non-goals

`urllib_gui` will not support:

```text
JavaScript execution
CSS layout
CSS cascade
DOM scripting
canvas
SVG rendering beyond source/text fallback
media playback
browser extensions
Service Workers
WebSockets
WebRTC
browser-grade security sandboxing
pixel-perfect layout
modern web-app compatibility
```

It is not intended to replace Firefox, Chrome, Safari, Edge, Qt WebEngine, CEF, Playwright, or pywebview.

---

# 5. Target Users

## 5.1 Python developers

Developers who want to inspect URLs and HTTP behavior without leaving Python’s mental model.

## 5.2 CLI users who want forms

People who like `curl`, `httpie`, or Postman-style workflows but want a small native GUI.

## 5.3 Text-first web users

Users who want to read simple pages, documentation, source pages, old-school sites, logs, text files, or HTML email-like content.

## 5.4 Educators and learners

People teaching or learning HTTP, URLs, headers, encodings, cookies, and `urllib`.

---

# 6. Application Model

## 6.1 Core object model

```python
@dataclass
class RequestSpec:
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


@dataclass
class ResponseRecord:
    final_url: str
    status: int | None
    reason: str | None
    headers: list[tuple[str, str]]
    body: bytes
    elapsed_seconds: float
    encoding: str | None
    content_type: str | None
    error: str | None = None


@dataclass
class RenderedDocument:
    title: str | None
    text: str
    links: list["LinkSpan"]
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class LinkSpan:
    start: str
    end: str
    href: str
    label: str
    title: str | None = None
```

The GUI should move through this pipeline:

```text
RequestSpec
    ↓
urllib opener
    ↓
ResponseRecord
    ↓
content decoder
    ↓
render engine
    ↓
RenderedDocument
    ↓
Tkinter Text widget
```

---

# 7. User Interface

## 7.1 Main window layout

The default main window should contain:

```text
┌──────────────────────────────────────────────────────────────┐
│ Menu bar                                                     │
├──────────────────────────────────────────────────────────────┤
│ Toolbar / location bar                                      │
├──────────────────────────────────────────────────────────────┤
│ Request options drawer, collapsible                         │
├──────────────────────────────────────────────────────────────┤
│ Tab bar                                                      │
├──────────────────────────────────────────────────────────────┤
│ Text viewer                                                  │
├──────────────────────────────────────────────────────────────┤
│ Status bar                                                   │
└──────────────────────────────────────────────────────────────┘
```

## 7.2 Menu bar

Recommended menus:

```text
File
  New Tab
  Open URL
  Open File
  Save Response Body As...
  Save Rendered Text As...
  Close Tab
  Quit

Edit
  Copy
  Copy Link URL
  Find
  Preferences

View
  Reload
  Stop
  View Rendered Text
  View Source
  View Headers
  View Request
  Toggle Request Options
  Zoom In
  Zoom Out
  Reset Zoom

History
  Back
  Forward
  Show History
  Clear History

Bookmarks
  Bookmark This Page
  Show Bookmarks
  Import Bookmarks
  Export Bookmarks

Tools
  Copy as urllib Code
  Copy as curl
  Request Scratchpad
  Cookie Jar
  Encoding Override

Help
  About urllib_gui
```

---

# 8. Location Bar on Steroids

## 8.1 Compact mode

The compact location bar should look browser-like:

```text
[ Back ] [ Forward ] [ Reload ] [ URL entry ................................ ] [ Go ]
```

The URL entry accepts:

```text
https://example.com
example.com
http://localhost:8000
file:///tmp/example.html
```

For bare hostnames, the app may default to `https://`.

## 8.2 Expanded request mode

The expanded request panel should expose request settings in forms.

Fields:

```text
URL
Method
Headers
Body
Body type
Timeout
User-Agent
Accept
Redirect behavior
Cookies
TLS verification
Proxy
Authentication
Render engine
```

## 8.3 Request method selector

Supported methods in the UI:

```text
GET
HEAD
POST
PUT
PATCH
DELETE
OPTIONS
Custom...
```

Internally, this should map to `urllib.request.Request(..., method=method)`.

## 8.4 Headers editor

The headers editor should be a table:

```text
Enabled | Header Name        | Value
--------|--------------------|-----------------------------
[x]     | User-Agent         | urllib_gui/0.1
[x]     | Accept             | text/html,text/plain,*/*
[ ]     | Authorization      |
```

Features:

```text
Add header
Remove header
Enable/disable header
Header presets
```

Suggested presets:

```text
Browser-ish
Python urllib default
JSON API
Plain text
HTML only
No cache
```

## 8.5 Body editor

The body editor should support:

```text
Raw
Form URL-encoded
JSON
Multipart, later
```

Initial implementation may include only:

```text
raw bytes/text
application/x-www-form-urlencoded
application/json
```

## 8.6 Query parameter editor

A URL query editor should be available:

```text
Enabled | Name | Value
--------|------|------
[x]     | q    | tkinter
[x]     | page | 1
```

The URL field and query editor should stay synchronized.

## 8.7 Request preview

The app should show a generated request preview:

```text
GET /search?q=tkinter HTTP/1.1
Host: example.com
User-Agent: urllib_gui/0.1
Accept: text/html,text/plain,*/*
```

This is informational only. Exact wire representation is still delegated to `urllib`.

---

# 9. Viewer

## 9.1 Main text viewer

The primary rendering area should be a Tkinter `Text` widget.

Capabilities:

```text
display text
select/copy text
click links
search within page
font selection
font size adjustment
optional line wrapping
```

## 9.2 Link behavior

Links should be represented as tagged ranges in the `Text` widget.

Default styling:

```text
blue foreground
underline
hand cursor on hover
```

Click behavior:

```text
Left click          open in current tab
Ctrl/Cmd+click      open in new tab
Middle click        open in new tab
Right click         context menu
```

Context menu:

```text
Open Link
Open Link in New Tab
Copy Link URL
Open Link in External Browser
Bookmark Link
```

## 9.3 Link resolution

Relative links must be resolved against the response URL:

```python
urllib.parse.urljoin(base_url, href)
```

The renderer should store original and resolved hrefs where practical.

## 9.4 Source view

Every tab should support switching between:

```text
Rendered Text
Source
Headers
Request
```

Source view shows decoded text if possible, otherwise a binary-safe placeholder.

## 9.5 Binary content fallback

For binary responses, show metadata:

```text
Binary response

URL: https://example.com/file.zip
Content-Type: application/zip
Size: 2.4 MB

[ Save Body As... ]
[ Open Externally ]
```

---

# 10. HTML-to-Text Engines

`urllib_gui` should support multiple render engines.

## 10.1 Engine interface

```python
class RenderEngine(Protocol):
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
        ...
```

## 10.2 Built-in engines

### 10.2.1 `plain`

Shows decoded text without HTML interpretation.

Useful for:

```text
text/plain
JSON
XML
source inspection
debugging
```

### 10.2.2 `stdlib_html_text`

A standard-library-only HTML parser based on `html.parser.HTMLParser`.

Supports:

```text
headings as blank-line-separated text
paragraph breaks
line breaks
lists
links as visible text
optional footnote-style links
title extraction
```

May support clickable links.

Example rendering:

```text
Example Domain

This domain is for use in illustrative examples in documents.

More information...
```

### 10.2.3 `stdlib_html_links`

A variant of the stdlib parser that preserves link spans for the `Text` widget.

This should be the default HTML engine.

### 10.2.4 `html_source`

Displays original source.

This engine should not parse. It simply decodes and shows the HTML.

## 10.3 Optional third-party engines

Optional engines may be detected at runtime:

```text
BeautifulSoup engine
lxml engine
html2text engine
markdownify engine
trafilatura engine
readability-lxml engine
inscriptis engine
```

These should never be required for the base application.

## 10.4 Engine picker

Each tab should expose an engine picker:

```text
Render as:
[ stdlib html with links v ]
```

Changing the engine should re-render the current response without re-fetching unless requested.

---

# 11. Standard-Library HTML Renderer

## 11.1 Scope

The default renderer should be deliberately modest.

Supported tags:

```text
html
head
title
body
main
article
section
nav
header
footer
p
br
hr
h1-h6
a
ul
ol
li
pre
code
blockquote
table
thead
tbody
tr
th
td
strong
b
em
i
```

Ignored tags:

```text
script
style
noscript, maybe configurable
canvas
svg
iframe
object
embed
video
audio
```

## 11.2 Whitespace rules

The renderer should normalize whitespace outside preformatted contexts.

General rules:

```text
Collapse repeated spaces.
Preserve paragraph boundaries.
Insert blank lines around headings.
Insert newlines after block elements.
Preserve whitespace inside <pre>.
```

## 11.3 Link representation

When parsing:

```html
<a href="/about">About us</a>
```

The renderer should produce:

```python
LinkSpan(
    start="line.char",
    end="line.char",
    href="https://example.com/about",
    label="About us",
)
```

Since Tkinter indices are only known after insertion, the renderer may alternatively emit a stream:

```python
TextRun("Go to ")
LinkRun("About us", href="https://example.com/about")
TextRun(".")
```

Then the viewer converts runs to `Text` indices.

Preferred internal representation:

```python
@dataclass
class TextRun:
    text: str

@dataclass
class LinkRun:
    text: str
    href: str
    title: str | None = None

RenderNode = TextRun | LinkRun
```

Then `RenderedDocument` can be constructed during insertion.

## 11.4 Lists

Unordered lists:

```text
• item
• item
```

Ordered lists:

```text
1. item
2. item
```

Nested lists may be indented, but sophisticated layout is out of scope.

## 11.5 Tables

Tables should render as whitespace-separated text.

Initial table rendering may be simple:

```text
Name    Age
Alice   30
Bob     28
```

No complex cell spanning is required.

## 11.6 Forms

Forms are initially displayed as text.

Example:

```text
[form action="/search" method="GET"]
  q: [input text]
  [submit: Search]
[/form]
```

Actual form submission belongs to the roadmap.

---

# 12. Networking Layer

## 12.1 `urllib` first

All HTTP requests should be executed through `urllib.request`.

The app should use:

```python
urllib.request.Request
urllib.request.OpenerDirector
urllib.request.build_opener
urllib.request.HTTPCookieProcessor
urllib.request.ProxyHandler
urllib.request.HTTPRedirectHandler
urllib.request.HTTPSHandler
urllib.error.HTTPError
urllib.error.URLError
```

## 12.2 Request execution

```python
class UrllibClient:
    def fetch(self, spec: RequestSpec) -> ResponseRecord:
        ...
```

## 12.3 Redirects

The UI should offer:

```text
Follow redirects
Do not follow redirects
Show redirect chain
```

Implementation may require custom redirect handlers.

## 12.4 Timeout

Expose timeout as a field.

Default:

```text
30 seconds
```

Allow:

```text
no timeout
custom seconds
```

## 12.5 TLS

Expose:

```text
Verify TLS certificates
Use default SSL context
Use custom CA bundle, later
Allow insecure TLS, with warning
```

Internally:

```python
ssl.create_default_context()
ssl._create_unverified_context()
```

The insecure option should be visibly marked.

## 12.6 Proxies

Expose proxy configuration:

```text
No proxy
Use environment proxy settings
Manual HTTP proxy
Manual HTTPS proxy
```

Map to:

```python
urllib.request.ProxyHandler
```

## 12.7 Cookies

Use:

```python
http.cookiejar.CookieJar
```

Default behavior:

```text
session cookies enabled
persistent cookies optional
```

Cookie UI:

```text
View cookies for current domain
Clear session cookies
Clear all cookies
Enable/disable cookies
```

## 12.8 Authentication

Initial auth helpers:

```text
Basic Auth
Bearer token header
Custom Authorization header
```

Basic Auth can use:

```python
urllib.request.HTTPBasicAuthHandler
urllib.request.HTTPPasswordMgrWithDefaultRealm
```

Bearer tokens can simply add:

```text
Authorization: Bearer <token>
```

---

# 13. Tabs

## 13.1 Tab state

Each tab should maintain:

```python
@dataclass
class TabState:
    request: RequestSpec
    response: ResponseRecord | None
    rendered: RenderedDocument | None
    history_index: int
    local_history: list[RequestSpec]
    render_engine_name: str
    title: str | None
    loading: bool = False
```

## 13.2 Tab title

Tab title priority:

```text
HTML <title>
final URL hostname
request URL
Untitled
```

## 13.3 Back and forward

Each tab should maintain its own navigation history.

Global history is separate.

---

# 14. History

## 14.1 History record

```python
@dataclass
class HistoryEntry:
    url: str
    title: str | None
    visited_at: datetime
    method: str
    status: int | None
    content_type: str | None
```

## 14.2 Storage

Use SQLite by default:

```text
~/.urllib_gui/history.sqlite3
```

Suggested table:

```sql
CREATE TABLE history (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    method TEXT NOT NULL,
    status INTEGER,
    content_type TEXT,
    visited_at TEXT NOT NULL
);
```

## 14.3 History UI

History view should support:

```text
search
sort by date
open in current tab
open in new tab
copy URL
delete entry
clear all
```

---

# 15. Bookmarks

## 15.1 Bookmark model

```python
@dataclass
class Bookmark:
    title: str
    url: str
    created_at: datetime
    tags: list[str]
    notes: str | None = None
```

## 15.2 Storage

Use SQLite or JSON.

For stdlib simplicity, SQLite is preferred.

Suggested table:

```sql
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    tags TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);
```

Tags may be stored as JSON text using stdlib `json`.

## 15.3 Bookmark UI

Features:

```text
Bookmark this page
Edit bookmark
Delete bookmark
Search bookmarks
Tag bookmarks
Open bookmark
Import/export bookmarks as JSON
```

## 15.4 Bookmark bar

Optional bookmark toolbar:

```text
[ Python docs ] [ Localhost ] [ RFCs ] [ Project docs ]
```

---

# 16. Request Scratchpad

A request scratchpad should allow users to create named reusable requests.

Example:

```text
Name: Local API health check
Method: GET
URL: http://localhost:8000/health
Headers:
  Accept: application/json
```

This is distinct from bookmarks because it may include:

```text
method
headers
body
auth
timeout
proxy settings
```

## 16.1 Storage model

```python
@dataclass
class SavedRequest:
    name: str
    spec: RequestSpec
    created_at: datetime
    updated_at: datetime
    tags: list[str]
```

---

# 17. Theming

## 17.1 Theme goals

Theming should use what Tkinter can realistically support.

The app should support:

```text
light theme
dark theme
system-ish theme
custom font family
custom font size
link color
visited link color
background color
foreground color
selection colors, where practical
```

## 17.2 Implementation

Use:

```python
tkinter.ttk.Style
Text widget tag configuration
configuration file
```

## 17.3 Theme config

Example:

```ini
[theme]
name = dark
font_family = TkFixedFont
font_size = 12
text_background = #1e1e1e
text_foreground = #dddddd
link_foreground = #6ab0ff
visited_link_foreground = #b48cff
```

---

# 18. Configuration

## 18.1 Config directory

Recommended:

```text
~/.urllib_gui/
```

Files:

```text
config.ini
history.sqlite3
bookmarks.sqlite3
cookies.lwp
saved_requests.sqlite3
```

## 18.2 Config file

Example:

```ini
[network]
timeout = 30
user_agent = urllib_gui/0.1
cookies_enabled = true
verify_tls = true
use_environment_proxies = true

[rendering]
default_engine = stdlib_html_links
default_encoding = utf-8
show_link_urls = false

[ui]
theme = system
font_family = TkDefaultFont
font_size = 12
open_links_in_new_tab = false
```

---

# 19. Generated Code Export

## 19.1 Copy as urllib code

The app should be able to generate a Python snippet approximating the current request.

Example:

```python
import urllib.request

url = "https://example.com"

headers = {
    "User-Agent": "urllib_gui/0.1",
    "Accept": "text/html,text/plain,*/*",
}

request = urllib.request.Request(
    url,
    headers=headers,
    method="GET",
)

with urllib.request.urlopen(request, timeout=30) as response:
    body = response.read()
    print(response.status)
    print(response.headers)
    print(body.decode("utf-8", errors="replace"))
```

This reinforces the “urllib-shaped” design.

## 19.2 Copy as curl

Generate a reasonable `curl` equivalent:

```bash
curl \
  -X GET \
  -H 'User-Agent: urllib_gui/0.1' \
  -H 'Accept: text/html,text/plain,*/*' \
  'https://example.com'
```

This should be best-effort, not exact feature parity.

---

# 20. Error Handling

## 20.1 Error page

Errors should render inside the tab as readable diagnostic pages.

Example:

```text
Request failed

URL:
https://example.invalid

Error:
URLError: [Errno -2] Name or service not known

What happened:
The host could not be resolved.

Options:
[ Retry ]
[ Edit Request ]
[ Copy Error ]
```

## 20.2 HTTP errors

`urllib` raises `HTTPError` for some status codes, but `HTTPError` also contains a response body.

The app should preserve and display:

```text
status code
reason
headers
body
```

Example:

```text
HTTP 404 Not Found

https://example.com/missing

[Rendered response body below]
```

## 20.3 Encoding errors

Fallback decode strategy:

```text
1. charset from Content-Type
2. BOM detection, if simple
3. utf-8
4. latin-1
5. utf-8 with replacement
```

The selected encoding should be visible and overrideable.

---

# 21. Security Model

## 21.1 No script execution

The app does not execute JavaScript.

This eliminates many browser-style risks but does not make the app automatically safe.

## 21.2 External links

Opening a link externally should clearly hand off to the system browser.

## 21.3 Local files

Support for `file://` URLs should be configurable.

Default:

```text
enabled
```

But remote pages should not get special privileges to read local files. Since there is no JS, the main concern is accidental user navigation.

## 21.4 Dangerous schemes

Supported schemes:

```text
http
https
file
```

Optional schemes:

```text
ftp, if urllib support is desired
data, maybe later
```

Unsupported or confirm-before-open:

```text
mailto
javascript
tel
shell
custom application schemes
```

`javascript:` links should be inert and shown as unsupported.

## 21.5 TLS warnings

Disabling TLS verification should show a visible warning in the request panel and status bar.

---

# 22. Accessibility

Minimum accessibility goals:

```text
keyboard navigation
copyable text
adjustable font size
high-contrast themes
visible focus indicators
menu accelerators
```

Keyboard shortcuts:

```text
Ctrl+L        focus URL bar
Ctrl+T        new tab
Ctrl+W        close tab
Ctrl+R        reload
Alt+Left      back
Alt+Right     forward
Ctrl+F        find
Ctrl+D        bookmark
Ctrl+S        save response
Ctrl+Plus     zoom in
Ctrl+Minus    zoom out
Ctrl+0        reset zoom
```

On macOS, use Command equivalents where reasonable.

---

# 23. Package Structure

Proposed package layout:

```text
urllib_gui/
  __init__.py
  __main__.py

  app.py
  main_window.py

  model.py
  client.py
  render/
    __init__.py
    base.py
    plain.py
    stdlib_html.py
    source.py
  ui/
    __init__.py
    tabs.py
    viewer.py
    request_panel.py
    headers_editor.py
    bookmarks.py
    history.py
    preferences.py
  storage/
    __init__.py
    config.py
    history.py
    bookmarks.py
    cookies.py
    saved_requests.py
  export/
    __init__.py
    urllib_code.py
    curl.py
  plugins/
    __init__.py
    discovery.py
```

CLI entry point:

```bash
python -m urllib_gui
```

Optional console script:

```text
urllib-gui
```

---

# 24. Public API

Even though this is a GUI app, it should expose reusable components.

## 24.1 Open a URL programmatically

```python
from urllib_gui import open_url

open_url("https://example.com")
```

## 24.2 Embed viewer widget

```python
from urllib_gui.ui.viewer import HypertextViewer

viewer = HypertextViewer(parent)
viewer.set_document(rendered_document)
```

## 24.3 Use renderer separately

```python
from urllib_gui.render.stdlib_html import StdlibHtmlRenderer

renderer = StdlibHtmlRenderer()
doc = renderer.render(html_bytes, base_url="https://example.com")
```

## 24.4 Use client separately

```python
from urllib_gui.client import UrllibClient
from urllib_gui.model import RequestSpec

client = UrllibClient()
response = client.fetch(RequestSpec(url="https://example.com"))
```

---

# 25. Plugin System

## 25.1 Renderer plugins

Renderer plugins should register by entry point eventually, but the stdlib-only core can also support explicit imports.

Future packaging entry point:

```toml
[project.entry-points."urllib_gui.renderers"]
beautifulsoup = "urllib_gui_bs4:BeautifulSoupRenderer"
```

Renderer requirements:

```python
class RenderEngine:
    name: str
    supports_links: bool

    def render(...) -> RenderedDocument:
        ...
```

## 25.2 Optional dependency handling

If an optional renderer is unavailable, it should simply not appear in the renderer picker.

No noisy import errors.

---

# 26. Roadmap

## 26.1 Version 0.1 — Minimal useful browser

Features:

```text
Tkinter main window
URL bar
GET requests through urllib
Tabbed interface
Text viewer
Clickable links
stdlib HTML-to-text renderer
source view
basic history
basic bookmarks
light/dark theme
copy link
open external browser
```

This version proves the concept.

## 26.2 Version 0.2 — Request tools

Features:

```text
expanded request panel
method selector
headers editor
body editor
timeout setting
user-agent setting
copy as urllib code
copy as curl
view request
view response headers
```

This version makes the app meaningfully different from a toy browser.

## 26.3 Version 0.3 — Storage and polish

Features:

```text
SQLite history
SQLite bookmarks
saved requests
cookie jar
preferences dialog
import/export bookmarks
find in page
encoding override
```

## 26.4 Version 0.4 — Better rendering

Features:

```text
improved stdlib HTML renderer
tables
pre/code blocks
blockquote handling
footnote link mode
visited link coloring
optional renderer plugins
```

## 26.5 Version 0.5 — Forms, maybe

Potential features:

```text
display forms as Tkinter controls
submit GET forms
submit POST application/x-www-form-urlencoded forms
basic input text fields
checkboxes
radio buttons
select boxes
submit buttons
```

Still out of scope:

```text
JavaScript-enhanced forms
client-side validation
CSS styling
dynamic DOM mutation
```

---

# 27. Form Posting Roadmap

Forms should be treated as structured request templates.

Given:

```html
<form action="/search" method="GET">
  <input name="q">
  <input type="submit" value="Search">
</form>
```

The renderer may emit:

```python
FormSpec(
    action="https://example.com/search",
    method="GET",
    fields=[
        FormField(name="q", type="text", value=""),
    ],
)
```

The UI can display:

```text
Search form

q: [________________]

[ Submit ]
```

Submitting the form creates a new `RequestSpec`.

This keeps forms aligned with the app’s core model.

---

# 28. Testing Strategy

## 28.1 Renderer tests

Test the stdlib renderer with small HTML fixtures:

```text
paragraphs
headings
links
relative links
nested links, malformed input
lists
pre/code
tables
ignored script/style content
entities
```

## 28.2 Client tests

Use local HTTP servers from the stdlib:

```python
http.server
socketserver
threading
```

Test:

```text
GET
POST
headers
redirects
cookies
timeouts
HTTP errors
binary responses
```

## 28.3 UI smoke tests

Manual or minimal automated tests:

```text
open app
open URL
click link
new tab
close tab
bookmark page
history entry created
switch render engine
```

Tkinter GUI tests should be limited and pragmatic.

---

# 29. Example User Flows

## 29.1 Read a simple web page

1. User enters `example.com`.
2. App normalizes to `https://example.com`.
3. App performs a `GET`.
4. HTML is decoded.
5. `stdlib_html_links` renders text.
6. Links are clickable in the text widget.
7. History records the visit.

## 29.2 Inspect an API response

1. User opens expanded request panel.
2. User selects `GET`.
3. User adds header `Accept: application/json`.
4. User enters URL.
5. Response is displayed as plain text.
6. Headers are available in the headers view.
7. User copies request as `urllib` code.

## 29.3 POST JSON

1. User selects `POST`.
2. User sets body type to `JSON`.
3. User enters:

```json
{"name": "Matt"}
```

4. App adds or suggests:

```text
Content-Type: application/json
```

5. Request is sent through `urllib`.
6. Response is shown.

## 29.4 Follow links text-first

1. User opens a documentation page.
2. Text is displayed without layout noise.
3. Links appear blue and underlined.
4. User Ctrl-clicks a link.
5. New tab opens with resolved absolute URL.

---

# 30. MVP Acceptance Criteria

The MVP is acceptable when:

```text
A user can launch the app.
A user can enter a URL.
The app fetches it with urllib.
HTML appears as readable text.
At least simple links are clickable.
Relative links resolve correctly.
Multiple tabs work.
Back/forward work within a tab.
History records visits.
Bookmarks can be added and reopened.
The user can view response headers.
The user can view source.
The user can copy the current request as Python urllib code.
The app has no required non-stdlib dependencies.
```

---

# 31. Naming

Package name:

```text
urllib_gui
```

Command name:

```text
urllib-gui
```

Window title:

```text
urllib_gui
```

Suggested tagline:

```text
A tiny urllib-shaped text browser for Tkinter.
```

Alternative tagline:

```text
The missing GUI for urllib.request.
```

---

# 32. Guiding Constraints

The project should regularly ask:

```text
Can this be explained in urllib terms?
Can this work without a browser engine?
Can this be useful as text?
Can this be implemented with stdlib first?
Can this degrade gracefully?
```

When the answer is no, the feature probably belongs outside the core.

---

# 33. One-Sentence Product Definition

`urllib_gui` is a Tkinter desktop app that lets users fetch, inspect, read, bookmark, and replay web requests through a friendly graphical interface built around Python’s `urllib`, with simple text-first hypertext support instead of browser rendering.
