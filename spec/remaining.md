# Deferred work

The current implementation focuses on the shipping-critical MVP: launch the app, open URLs, render readable text, follow
links, manage tabs, record history, add bookmarks, inspect headers/source/request text, and copy a request as Python
`urllib` code.

These pieces are intentionally deferred:

- Expanded request drawer with method selector, headers table, body editor, timeout editor, proxy controls, TLS toggle,
  cookie toggle, auth helpers, and request preview form editing.
- Cookie jar inspection and clearing UI.
- `curl` export.
- Saved request scratchpad and reusable request templates.
- Save/open affordances beyond the current basic file dialogs.

- Bookmark import/export, bookmark tags/notes editing, and richer bookmark/history management views.
- Preferences/config editor and persistent theme settings.
- Proxy and authentication UI helpers.

- Async request loading, stop/cancel behavior, and redirect-chain inspection.
- Better HTML fidelity for tables, blockquotes, code/pre formatting, and form rendering.