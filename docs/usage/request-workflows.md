# Request Workflows

This page covers the parts of `urllib_gui` that go beyond "type a URL and open it".

## Request options drawer

Open **View -> Toggle Request Options** to expand the drawer below the toolbar. The drawer is organized into tabs.

## Basic

- choose a built-in method or type a custom method
- edit the target URL
- control redirect following
- override the user agent

## Headers

Add, remove, enable, or disable request headers. The presets menu gives you quick starting points for common cases such as:

- browser-ish headers
- urllib-like defaults
- JSON API requests
- plain-text requests
- HTML-only requests
- no-cache headers

## Body

The body editor supports three modes:

- `raw`
- `form-urlencoded`
- `json`

For JSON and form-urlencoded bodies, the drawer also adds the expected `Content-Type` header unless you already supplied one manually.

## Network

The network tab controls:

- timeout
- proxy mode
- TLS certificate verification
- cookie handling

Proxy mode can use:

- environment defaults
- no proxy
- a manually entered proxy URL

## Auth

The auth tab supports:

- no auth
- Basic auth
- Bearer auth
- a custom `Authorization` header value

## Preview

The preview tab shows a readable request summary based on the current drawer state. Use it to confirm method, path, headers, and body before sending the request.

## Working with responses

Once a response has loaded, the app can show:

- rendered text
- source text
- headers
- request preview

The status bar shows the status code, content type, and elapsed time for the current response.

## Renderers

Built-in renderers:

- `stdlib_html_links`
- `stdlib_html_text`
- `plain`
- `html_source`

If optional packages such as `html2text`, `beautifulsoup4`, `markdownify`, or `inscriptis` are installed, `urllib_gui` discovers extra renderers automatically.

## Requests you can save and reuse

## Scratchpad

Use **Tools -> Request Scratchpad** to save named request templates into the local SQLite store. You can search, rename, delete, and load them later.

## Request JSON files

Use:

- **Tools -> Save Request to File...**
- **Tools -> Open Request from File...**

These files are JSON representations of the current request spec, including headers, body, proxy, timeout, TLS, cookies, and auth settings.

## Exporting for other tools

Use:

- **Tools -> Copy as urllib Code**
- **Tools -> Copy as curl**

These generate best-effort equivalents of the current request so you can move from exploratory GUI work into scripts or shell commands.

## Local data and preferences

The app stores local data in `~/.urllib_gui/`:

- `config.ini`
- `history.sqlite3`
- `bookmarks.sqlite3`
- `saved_requests.sqlite3`

From **Preferences** you can change:

- theme
- font family and size
- whether links open in new tabs
- default timeout
- default user agent
- cookie defaults
- TLS verification default
- proxy defaults
- auth defaults
- default renderer
- default encoding
