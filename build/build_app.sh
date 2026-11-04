#!/usr/bin/env bash
set -euo pipefail
# Reproducible macOS .app build for the standalone yt-dlp GUI.
#
# Steps:
#   1) Locate the yt-dlp core checkout (sibling ../yt-dlp or YT_DLP_CORE_DIR).
#   2) Build dist/yt-dlp-gui.app with PyInstaller from build/yt-dlp-gui.spec.
#   3) Optionally install it into /Applications (--install) after ad-hoc
#      re-signing so Gatekeeper accepts the locally built bundle.
#
# Requirements: run inside the GUI virtualenv that has pyinstaller installed.
#   source .venv/bin/activate && ./build/build_app.sh --install

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC="$DIR/build/yt-dlp-gui.spec"
DIST="$DIR/dist"
INSTALL=0
if [ "${1:-}" = "--install" ]; then
  INSTALL=1
fi

cd "$DIR"

# Resolve the yt-dlp core checkout the same way the spec does, for early feedback.
if [ -z "${YT_DLP_CORE_DIR:-}" ]; then
  if [ -f "$DIR/../yt-dlp/yt_dlp/__init__.py" ]; then
    export YT_DLP_CORE_DIR="$DIR/../yt-dlp"
  elif [ -f "$DIR/yt_dlp/__init__.py" ]; then
    export YT_DLP_CORE_DIR="$DIR"
  else
    echo "[build_app] yt-dlp core checkout not found." >&2
    echo "[build_app] Set YT_DLP_CORE_DIR to a directory containing yt_dlp/__init__.py." >&2
    exit 2
  fi
fi
CORE_DIR="$(cd "$YT_DLP_CORE_DIR" && pwd)"
echo "[build_app] Core: $CORE_DIR"

PY="${PYTHON:-$DIR/.venv/bin/python}"
if ! "$PY" -c 'import PyInstaller' >/dev/null 2>&1; then
  echo "[build_app] pyinstaller not found in $PY. Run: $PY -m pip install 'pyinstaller~=6.21'" >&2
  exit 2
fi

VERSION="$(cat "$DIR/VERSION")"
export YT_DLP_GUI_VERSION="$VERSION"
echo "[build_app] GUI version: $VERSION"

"$PY" -m PyInstaller --noconfirm --clean \
  --distpath "$DIST" --workpath "$DIR/build/.work" \
  "$SPEC"

APP="$DIST/yt-dlp-gui.app"
if [ ! -d "$APP" ]; then
  echo "[build_app] Expected bundle not found: $APP" >&2
  exit 1
fi

# Place the standalone yt-dlp CLI helper next to the GUI executable so
# guiapi.core.core_launcher can spawn it when the GUI runs frozen.
if [ -f "$DIST/yt-dlp-cli" ]; then
  echo "[build_app] Copying yt-dlp-cli helper into the bundle"
  cp "$DIST/yt-dlp-cli" "$APP/Contents/MacOS/yt-dlp-cli"
  chmod +x "$APP/Contents/MacOS/yt-dlp-cli"
else
  echo "[build_app] WARNING: dist/yt-dlp-cli not found; frozen GUI cannot call the core." >&2
fi

# Ad-hoc sign the whole bundle. A locally built app is unsigned, and macOS
# refuses to launch it from /Applications without at least an ad-hoc signature.
echo "[build_app] Ad-hoc signing $APP"
codesign --force --deep --sign - "$APP"

if [ "$INSTALL" -eq 1 ]; then
  DEST="/Applications/yt-dlp-gui.app"
  echo "[build_app] Installing to $DEST"
  if [ -e "$DEST" ] || [ -L "$DEST" ]; then
    osascript -e "tell application \"yt-dlp-gui\" to quit" >/dev/null 2>&1 || true
    rm -rf "$DEST"
  fi
  ditto "$APP" "$DEST"
  echo "[build_app] Installed. Launch with: open -a yt-dlp-gui"
fi

echo "[build_app] Done: $APP"
