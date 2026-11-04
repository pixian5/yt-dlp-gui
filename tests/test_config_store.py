"""Tests for configuration persistence and secrets filtering."""

from guiapi.config_store import (
    SECRET_CONFIG_KEYS,
    filter_secrets,
    load_config_file,
    save_config_file,
)


def test_filter_secrets():
    state = {
        'url_entry': 'https://example.com',
        'format': 'best',
        'password': 'mypassword',
        'video_password': 'vidpass',
        'ap_password': 'appass',
        'client_certificate_password': 'certpass',
        'username': 'normal_user',
    }
    filtered = filter_secrets(state)
    assert 'password' not in filtered
    assert 'video_password' not in filtered
    assert 'ap_password' not in filtered
    assert 'client_certificate_password' not in filtered
    assert filtered['url_entry'] == 'https://example.com'
    assert filtered['username'] == 'normal_user'
    for sec_key in SECRET_CONFIG_KEYS:
        assert sec_key not in filtered


def test_load_config_file_missing(tmp_path):
    missing_file = tmp_path / 'missing.json'
    assert load_config_file(missing_file) == {}


def test_save_and_load_config_roundtrip(tmp_path):
    target = tmp_path / 'test_cfg.json'
    payload = {
        'config_version': 1,
        'language': 'zh',
        'gui_state': {'format': 'bv*+ba', 'proxy': '127.0.0.1:7890'},
    }
    save_config_file(payload, target)
    loaded = load_config_file(target)
    assert loaded == payload


def test_load_corrupted_json(tmp_path):
    corrupt = tmp_path / 'corrupt.json'
    corrupt.write_text('{invalid json syntax...', encoding='utf-8')
    assert load_config_file(corrupt) == {}
