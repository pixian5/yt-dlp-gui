# Legacy GUI mixins (not wired)

These modules are **not imported** by the live GUI.

Runtime entry points (`guiapi.app.YtDlpGUI`, `python -m guiapi`, `yt-dlp-gui.py`)
use the monolithic implementation in `guiapi/app.py` only.

| Path | Former role |
|------|-------------|
| `downloader.py` | `DownloaderMixin` (command build / download) |
| `config.py` | `ConfigMixin` |
| `utils.py` | `UtilsMixin` |
| `tabs/*` | Tab-builder mixins |

They were kept only as historical/reference code after a partial modularization.
Do **not** edit these expecting runtime changes — fix `guiapi/app.py` instead.
If a future refactor re-adopts mixins, wire them into `YtDlpGUI` deliberately
and delete the duplicated methods from `app.py`.
