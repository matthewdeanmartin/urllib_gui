# Quick Start

## Start the app

```bash
urllib_gui
```

Open a page immediately:

```bash
urllib_gui https://example.com
```

## Open something

The main window starts with a location bar and an empty tab.

1. Type a URL or local path.
2. Press Enter or click **Go**.
3. Use **Back**, **Forward**, or **Reload** as needed.

If you type a local filesystem path and it exists, the app turns it into a `file:` URL automatically.

## Use the request drawer

Open **View -> Toggle Request Options** when you need more than a plain GET.

From there you can:

- switch methods
- add or remove headers
- send JSON, raw text, or form-urlencoded bodies
- control redirects and timeouts
- change proxy behavior
- disable TLS verification
- turn cookies on or off
- configure auth

Use the **Preview** tab inside the drawer to inspect the request before you send it.

## Switch views

After a response arrives, switch between:

- **Rendered** for readable text
- **Source** for decoded body text
- **Headers** for status and response headers
- **Request** for the outgoing request preview

For HTML responses, the rendered view is text-first. Links remain clickable, but the app does not execute JavaScript or render a browser-grade layout.

## Save useful things

Common follow-up actions:

- **Bookmarks -> Bookmark This Page**
- **Tools -> Copy as urllib Code**
- **Tools -> Copy as curl**
- **Tools -> Request Scratchpad**
- **Tools -> Save Request to File...**
- **File -> Save Response Body As...**
- **File -> Save Rendered Text As...**

## Handy shortcuts

- `Ctrl+L` focus the location bar
- `Ctrl+T` new tab
- `Ctrl+W` close tab
- `Ctrl+R` reload
- `Alt+Left` / `Alt+Right` back and forward
- `Ctrl+D` bookmark current page
- `Ctrl+F` find in page
- `Ctrl+S` save the response body
- `Ctrl++`, `Ctrl+-`, `Ctrl+0` zoom controls
