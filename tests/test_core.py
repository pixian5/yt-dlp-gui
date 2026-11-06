from pathlib import Path

import pytest

from guiapi import core


def _make_core(path: Path) -> Path:
    package = path / 'yt_dlp'
    package.mkdir(parents=True)
    (package / '__init__.py').write_text('__version__ = "test"\n', encoding='utf-8')
    return path


def test_core_dir_uses_sibling_checkout(monkeypatch, tmp_path):
    gui_root = tmp_path / 'yt-dlp-gui'
    gui_root.mkdir()
    expected = _make_core(tmp_path / 'yt-dlp')
    monkeypatch.setattr(core, '_GUI_ROOT', gui_root)
    monkeypatch.delenv('YT_DLP_CORE_DIR', raising=False)

    assert core.core_dir() == expected


def test_core_dir_keeps_legacy_nested_layout(monkeypatch, tmp_path):
    expected = _make_core(tmp_path / 'yt-dlp')
    (expected / 'gui').mkdir()
    monkeypatch.setattr(core, '_GUI_ROOT', expected / 'gui')
    monkeypatch.delenv('YT_DLP_CORE_DIR', raising=False)

    assert core.core_dir() == expected


def test_core_dir_honors_explicit_checkout(monkeypatch, tmp_path):
    expected = _make_core(tmp_path / 'custom-core')
    monkeypatch.setenv('YT_DLP_CORE_DIR', str(expected))

    assert core.core_dir() == expected


def test_core_dir_rejects_invalid_explicit_checkout(monkeypatch, tmp_path):
    monkeypatch.setenv('YT_DLP_CORE_DIR', str(tmp_path / 'missing-core'))

    with pytest.raises(RuntimeError, match='YT_DLP_CORE_DIR'):
        core.core_dir()


def test_find_core_checkout_returns_none_when_missing(monkeypatch, tmp_path):
    empty_gui = tmp_path / 'isolated-gui'
    empty_gui.mkdir()
    monkeypatch.setattr(core, '_GUI_ROOT', empty_gui)
    monkeypatch.delenv('YT_DLP_CORE_DIR', raising=False)

    assert core.find_core_checkout() is None


def test_core_launcher_honors_explicit_executable(monkeypatch, tmp_path):
    fake_exe = tmp_path / 'custom-yt-dlp'
    fake_exe.write_text('#!/bin/sh\necho "test"\n', encoding='utf-8')
    monkeypatch.setenv('YT_DLP_EXECUTABLE', str(fake_exe))

    assert core.core_launcher() == [str(fake_exe)]


def test_core_launcher_rejects_missing_explicit_executable(monkeypatch, tmp_path):
    monkeypatch.setenv('YT_DLP_EXECUTABLE', str(tmp_path / 'nonexistent-bin'))

    with pytest.raises(RuntimeError, match='Configured YT_DLP_EXECUTABLE not found'):
        core.core_launcher()


def test_core_launcher_system_binary_fallback(monkeypatch, tmp_path):
    empty_gui = tmp_path / 'empty-gui'
    empty_gui.mkdir()
    monkeypatch.setattr(core, '_GUI_ROOT', empty_gui)
    monkeypatch.delenv('YT_DLP_CORE_DIR', raising=False)
    monkeypatch.delenv('YT_DLP_EXECUTABLE', raising=False)

    monkeypatch.setattr(core.shutil, 'which', lambda name: '/fake/bin/yt-dlp' if name == 'yt-dlp' else None)

    launcher = core.core_launcher()
    assert launcher == ['/fake/bin/yt-dlp']


def test_core_env_with_explicit_executable(monkeypatch, tmp_path):
    fake_exe = tmp_path / 'custom-yt-dlp'
    fake_exe.write_text('', encoding='utf-8')
    monkeypatch.setenv('YT_DLP_EXECUTABLE', str(fake_exe))
    monkeypatch.delenv('PYTHONPATH', raising=False)

    env = core.core_env()
    assert 'PYTHONPATH' not in env


def test_probe_core_info_executable_mode(monkeypatch, tmp_path):
    fake_exe = tmp_path / 'custom-yt-dlp'
    fake_exe.write_text('', encoding='utf-8')
    monkeypatch.setenv('YT_DLP_EXECUTABLE', str(fake_exe))

    class DummyProc:
        returncode = 0
        stdout = '2026.01.01\n'

    monkeypatch.setattr(core.subprocess, 'run', lambda *args, **kwargs: DummyProc())

    info = core.probe_core_info()
    assert info['version'] == '2026.01.01'
    assert info['mode'] == 'executable'
    assert info['launcher'] == [str(fake_exe)]
    assert info['location'] == str(fake_exe)


def test_sanitize_command():
    cmd = [
        'yt-dlp',
        '--password', 'supersecret123',
        '-u', 'myuser',
        '--video-password', 'vidsecret',
        '--token', 'tok_abc999',
        '--proxy', 'http://admin:pass456@proxy.corp:8080',
        'https://example.com/watch?v=123',
    ]
    sanitized = core.sanitize_command(cmd)

    # Secrets must not appear in plaintext
    assert 'supersecret123' not in sanitized
    assert 'vidsecret' not in sanitized
    assert 'tok_abc999' not in sanitized
    assert 'pass456' not in ' '.join(sanitized)

    # Redactions must be present in argument list
    assert sanitized[1:3] == ['--password', '***']
    assert sanitized[5:7] == ['--video-password', '***']
    assert sanitized[7:9] == ['--token', '***']
    assert 'http://admin:***@proxy.corp:8080' in sanitized

    # Non-secrets must be preserved
    assert sanitized[3:5] == ['-u', 'myuser']
    assert sanitized[-1] == 'https://example.com/watch?v=123'


