"""Persistent application configuration backed by configparser."""

from __future__ import annotations

import configparser
from pathlib import Path

from urllib_gui.storage.config import ensure_config_dir

_DEFAULTS: dict[str, dict[str, str]] = {
    "network": {
        "timeout": "30",
        "user_agent": "urllib_gui/0.1",
        "cookies_enabled": "true",
        "verify_tls": "true",
        "proxy_mode": "Environment",
        "proxy_url": "",
    },
    "rendering": {
        "default_engine": "stdlib_html_links",
        "default_encoding": "utf-8",
    },
    "ui": {
        "theme": "light",
        "font_family": "TkDefaultFont",
        "font_size": "12",
        "open_links_in_new_tab": "false",
    },
    "auth": {
        "default_scheme": "None",
        "default_username": "",
        "default_token": "",
    },
}


class AppConfig:
    """Read/write application preferences from config.ini."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (ensure_config_dir() / "config.ini")
        self._parser = configparser.ConfigParser()
        self._load()

    def _load(self) -> None:
        for section, values in _DEFAULTS.items():
            if not self._parser.has_section(section):
                self._parser.add_section(section)
            for key, default in values.items():
                if not self._parser.has_option(section, key):
                    self._parser.set(section, key, default)
        if self._path.exists():
            self._parser.read(self._path, encoding="utf-8")
            # Re-apply defaults for any missing keys added in a newer version
            for section, values in _DEFAULTS.items():
                if not self._parser.has_section(section):
                    self._parser.add_section(section)
                for key, default in values.items():
                    if not self._parser.has_option(section, key):
                        self._parser.set(section, key, default)

    def save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as fh:
            self._parser.write(fh)

    def get(self, section: str, key: str) -> str:
        return self._parser.get(section, key)

    def set(self, section: str, key: str, value: str) -> None:
        if not self._parser.has_section(section):
            self._parser.add_section(section)
        self._parser.set(section, key, value)

    def getbool(self, section: str, key: str) -> bool:
        return self._parser.getboolean(section, key)

    def getint(self, section: str, key: str) -> int:
        return self._parser.getint(section, key)

    def getfloat(self, section: str, key: str) -> float:
        return self._parser.getfloat(section, key)

    # Convenience properties for the most-used settings

    @property
    def theme(self) -> str:
        return self.get("ui", "theme")

    @theme.setter
    def theme(self, value: str) -> None:
        self.set("ui", "theme", value)

    @property
    def font_family(self) -> str:
        return self.get("ui", "font_family")

    @font_family.setter
    def font_family(self, value: str) -> None:
        self.set("ui", "font_family", value)

    @property
    def font_size(self) -> int:
        return self.getint("ui", "font_size")

    @font_size.setter
    def font_size(self, value: int) -> None:
        self.set("ui", "font_size", str(value))

    @property
    def default_timeout(self) -> float:
        return self.getfloat("network", "timeout")

    @property
    def default_user_agent(self) -> str:
        return self.get("network", "user_agent")

    @property
    def default_engine(self) -> str:
        return self.get("rendering", "default_engine")

    @property
    def proxy_mode(self) -> str:
        return self.get("network", "proxy_mode")

    @property
    def proxy_url(self) -> str:
        return self.get("network", "proxy_url")

    @property
    def verify_tls(self) -> bool:
        return self.getbool("network", "verify_tls")

    @property
    def cookies_enabled(self) -> bool:
        return self.getbool("network", "cookies_enabled")

    @property
    def open_links_in_new_tab(self) -> bool:
        return self.getbool("ui", "open_links_in_new_tab")
