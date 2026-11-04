"""Tests for translation dictionaries integrity and completeness."""

from guiapi.translations import TRANSLATIONS

EXPECTED_LANGUAGES = {'zh', 'ru', 'ja', 'ko', 'es', 'fr', 'de'}

ESSENTIAL_KEYS = [
    'Download',
    'Stop',
    'Ready',
    'Language:',
    'Parse Playlist',
    'Open Output Folder',
    'Stopping download...',
    'Stopping playlist parse...',
    'Stopping bulk parse...',
]


def test_translations_supported_languages():
    assert set(TRANSLATIONS.keys()) == EXPECTED_LANGUAGES


def test_translations_entry_types_and_non_empty():
    for lang, dictionary in TRANSLATIONS.items():
        assert isinstance(dictionary, dict), f'Translations for {lang} must be a dict'
        assert len(dictionary) > 50, f'Translations for {lang} must have at least 50 entries'

        for key, val in dictionary.items():
            assert isinstance(key, str), f'Translation key {key!r} in {lang} must be a str'
            assert isinstance(val, str), f'Translation value for {key!r} in {lang} must be a str'
            assert val.strip(), f'Translation for {key!r} in {lang} should not be empty'


def test_translations_essential_ui_keys_in_chinese():
    zh_dict = TRANSLATIONS['zh']
    for key in ESSENTIAL_KEYS:
        assert key in zh_dict, f'Essential key {key!r} missing in zh translations'
        assert zh_dict[key].strip() != '', f'Empty translation for {key!r} in zh'


def test_translations_no_corrupted_newlines_in_short_keys():
    for lang, dictionary in TRANSLATIONS.items():
        for key in dictionary:
            if len(key) < 40:
                assert '\n' not in key, f'Unexpected newline in short translation key {key!r} for {lang}'
