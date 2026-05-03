# Deferred work

The current implementation focuses on the shipping-critical MVP: launch the app, open URLs, render readable text, follow
links, manage tabs, record history, add bookmarks, inspect headers/source/request text, and copy a request as Python
`urllib` code.

These pieces are intentionally deferred:

- Async request loading, stop/cancel behavior, and redirect-chain inspection.
- Better HTML fidelity for tables, blockquotes, code/pre formatting, and form rendering.