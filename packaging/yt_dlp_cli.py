#!/usr/bin/env python3
"""Standalone yt-dlp CLI launcher bundled inside the macOS .app.

The GUI cannot spawn ``sys.executable -m yt_dlp`` when frozen, because the
PyInstaller bootloader ignores ``-m``. PyInstaller builds this module into a
separate executable (``yt-dlp-cli``) placed next to the GUI binary in the
bundle; :func:`guiapi.core.core_launcher` returns that executable at runtime.
"""

from yt_dlp import main

if __name__ == '__main__':
    main()
