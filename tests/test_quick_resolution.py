"""Regression tests for the quick-resolution preset writer."""

from types import SimpleNamespace

from guiapi.app import YtDlpGUI


class _Entry:
    def __init__(self, value=''):
        self.value = value

    def delete(self, *_args):
        self.value = ''

    def insert(self, _index, value):
        self.value = value


def _app(selection, translations=None):
    app = YtDlpGUI.__new__(YtDlpGUI)
    app.res_var = SimpleNamespace(get=lambda: selection)
    app.format = _Entry('manual-format')
    app.tr = lambda text: (translations or {}).get(text, text)
    app.autosave_calls = 0
    app.trigger_autosave = lambda: setattr(app, 'autosave_calls', app.autosave_calls + 1)
    return app


def test_720p_quick_selection_overwrites_manual_format():
    app = _app('720p')

    app._on_res_selected()

    assert app.format.value == 'bv*[height<=720]+ba'
    assert app.autosave_calls == 1


def test_localized_quick_selection_uses_same_preset():
    app = _app('720p（快速）', {'720p': '720p（快速）'})

    app._on_res_selected()

    assert app.format.value == 'bv*[height<=720]+ba'


def test_60fps_preset_requires_high_frame_rate():
    app = _app('1080p 60fps')

    app._on_res_selected()

    assert app.format.value == 'bv*[height<=1080][fps>=60]+ba'


def test_combobox_event_path_uses_same_writer():
    app = _app('')
    selector = SimpleNamespace(get=lambda: '480p')

    app._on_res_selected(SimpleNamespace(widget=selector))

    assert app.format.value == 'bv*[height<=480]+ba'
