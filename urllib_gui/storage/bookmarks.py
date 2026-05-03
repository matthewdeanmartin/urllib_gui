"""SQLite-backed bookmarks."""

from __future__ import annotations

import atexit
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from urllib_gui.model import Bookmark
from urllib_gui.storage.config import ensure_config_dir


class BookmarkStore:
    """Persist bookmarks in SQLite."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or ensure_config_dir() / "bookmarks.sqlite3"
        self.connection: sqlite3.Connection | None = sqlite3.connect(self.path)
        self.initialize()
        atexit.register(self.close)

    def add(self, bookmark: Bookmark) -> None:
        """Insert or update a bookmark."""
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO bookmarks (title, url, tags, notes, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    tags = excluded.tags,
                    notes = excluded.notes
                """,
                (
                    bookmark.title,
                    bookmark.url,
                    json.dumps(bookmark.tags),
                    bookmark.notes,
                    bookmark.created_at.isoformat(),
                ),
            )

    def list_bookmarks(self, *, search: str = "") -> list[Bookmark]:
        """Return bookmarks ordered by title."""
        if self.connection is None:
            return []
        sql = """
            SELECT title, url, tags, notes, created_at
            FROM bookmarks
        """
        parameters: list[object] = []
        if search:
            sql += " WHERE title LIKE ? OR url LIKE ? OR COALESCE(notes, '') LIKE ?"
            pattern = f"%{search}%"
            parameters.extend([pattern, pattern, pattern])
        sql += " ORDER BY title COLLATE NOCASE ASC"

        rows = self.connection.execute(sql, parameters).fetchall()

        return [
            Bookmark(
                title=row[0],
                url=row[1],
                tags=json.loads(row[2] or "[]"),
                notes=row[3],
                created_at=datetime.fromisoformat(row[4]),
            )
            for row in rows
        ]

    def remove(self, url: str) -> None:
        """Delete a bookmark by URL."""
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute("DELETE FROM bookmarks WHERE url = ?", (url,))

    def initialize(self) -> None:
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    tags TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """)

    def close(self) -> None:
        """Close the store."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            atexit.unregister(self.close)
