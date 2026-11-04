"""Tests for tab builders and format resolution presets."""

from guiapi import tab_builders
from guiapi.constants import QUICK_RESOLUTION_FORMATS

EXPECTED_TABS = [
    'create_general_tab',
    'create_network_tab',
    'create_geo_restriction_tab',
    'create_video_selection_tab',
    'create_download_tab',
    'create_filesystem_tab',
    'create_video_format_tab',
    'create_subtitle_tab',
    'create_authentication_tab',
    'create_postprocessing_tab',
    'create_thumbnail_tab',
    'create_verbosity_tab',
    'create_workarounds_tab',
    'create_sponsorblock_tab',
    'create_extractor_tab',
    'create_advanced_tab',
]


def test_tab_builders_all_present():
    for tab_name in EXPECTED_TABS:
        assert hasattr(tab_builders, tab_name), f'Missing builder: {tab_name}'
        assert callable(getattr(tab_builders, tab_name))


def test_quick_resolution_formats():
    assert 'Best (Auto)' in QUICK_RESOLUTION_FORMATS
    assert '1080p' in QUICK_RESOLUTION_FORMATS
    assert '4K (2160p)' in QUICK_RESOLUTION_FORMATS
    for name, fmt in QUICK_RESOLUTION_FORMATS.items():
        assert isinstance(name, str) and name
        assert isinstance(fmt, str) and fmt


def test_build_smart_sub_langs():
    class DummyApp:
        pass

    app = DummyApp()
    sub_langs = tab_builders.build_smart_sub_langs(app, 'zh-Hans')
    assert 'zh-Hans' in sub_langs
    assert 'en-zh-Hans' in sub_langs
