#!/usr/bin/env bash
set -euo pipefail
# Launcher script for the in-repository yt-dlp GUI sidecar.
# Behavior:
# 1) Stops the previous GUI process recorded in run_gui.pid.
# 2) Starts the GUI and writes PID to run_gui.pid; logs appended to run_gui.log.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$DIR/run_gui.pid"
LOGFILE="$DIR/run_gui.log"
CORE_DIR="${YT_DLP_CORE_DIR:-$DIR/..}"
CORE_DIR="$(cd "$CORE_DIR" && pwd)"

# The sidecar never writes into CORE_DIR. Reuse its virtualenv when it exists
# so GUI subprocesses and the original yt-dlp core use identical dependencies.
# Otherwise use a sidecar venv, then fall back to the system Python.
if [ ! -f "$CORE_DIR/yt_dlp/__init__.py" ]; then
  echo "[run_gui] Invalid YT_DLP_CORE_DIR: $CORE_DIR" >&2
  exit 2
fi

# Activate the sidecar venv if present.
if [ -f "$DIR/.venv/bin/activate" ]; then
  # shellcheck disable=SC1090
  . "$DIR/.venv/bin/activate"
fi

# Prefer the core venv, then a sidecar venv, then the system interpreter.
if [ -x "$CORE_DIR/.venv/bin/python" ]; then
  PY="$CORE_DIR/.venv/bin/python"
elif [ -x "$DIR/.venv/bin/python" ]; then
  PY="$DIR/.venv/bin/python"
else
  PY="$(command -v python3 || command -v python)"
fi

echo "[run_gui] Core: $CORE_DIR" | tee -a "$LOGFILE"
echo "[run_gui] Using Python: $PY" | tee -a "$LOGFILE"

# If PID file exists, try to stop the old process gracefully
if [ -f "$PIDFILE" ]; then
  OLD_PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "[run_gui] Stopping previous GUI process $OLD_PID" | tee -a "$LOGFILE"
    kill "$OLD_PID" 2>/dev/null || true
    # wait up to 10s for graceful exit
    for i in $(seq 1 20); do
      if ! kill -0 "$OLD_PID" 2>/dev/null; then
        break
      fi
      sleep 0.5
    done
    if kill -0 "$OLD_PID" 2>/dev/null; then
      echo "[run_gui] Force killing $OLD_PID" | tee -a "$LOGFILE"
      kill -9 "$OLD_PID" 2>/dev/null || true
    fi
  else
    echo "[run_gui] No live process for PID in $PIDFILE, removing stale PID file" | tee -a "$LOGFILE"
  fi
  rm -f "$PIDFILE"
fi

# Deliberately do not fall back to ``pgrep -f`` here. A broad script-name match
# can terminate an unrelated GUI checkout or the current smoke-test shell.
# The PID file above is created exclusively by this sidecar launcher.

# Start GUI
echo "[run_gui] Starting yt-dlp GUI with: $PY" | tee -a "$LOGFILE"
# write this process PID so subsequent runs can stop it
echo "$$" > "$PIDFILE"

exec "$PY" "$DIR/yt-dlp-gui.py" "$@" >>"$LOGFILE" 2>&1
