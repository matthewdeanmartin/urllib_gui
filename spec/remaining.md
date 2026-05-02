# Deferred work

The current implementation focuses on the shipping-critical MVP: launch the app, open URLs, render readable text, follow links, manage tabs, record history, add bookmarks, inspect headers/source/request text, and copy a request as Python `urllib` code.

These pieces are intentionally deferred:

- Expanded request drawer with method selector, headers table, body editor, timeout editor, proxy controls, TLS toggle, cookie toggle, auth helpers, and request preview form editing.
- Non-GET request workflows in the UI, including JSON and form posting.
- Bookmark import/export, bookmark tags/notes editing, and richer bookmark/history management views.
- Cookie jar inspection and clearing UI.
- Proxy and authentication UI helpers.
- `curl` export.
- Find-in-page, zoom controls, encoding override, and visited-link styling.
- Preferences/config editor and persistent theme settings.
- Optional third-party renderer plugins and engine discovery.
- Better HTML fidelity for tables, blockquotes, code/pre formatting, and form rendering.
- Save/open affordances beyond the current basic file dialogs.
- Async request loading, stop/cancel behavior, and redirect-chain inspection.
- Saved request scratchpad and reusable request templates.
