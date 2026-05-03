"""Persistent storage for saved/template requests."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from urllib_gui.model import AuthSpec, RequestSpec, utc_now


@dataclass
class SavedRequest:
    """A named, reusable request template."""

    name: str
    spec: RequestSpec
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    tags: list[str] = field(default_factory=list)


def _spec_to_json(spec: RequestSpec) -> str:
    data: dict = {
        "url": spec.url,
        "method": spec.method,
        "headers": list(spec.headers),
        "body": spec.body.decode("latin-1") if spec.body is not None else None,
        "timeout": spec.timeout,
        "follow_redirects": spec.follow_redirects,
        "verify_tls": spec.verify_tls,
        "proxy": spec.proxy,
        "user_agent": spec.user_agent,
        "cookies_enabled": spec.cookies_enabled,
        "auth": None,
    }
    if spec.auth is not None:
        data["auth"] = {
            "scheme": spec.auth.scheme,
            "username": spec.auth.username,
            "password": spec.auth.password,
            "token": spec.auth.token,
            "header_value": spec.auth.header_value,
        }
    return json.dumps(data)


def _json_to_spec(text: str) -> RequestSpec:
    data = json.loads(text)
    auth = None
    if data.get("auth"):
        auth = AuthSpec(**data["auth"])
    body_raw = data.get("body")
    body = body_raw.encode("latin-1") if body_raw is not None else None
    return RequestSpec(
        url=data["url"],
        method=data.get("method", "GET"),
        headers=[tuple(h) for h in data.get("headers", [])],  # type: ignore[misc]
        body=body,
        timeout=data.get("timeout"),
        follow_redirects=data.get("follow_redirects", True),
        verify_tls=data.get("verify_tls", True),
        proxy=data.get("proxy"),
        user_agent=data.get("user_agent"),
        cookies_enabled=data.get("cookies_enabled", True),
        auth=auth,
    )


class SavedRequestStore:
    """SQLite-backed store for named request templates."""

    def __init__(self, db_path: Path | None = None) -> None:
        from urllib_gui.storage.config import ensure_config_dir

        self._path = db_path or (ensure_config_dir() / "saved_requests.sqlite3")
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_requests (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    spec_json TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, saved: SavedRequest) -> None:
        """Insert or replace a saved request by name."""
        now = utc_now().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO saved_requests (name, spec_json, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    spec_json = excluded.spec_json,
                    tags = excluded.tags,
                    updated_at = excluded.updated_at
                """,
                (
                    saved.name,
                    _spec_to_json(saved.spec),
                    json.dumps(saved.tags),
                    saved.created_at.isoformat(),
                    now,
                ),
            )
            conn.commit()

    def list_saved(self, query: str = "") -> list[SavedRequest]:
        """Return saved requests, optionally filtered by name."""
        with self._connect() as conn:
            if query:
                rows = conn.execute(
                    "SELECT * FROM saved_requests WHERE name LIKE ? ORDER BY updated_at DESC",
                    (f"%{query}%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM saved_requests ORDER BY updated_at DESC"
                ).fetchall()
        results = []
        for row in rows:
            try:
                spec = _json_to_spec(row["spec_json"])
                results.append(
                    SavedRequest(
                        name=row["name"],
                        spec=spec,
                        tags=json.loads(row["tags"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            except Exception:  # pylint: disable=broad-except
                continue
        return results

    def delete(self, name: str) -> None:
        """Delete a saved request by name."""
        with self._connect() as conn:
            conn.execute("DELETE FROM saved_requests WHERE name = ?", (name,))
            conn.commit()

    def rename(self, old_name: str, new_name: str) -> None:
        """Rename a saved request."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE saved_requests SET name = ?, updated_at = ? WHERE name = ?",
                (new_name, utc_now().isoformat(), old_name),
            )
            conn.commit()
