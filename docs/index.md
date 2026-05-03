# urllib_gui

`urllib_gui` is a small Tkinter desktop client built around Python's standard-library `urllib` stack. It is useful when you want a lightweight GUI for opening URLs, inspecting responses, trying request variations, and exporting what you just sent.

It is intentionally not a full browser engine. HTML is rendered into readable text, links can be followed, and response details are easy to inspect, but there is no JavaScript execution or CSS layout engine.

## What the app does today

- opens `http`, `https`, and `file` URLs
- works in tabs
- keeps per-tab back and forward history
- renders HTML into readable text
- exposes source, headers, and request preview views
- lets you edit request method, headers, body, timeout, proxy, TLS, cookies, and auth
- copies the current request as Python `urllib` code or `curl`
- stores bookmarks, history, preferences, cookies, and saved requests

## What the app is good for

- reading HTML pages in a text-first way
- reproducing a request from a GUI instead of hand-writing it each time
- checking headers, redirects, and content types
- saving repeatable request templates
- exporting a request as code you can paste into a script

## What it does not try to be

- a full graphical browser
- a JavaScript-capable test client
- a browser devtools replacement
- a multi-command CLI tool

The CLI is deliberately small: it launches the desktop app, optionally opens a starting URL, and optionally chooses the initial theme.

## Feature summary

## Navigation and viewing

- location bar with URL normalization
- new tab, close tab, reload, back, and forward
- open links in the same tab or a new tab
- open the current page externally
- save raw response bytes or rendered text

## Request controls

- methods: `GET`, `HEAD`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`, or custom
- editable headers with presets
- raw, JSON, or form-urlencoded request bodies
- timeout control
- redirect handling
- environment, disabled, or manual proxy configuration
- TLS verification toggle
- cookie enable/disable
- Basic, Bearer, or custom header auth

## Persistence and export

- bookmarks with tags, notes, import, and export
- browsing history in SQLite
- saved request scratchpad in SQLite
- request export/import as JSON
- copy current request as `curl`
- copy current request as Python `urllib` code

## Appearance and rendering

- light and dark themes
- font controls
- find in page
- zoom in, zoom out, reset zoom
- built-in renderers for text, HTML text, HTML links, and source views
- optional third-party renderer discovery when supported packages are installed

## Next steps

- See [Installation](installation.md) to get started.
- See [Quick Start](usage/quickstart.md) for the normal day-to-day flow.
- See [Request Workflows](usage/request-workflows.md) for the advanced controls.
