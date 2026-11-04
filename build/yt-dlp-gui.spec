# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the standalone yt-dlp GUI macOS .app bundle.
#
# Usage (from the GUI virtualenv that also has pyinstaller installed):
#     pyinstaller --noconfirm build/yt-dlp-gui.spec
#
# The resulting bundle is written to dist/yt-dlp-gui.app. See build_app.sh for
# the end-to-end script that also installs the app into /Applications.

import os
import sys
from pathlib import Path

# Locate the yt-dlp core source tree so its package can be bundled as data.
# Priority: explicit YT_DLP_CORE_DIR, then the sibling ../yt-dlp checkout.
_gui_root = Path(SPECPATH).resolve().parent
_core_env = os.environ.get('YT_DLP_CORE_DIR')
_core_candidates = (
    (Path(_core_env).expanduser(),) if _core_env
    else (_gui_root.parent / 'yt-dlp', _gui_root.parent)
)
CORE_DIR = next(
    (p.resolve() for p in _core_candidates if (p / 'yt_dlp' / '__init__.py').is_file()),
    None,
)
if CORE_DIR is None:
    raise SystemExit(
        'yt-dlp core checkout not found. Set YT_DLP_CORE_DIR to a directory '
        'that contains yt_dlp/__init__.py.')

_icon = _gui_root / 'build' / 'icon.icns'
_cli_entry = _gui_root / 'packaging' / 'yt_dlp_cli.py'

# ---- GUI executable -------------------------------------------------------
a = Analysis(
    ['../yt-dlp-gui.py'],
    pathex=[str(_gui_root)],
    binaries=[],
    datas=[(str(CORE_DIR / 'yt_dlp'), 'yt_dlp')],
    hiddenimports=['yt_dlp'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='yt-dlp-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_icon) if _icon.is_file() else None,
)

# ---- yt-dlp CLI helper executable -----------------------------------------
# A frozen GUI cannot spawn ``sys.executable -m yt_dlp`` (the bootloader ignores
# ``-m``), so we build a separate console executable that calls
# ``yt_dlp.main()``. guiapi.core.core_launcher spawns this binary when frozen.
b = Analysis(
    [str(_cli_entry)],
    pathex=[str(_gui_root), str(CORE_DIR)],
    binaries=[],
    datas=[],
    hiddenimports=['yt_dlp'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_b = PYZ(b.pure)

# One-file console executable: bundles its own Python runtime and yt_dlp so it
# runs independently of the GUI bundle. build_app.sh copies the resulting
# dist/yt-dlp-cli into Contents/MacOS/ next to the GUI binary.
cli_exe = EXE(
    pyz_b,
    b.scripts,
    b.binaries,
    b.datas,
    name='yt-dlp-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='yt-dlp-gui',
)
app = BUNDLE(
    coll,
    name='yt-dlp-gui.app',
    icon=str(_icon) if _icon.is_file() else None,
    bundle_identifier='io.github.pixian5.yt-dlp-gui',
    version=os.environ.get('YT_DLP_GUI_VERSION', '0.0.0'),
    info_plist={
        'CFBundleName': 'yt-dlp-gui',
        'CFBundleDisplayName': 'yt-dlp GUI',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
)
