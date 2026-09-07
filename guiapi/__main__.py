#!/usr/bin/env python3
"""Module entry point for the live Tk GUI.

Use ``python -m guiapi`` from the repository (preferably inside ``.venv``).
The actual application class lives in :mod:`guiapi.app`; keeping this module
thin avoids a second startup path with different state or environment setup.
"""

from .app import main


if __name__ == '__main__':
    main()
