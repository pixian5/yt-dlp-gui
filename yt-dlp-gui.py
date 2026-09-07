#!/usr/bin/env python3
"""
Standalone yt-dlp GUI launcher.

This script launches the graphical user interface for yt-dlp.
It can be executed directly or via:
    python yt-dlp-gui.py
The GUI is a sidecar and starts the original core through ``PYTHONPATH``.
"""

from guiapi import main


if __name__ == '__main__':
    main()
