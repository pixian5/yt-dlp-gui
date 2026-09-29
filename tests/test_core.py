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
