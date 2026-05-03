"""SQLite-backed browsing history."""

from __future__ import annotations

import atexit
import sqlite3
from datetime import datetime
from pathlib import Path

from urllib_gui.model import HistoryEntry
from urllib_gui.storage.config import ensure_config_dir


class HistoryStore:
    """Persist global history entries in SQLite."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or ensure_config_dir() / "history.sqlite3"
        self.connection: sqlite3.Connection | None = sqlite3.connect(self.path)
        self.initialize()
        atexit.register(self.close)

    def add_entry(self, entry: HistoryEntry) -> None:
        """Store a history entry."""
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO history (url, title, method, status, content_type, visited_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.url,
                    entry.title,
                    entry.method,
                    entry.status,
                    entry.content_type,
                    entry.visited_at.isoformat(),
                ),
            )

    def list_entries(self, *, search: str = "", limit: int = 200) -> list[HistoryEntry]:
        """Return stored history entries, newest first."""
        if self.connection is None:
            return []
        sql = """
            SELECT url, title, method, status, content_type, visited_at
            FROM history
        """
        parameters: list[object] = []
        if search:
            sql += " WHERE url LIKE ? OR COALESCE(title, '') LIKE ?"
            pattern = f"%{search}%"
            parameters.extend([pattern, pattern])
        sql += " ORDER BY visited_at DESC LIMIT ?"
        parameters.append(limit)

        rows = self.connection.execute(sql, parameters).fetchall()

        return [
            HistoryEntry(
                url=row[0],
                title=row[1],
                method=row[2],
                status=row[3],
                content_type=row[4],
                visited_at=datetime.fromisoformat(row[5]),
            )
            for row in rows
        ]

    def delete_entry(self, url: str, visited_at: datetime) -> None:
        """Delete a single history entry identified by url + timestamp."""
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute(
                "DELETE FROM history WHERE url = ? AND visited_at = ?",
                (url, visited_at.isoformat()),
            )

    def clear(self) -> None:
        """Delete all history entries."""
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute("DELETE FROM history")

    def initialize(self) -> None:
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    method TEXT NOT NULL,
                    status INTEGER,
                    content_type TEXT,
                    visited_at TEXT NOT NULL
                )
                """)

    def close(self) -> None:
        """Close the store."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            atexit.unregister(self.close)
