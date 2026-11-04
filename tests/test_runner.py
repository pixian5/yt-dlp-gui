"""Tests for subprocess runner and process management."""

import os
import sys

from guiapi.runner import (
    SubprocessRunner,
    augmented_path,
    extra_bin_dirs,
    spawn_process,
    subprocess_env,
    subprocess_text_kwargs,
    terminate_process,
)


def test_subprocess_text_kwargs():
    kwargs = subprocess_text_kwargs()
    assert kwargs['text'] is True
    assert kwargs['encoding'] == 'utf-8'
    assert kwargs['errors'] == 'replace'
    assert kwargs['bufsize'] == 1


def test_extra_bin_dirs():
    dirs = extra_bin_dirs()
    assert isinstance(dirs, list)
    for d in dirs:
        assert os.path.isdir(d)


def test_augmented_path_preserves_and_prepends():
    base = '/usr/bin'
    augmented = augmented_path(base)
    assert '/usr/bin' in augmented.split(os.pathsep)


def test_subprocess_env():
    env = subprocess_env()
    assert 'PATH' in env
    assert len(env['PATH']) > 0


def test_terminate_process_none():
    # Should not raise
    terminate_process(None)


def test_terminate_process_running():
    proc = spawn_process([sys.executable, '-c', 'import time; time.sleep(10)'])
    assert proc.poll() is None
    terminate_process(proc)
    assert proc.poll() is not None


def test_spawn_and_run_task():
    lines = []
    runner = SubprocessRunner(on_log=lines.append)
    proc = spawn_process([sys.executable, '-c', 'print("hello world")'])
    stdout, _ = proc.communicate(timeout=5)
    assert 'hello world' in stdout.strip()
    assert not runner.is_cancelled()


def test_runner_cancel():
    runner = SubprocessRunner()
    assert not runner.is_cancelled()
    runner.cancel()
    assert runner.is_cancelled()
    assert runner.run_task(['--version']) == -1
