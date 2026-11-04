"""Configuration persistence and security filtering for yt-dlp GUI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILE = os.path.expanduser('~/.yt-dlp-gui-config.json')

# Never persist these authentication fields to disk
SECRET_CONFIG_KEYS: frozenset[str] = frozenset({
    'password',
    'video_password',
    'ap_password',
    'client_certificate_password',
    'twofactor',
})


def filter_secrets(state: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy of state dict with sensitive authentication keys stripped."""
    return {k: v for k, v in state.items() if k not in SECRET_CONFIG_KEYS}


def load_config_file(path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration dictionary from JSON file."""
    config_path = Path(path if path is not None else DEFAULT_CONFIG_FILE)
    if not config_path.is_file():
        return {}
    try:
        with open(config_path, encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config_file(config: dict[str, Any], path: str | Path | None = None) -> None:
    """Save configuration dictionary to JSON file."""
    config_path = Path(path if path is not None else DEFAULT_CONFIG_FILE)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
