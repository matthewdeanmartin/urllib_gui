"""SQLite-backed bookmarks."""

from __future__ import annotations

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
        self.initialize()

    def add(self, bookmark: Bookmark) -> None:
        """Insert or update a bookmark."""
        with sqlite3.connect(self.path) as connection:
            connection.execute(
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
            connection.commit()

    def list_bookmarks(self, *, search: str = "") -> list[Bookmark]:
        """Return bookmarks ordered by title."""
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
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(sql, parameters).fetchall()
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
        with sqlite3.connect(self.path) as connection:
            connection.execute("DELETE FROM bookmarks WHERE url = ?", (url,))
            connection.commit()

    def initialize(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    tags TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """)
            connection.commit()
