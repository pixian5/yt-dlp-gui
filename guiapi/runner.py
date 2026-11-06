"""Subprocess execution and process lifecycle management for yt-dlp GUI.

Isolates child process execution, environment augmentation (ffmpeg/node/deno detection),
process group signaling (cross-platform termination), and line streaming.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess
from collections.abc import Callable
from typing import Any

from guiapi.core import core_env, core_launcher, sanitize_command


def subprocess_text_kwargs() -> dict[str, Any]:
    """Text-mode kwargs that avoid UnicodeDecodeError on non-UTF-8 locales (esp. Windows)."""
    return {
        'text': True,
        'encoding': 'utf-8',
        'errors': 'replace',
        'bufsize': 1,
    }


def extra_bin_dirs() -> list[str]:
    """Common tool directories (Homebrew/local) that may hold node/ffmpeg/deno."""
    candidates = (
        '/opt/homebrew/bin',
        '/usr/local/bin',
        os.path.expanduser('~/.local/bin'),
    )
    return [path for path in candidates if path and os.path.isdir(path)]


def augmented_path(base_path: str | None = None) -> str:
    """Return PATH with existing common tool dirs prepended (no duplicates)."""
    path = base_path if base_path is not None else os.environ.get('PATH', '')
    parts = [p for p in path.split(os.pathsep) if p]
    for directory in reversed(extra_bin_dirs()):
        if directory not in parts:
            parts.insert(0, directory)
    return os.pathsep.join(parts)


def subprocess_env() -> dict[str, str]:
    """Environment for original-core children with tools and PYTHONPATH set."""
    env = core_env()
    env['PATH'] = augmented_path(env.get('PATH', ''))
    return env


def check_runtime_dependencies(timeout: float = 2.0) -> dict[str, dict[str, Any]]:
    """检测 ffmpeg, ffprobe, node, deno 等运行时工具链就绪状态与版本。"""
    tools = ['ffmpeg', 'ffprobe', 'node', 'deno']
    env = subprocess_env()
    path_env = env.get('PATH', '')
    results: dict[str, dict[str, Any]] = {}

    for tool in tools:
        found_path = shutil.which(tool, path=path_env)
        version = ''
        available = bool(found_path)

        if found_path:
            try:
                cmd = [found_path, '-version'] if tool in ('ffmpeg', 'ffprobe') else [found_path, '--version']
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
                if proc.returncode == 0:
                    raw = (proc.stdout or proc.stderr).splitlines()
                    if raw:
                        first_line = raw[0].strip()
                        if tool in ('ffmpeg', 'ffprobe') and 'version' in first_line:
                            parts = first_line.split()
                            if len(parts) >= 3 and parts[1] == 'version':
                                version = parts[2]
                            else:
                                version = first_line
                        else:
                            version = first_line
            except Exception:
                pass

        results[tool] = {
            'available': available,
            'path': found_path or '',
            'version': version,
        }

    return results


def terminate_process(process: subprocess.Popen | None) -> None:
    """Terminate a process and its child processes, then reap it."""
    if process is None:
        return
    try:
        if process.poll() is None:
            if os.name != 'nt':
                with contextlib.suppress(ProcessLookupError, OSError):
                    pgid = os.getpgid(process.pid)
                    if pgid != os.getpgrp():
                        os.killpg(pgid, signal.SIGTERM)
            else:
                with contextlib.suppress(Exception):
                    process.send_signal(signal.CTRL_BREAK_EVENT)
            with contextlib.suppress(ProcessLookupError):
                process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()
                process.wait(timeout=2)
    except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
        pass


def spawn_process(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    stdout: int = subprocess.PIPE,
    stderr: int = subprocess.STDOUT,
) -> subprocess.Popen:
    """Spawn a subprocess in a new process group/session for clean teardown."""
    popen_kwargs: dict[str, Any] = {
        'stdout': stdout,
        'stderr': stderr,
        'env': env if env is not None else subprocess_env(),
        **subprocess_text_kwargs(),
    }
    if os.name == 'nt':
        popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs['start_new_session'] = True
    return subprocess.Popen(cmd, **popen_kwargs)


class SubprocessRunner:
    """Manages sequential execution of command tasks with live output callbacks."""

    def __init__(
        self,
        *,
        on_log: Callable[[str], None] | None = None,
        on_task_start: Callable[[int, int, str], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        line_filter: Callable[[str], str] | None = None,
    ):
        self.on_log = on_log
        self.on_task_start = on_task_start
        self.on_status = on_status
        self.line_filter = line_filter
        self.current_process: subprocess.Popen | None = None
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel current execution and terminate running child."""
        self._cancelled = True
        proc = self.current_process
        self.current_process = None
        if proc is not None:
            terminate_process(proc)

    def is_cancelled(self) -> bool:
        return self._cancelled

    def run_task(self, args: list[str]) -> int:
        """Execute a single set of yt-dlp CLI arguments."""
        if self._cancelled:
            return -1

        full_cmd = [*core_launcher(), '--remote-components', 'ejs:github', *args]
        if self.on_log:
            sanitized = sanitize_command(full_cmd)
            self.on_log('[DEBUG] ' + ' '.join(sanitized))

        proc = spawn_process(full_cmd)
        self.current_process = proc
        output_lines: list[str] = []

        try:
            if proc.stdout:
                for line in proc.stdout:
                    if line:
                        cleaned = line.rstrip()
                        if self.line_filter:
                            cleaned = self.line_filter(cleaned)
                        output_lines.append(cleaned)
                        if self.on_log:
                            self.on_log(cleaned)

            proc.wait()
            return proc.returncode
        finally:
            if self.current_process is proc:
                self.current_process = None
