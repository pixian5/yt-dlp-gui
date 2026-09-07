"""Locate the unmodified yt-dlp core for the in-repository GUI sidecar.

The GUI is intentionally a sidecar project: it never imports from or writes
into the core checkout until a child process is launched. Set
``YT_DLP_CORE_DIR`` to select another checkout; otherwise the parent of this
``gui/`` directory is used.
"""

from __future__ import annotations

import os
from pathlib import Path


_GUI_ROOT = Path(__file__).resolve().parent.parent


def core_dir() -> Path:
    """Return the configured core directory after validating its package."""
    configured = os.environ.get('YT_DLP_CORE_DIR')
    # The sidecar lives at ``<core checkout>/gui`` by default. An explicit
    # YT_DLP_CORE_DIR remains available for another checkout or CI workspace.
    candidate = Path(configured).expanduser() if configured else _GUI_ROOT.parent
    candidate = candidate.resolve()
    if not (candidate / 'yt_dlp' / '__init__.py').is_file():
        raise RuntimeError(
            'yt-dlp core checkout not found. Set YT_DLP_CORE_DIR to a directory '
            'that contains yt_dlp/__init__.py.')
    return candidate


def core_env() -> dict[str, str]:
    """Return child environment that imports yt-dlp only from the core checkout."""
    env = os.environ.copy()
    core = str(core_dir())
    existing = env.get('PYTHONPATH', '')
    env['PYTHONPATH'] = core if not existing else os.pathsep.join((core, existing))
    return env
