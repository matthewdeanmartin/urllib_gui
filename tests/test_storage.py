"""Storage tests."""

from datetime import UTC
from pathlib import Path

from urllib_gui.model import Bookmark, HistoryEntry, utc_now
from urllib_gui.storage import BookmarkStore, HistoryStore


def test_history_store_round_trips_entries(tmp_path: Path) -> None:
    """History entries should persist in SQLite."""
    store = HistoryStore(tmp_path / "history.sqlite3")
    try:
        entry = HistoryEntry(
            url="https://example.com",
            title="Example",
            visited_at=utc_now(),
            method="GET",
            status=200,
            content_type="text/html",
        )

        store.add_entry(entry)
        saved = store.list_entries()

        assert len(saved) == 1
        assert saved[0].url == "https://example.com"
        assert saved[0].visited_at.tzinfo == UTC
    finally:
        store.close()


def test_bookmark_store_upserts_by_url(tmp_path: Path) -> None:
    """Bookmarks should be replaced when the URL already exists."""
    store = BookmarkStore(tmp_path / "bookmarks.sqlite3")
    try:
        store.add(Bookmark(title="One", url="https://example.com", created_at=utc_now(), tags=["docs"]))
        store.add(Bookmark(title="Two", url="https://example.com", created_at=utc_now(), tags=["updated"]))

        bookmarks = store.list_bookmarks()

        assert len(bookmarks) == 1
        assert bookmarks[0].title == "Two"
        assert bookmarks[0].tags == ["updated"]
    finally:
        store.close()
