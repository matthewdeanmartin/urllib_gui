# urllib_gui

`urllib_gui` is a small desktop client built with Tkinter and Python's standard-library `urllib` stack. It sits somewhere between a text browser, an API scratchpad, and a lightweight request inspector: you can open `http`, `https`, and `file` URLs, adjust request settings, inspect responses, and save the parts you want to keep.

The current app is intentionally modest. It renders HTML into readable text, not a full browser engine. There is no JavaScript execution, no DOM inspector, and no headless automation layer. The value here is a simple GUI around `urllib`, with very little magic and very few dependencies.

## Current feature set

- Open `http`, `https`, and `file` URLs in tabs.
- Navigate with back, forward, reload, and open-in-new-tab flows.
- Render HTML into readable text and follow extracted links inside the app.
- Switch between **Rendered**, **Source**, **Headers**, and **Request** views.
- Use the request drawer to change method, headers, body, timeout, redirects, proxy, TLS verification, cookies, and auth.
- Preview the exact request before sending it.
- Copy the current request as generated `urllib` code or as a `curl` command.
- Save request templates to a scratchpad or export/import them as JSON.
- Save response bodies or rendered text to disk.
- Keep persistent browsing history, bookmarks, saved requests, and preferences.
- Inspect and clear cookies from the active cookie jar.
- Switch between light and dark themes and adjust rendering preferences.

## Installation

## Install from PyPI

With `pipx`:

```bash
pipx install urllib_gui
```

With `pip`:

```bash
pip install urllib_gui
```

## Install from source

```bash
git clone https://github.com/matthewdeanmartin/urllib_gui.git
cd urllib_gui
uv sync --all-extras
```

## Requirements

- Python 3.13 or newer
- A working Tkinter desktop environment
- Network access for `http` and `https` requests

If you are on a minimal Linux install, you may need to install the OS package that provides Tk before launching the app.

## Running the app

Show CLI help:

```bash
urllib_gui --help
```

Launch the GUI:

```bash
urllib_gui
```

Open a URL immediately:

```bash
urllib_gui https://example.com
```

Start in dark mode:

```bash
urllib_gui --theme dark https://example.com
```

You can also launch it as a module:

```bash
python -m urllib_gui https://example.com
```

## How to use it

## Basic browsing

1. Start the app and type a URL into the location bar.
2. Press Enter or click **Go**.
3. Use **Back**, **Forward**, and **Reload** as you would in a simple browser.
4. Open local files with **File -> Open File**.

Supported schemes are currently limited to `http`, `https`, and `file`.

## Request editing

Open **View -> Toggle Request Options** to show the request drawer. That drawer is where the application becomes more than a basic browser tab.

From the drawer you can:

- choose standard HTTP methods or enter a custom one
- add or remove headers, including preset groups
- send raw text, form-urlencoded data, or JSON bodies
- change timeouts
- choose environment proxy settings, no proxy, or a manual proxy URL
- disable TLS verification when needed
- enable or disable cookies
- use Basic auth, Bearer auth, or a custom `Authorization` header
- preview the exact request before sending it

The CLI only launches the GUI and optionally seeds the starting URL and theme. Request customization happens inside the desktop app.

## Response inspection

Use the view selector or the **View** menu to switch between:

- **Rendered**: HTML converted to readable text with clickable links
- **Source**: decoded response body
- **Headers**: status line and response headers
- **Request**: a readable request preview

For HTML responses, the built-in renderers are:

- `stdlib_html_links`
- `stdlib_html_text`
- `plain`
- `html_source`

If compatible third-party packages are installed, additional renderers are discovered automatically.

## Saving and exporting

The app includes a few persistence and export tools:

- **Bookmarks** can be added, edited, searched, tagged, imported, and exported as JSON.
- **History** is stored in SQLite and can be searched or cleared.
- **Request scratchpad** stores named request templates in SQLite.
- **Request files** can be exported to JSON and loaded back later.
- **Copy as urllib Code** generates a Python snippet.
- **Copy as curl** generates a best-effort `curl` equivalent.
- **Save Response Body As...** writes raw bytes to disk.
- **Save Rendered Text As...** writes the rendered text view to disk.

## Preferences and stored data

Preferences are stored under `~/.urllib_gui/`, alongside the app's local data files:

- `config.ini`
- `history.sqlite3`
- `bookmarks.sqlite3`
- `saved_requests.sqlite3`

From the Preferences dialog you can change theme, font settings, link-opening behavior, default timeout, default user agent, cookie behavior, TLS verification, proxy defaults, auth defaults, render engine, and default encoding.

## Keyboard shortcuts

- `Ctrl+L` focus the location bar
- `Ctrl+T` new tab
- `Ctrl+W` close tab
- `Ctrl+R` reload
- `Alt+Left` back
- `Alt+Right` forward
- `Ctrl+D` bookmark current page
- `Ctrl+S` save the current response body
- `Ctrl+F` find in page
- `Ctrl++`, `Ctrl+-`, `Ctrl+0` zoom controls

## Documentation

Project docs live in [`docs/`](https://github.com/matthewdeanmartin/urllib_gui/tree/main/docs/) and are built with MkDocs for Read the Docs. The docs cover installation, day-to-day usage, request workflows, and contributing.

## Contributing

See [CONTRIBUTING.md](https://github.com/matthewdeanmartin/urllib_gui/blob/main/CONTRIBUTING.md) for the local workflow, quality gates, and how CI is wired.

## License

MIT - see [LICENSE](https://github.com/matthewdeanmartin/urllib_gui/blob/main/LICENSE).

## Changelog

See [CHANGELOG.md](https://github.com/matthewdeanmartin/urllib_gui/blob/main/CHANGELOG.md).

## Project Links

- [GitHub](https://github.com/matthewdeanmartin/urllib_gui)
- [PyPI](https://pypi.org/project/urllib-gui/)
- [Documentation](https://urllib_gui.readthedocs.io/en/latest/)
- [Bug Tracker](https://github.com/matthewdeanmartin/urllib_gui/issues)
- [Change Log](https://github.com/matthewdeanmartin/urllib_gui/blob/main/CHANGELOG.md)
