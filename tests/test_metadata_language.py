"""Regression tests for playlist title language selection."""

from types import SimpleNamespace
from unittest.mock import patch

from guiapi.app import YtDlpGUI


def _app(metadata_lang='', gui_language='zh'):
    app = YtDlpGUI.__new__(YtDlpGUI)
    app.current_language = gui_language
    app._pending_gui_state = {'metadata_lang': metadata_lang} if metadata_lang else {}
    return app


def test_metadata_language_defaults_to_gui_language():
    assert _app().get_metadata_language() == ('zh-CN', False)
    assert _app(gui_language='ja').get_metadata_language() == ('ja', False)


def test_metadata_language_reads_localized_combobox_value():
    app = _app('Chinese (Simplified) (zh-CN)', gui_language='en')
    assert app.get_metadata_language() == ('zh-CN', True)


def test_playlist_preflight_passes_youtube_language_to_core():
    """The title-fetch command must match the locale used for filenames."""
    app = _app('Chinese (Simplified) (zh-CN)', gui_language='en')
    app._closing = False
    app._parse_cancel = False
    app._parse_generation = 1
    app._parse_running = True
    app._runner_kind = 'parse'
    app._parse_process = None
    app.root = SimpleNamespace(after=lambda *_args: None)
    app.log_message = lambda *_args: None
    app._subprocess_env = lambda: {}

    captured = []

    class FailingProcess:
        returncode = 1

        def communicate(self, timeout):
            return '', 'expected test failure'

    def fake_popen(command, **_kwargs):
        captured.extend(command)
        return FailingProcess()

    with patch('guiapi.app.subprocess.Popen', fake_popen):
        app._parse_playlist_only('https://www.youtube.com/playlist?list=test', {}, 1)

    assert ['--extractor-args', 'youtube:lang=zh-CN'] == captured[
        captured.index('--extractor-args'):captured.index('--extractor-args') + 2]
