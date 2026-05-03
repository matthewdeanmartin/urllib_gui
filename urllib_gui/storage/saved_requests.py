"""Persistent storage for saved/template requests."""

from __future__ import annotations

import atexit
import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from urllib_gui.model import AuthSpec, RequestSpec, utc_now
from urllib_gui.storage.config import ensure_config_dir


@dataclass
class SavedRequest:
    """A named, reusable request template."""

    name: str
    spec: RequestSpec
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    tags: list[str] = field(default_factory=list)


def spec_to_json(spec: RequestSpec) -> str:
    """Serialize a request spec to JSON for persistent storage."""
    data: dict[str, object] = {
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


def json_to_spec(text: str) -> RequestSpec:
    """Deserialize a request spec from persisted JSON."""
    loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("Saved request payload must be a JSON object.")

    auth = None
    auth_raw = loaded.get("auth")
    if auth_raw is not None:
        if not isinstance(auth_raw, dict):
            raise ValueError("Saved auth payload must be a JSON object.")
        auth = AuthSpec(
            scheme=str(auth_raw.get("scheme", "")),
            username=_optional_string(auth_raw.get("username")),
            password=_optional_string(auth_raw.get("password")),
            token=_optional_string(auth_raw.get("token")),
            header_value=_optional_string(auth_raw.get("header_value")),
        )

    headers = list(parse_headers(loaded.get("headers", [])))
    url = loaded.get("url")
    if not isinstance(url, str):
        raise ValueError("Saved request payload is missing a string URL.")
    body_raw = loaded.get("body")
    if body_raw is not None and not isinstance(body_raw, str):
        raise ValueError("Saved request body must be a string or null.")
    body = body_raw.encode("latin-1") if body_raw is not None else None
    return RequestSpec(
        url=url,
        method=str(loaded.get("method", "GET")),
        headers=headers,
        body=body,
        timeout=parse_timeout(loaded.get("timeout")),
        follow_redirects=bool(loaded.get("follow_redirects", True)),
        verify_tls=bool(loaded.get("verify_tls", True)),
        proxy=_optional_string(loaded.get("proxy")),
        user_agent=_optional_string(loaded.get("user_agent")),
        cookies_enabled=bool(loaded.get("cookies_enabled", True)),
        auth=auth,
    )


def _optional_string(value: object) -> str | None:
    """Normalize an optional string value loaded from JSON."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise ValueError("Expected a string or null value.")


def parse_timeout(value: object) -> float | None:
    """Normalize an optional timeout value loaded from JSON."""
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    raise ValueError("Timeout must be numeric or null.")


def parse_headers(value: object) -> Iterable[tuple[str, str]]:
    """Yield normalized header pairs from a JSON value."""
    if not isinstance(value, list):
        raise ValueError("Headers must be a list of name/value pairs.")
    for header in value:
        if not isinstance(header, list | tuple) or len(header) != 2:
            raise ValueError("Each header must contain exactly two items.")
        name, item_value = header
        if not isinstance(name, str) or not isinstance(item_value, str):
            raise ValueError("Header names and values must be strings.")
        yield name, item_value


class SavedRequestStore:
    """SQLite-backed store for named request templates."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or (ensure_config_dir() / "saved_requests.sqlite3")
        self.connection: sqlite3.Connection | None = sqlite3.connect(self._path)
        self.connection.row_factory = sqlite3.Row
        self.initialize()
        atexit.register(self.close)

    def initialize(self) -> None:
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS saved_requests (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    spec_json TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)

    def save(self, saved: SavedRequest) -> None:
        """Insert or replace a saved request by name."""
        if self.connection is None:
            return
        now = utc_now().isoformat()
        with self.connection:
            self.connection.execute(
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
                    spec_to_json(saved.spec),
                    json.dumps(saved.tags),
                    saved.created_at.isoformat(),
                    now,
                ),
            )

    def list_saved(self, query: str = "") -> list[SavedRequest]:
        """Return saved requests, optionally filtered by name."""
        if self.connection is None:
            return []
        if query:
            rows = self.connection.execute(
                "SELECT * FROM saved_requests WHERE name LIKE ? ORDER BY updated_at DESC",
                (f"%{query}%",),
            ).fetchall()
        else:
            rows = self.connection.execute("SELECT * FROM saved_requests ORDER BY updated_at DESC").fetchall()

        results = []
        for row in rows:
            try:
                spec = json_to_spec(row["spec_json"])
                tags_raw = json.loads(row["tags"])
                if not isinstance(tags_raw, list) or not all(isinstance(tag, str) for tag in tags_raw):
                    continue
                created_at = datetime.fromisoformat(row["created_at"])
                updated_at = datetime.fromisoformat(row["updated_at"])
            except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
            results.append(
                SavedRequest(
                    name=row["name"],
                    spec=spec,
                    tags=tags_raw,
                    created_at=created_at,
                    updated_at=updated_at,
                )
            )
        return results

    def delete(self, name: str) -> None:
        """Delete a saved request by name."""
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute("DELETE FROM saved_requests WHERE name = ?", (name,))

    def rename(self, old_name: str, new_name: str) -> None:
        """Rename a saved request."""
        if self.connection is None:
            return
        with self.connection:
            self.connection.execute(
                "UPDATE saved_requests SET name = ?, updated_at = ? WHERE name = ?",
                (new_name, utc_now().isoformat(), old_name),
            )

    def close(self) -> None:
        """Close the store."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            atexit.unregister(self.close)
