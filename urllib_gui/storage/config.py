"""Configuration path helpers."""

from __future__ import annotations

from pathlib import Path

CONFIG_DIRECTORY_NAME = ".urllib_gui"


def get_config_dir() -> Path:
    """Return the persistent application config directory."""
    return Path.home() / CONFIG_DIRECTORY_NAME


def ensure_config_dir() -> Path:
    """Create and return the application config directory."""
    path = get_config_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path
