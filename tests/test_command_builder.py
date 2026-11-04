"""Unit tests for command building and credential sanitization."""

from guiapi.app import YtDlpGUI
from guiapi.core import sanitize_command


class DummyVar:
    def __init__(self, val=''):
        self.val = val

    def get(self, *args):
        return self.val

    def set(self, val):
        self.val = val

    def __bool__(self):
        return bool(self.val)

    def __str__(self):
        return str(self.val)


class DummyText:
    def __init__(self, val=''):
        self.val = val

    def get(self, *args):
        return self.val


class StubYtDlpGUI(YtDlpGUI):
    """Headless stub of YtDlpGUI for command builder testing without Tk."""

    def __init__(self, **overrides):
        self.current_language = overrides.pop('gui_language', 'en')
        self._pending_gui_state = {}
        self._batch_file = overrides.pop('batch_file', '')
        self._batch_file_path = overrides.pop('batch_file_path', '')
        self._batch_urls = overrides.pop('batch_urls', [])
        self.url_entry = DummyVar(overrides.pop('url', 'https://www.youtube.com/watch?v=123'))
        self.raw_args = DummyText(overrides.pop('raw_args', ''))
        self.sb_remove_vars = overrides.pop('sb_remove_vars', {})
        self.sb_mark_vars = overrides.pop('sb_mark_vars', {})

        # Populate explicit overrides
        for k, v in overrides.items():
            if isinstance(v, (DummyVar, DummyText)):
                setattr(self, k, v)
            elif isinstance(v, bool):
                setattr(self, k, DummyVar(v))
            else:
                setattr(self, k, DummyVar(str(v)))

    def ensure_all_tabs_built(self):
        pass

    def get_batch_file_value(self):
        return self._batch_file

    def collect_batch_targets(self, batch_file=''):
        return self._batch_file_path, self._batch_urls

    def __getattr__(self, name):
        # Default fallback for unconfigured flags
        is_bool = any(name.startswith(p) for p in (
            'no_', 'yes_', 'force_', 'embed_', 'write_', 'list_', 'check_',
            'prefer_', 'allow_', 'ignore_', 'abort_', 'keep_', 'add_', 'get_',
            'dump_', 'print_', 'simulate', 'quiet', 'verbose', 'test', 'break_',
            'continue_', 'include_',
        ))
        var = DummyVar(False if is_bool else '')
        setattr(self, name, var)
        return var


# ---------------------------------------------------------------------------
# Tests for sanitize_command (Task 1: Credential Masking)
# ---------------------------------------------------------------------------

def test_sanitize_command_basic_password():
    cmd = ['yt-dlp', '--password', 'supersecret', 'https://example.com']
    clean = sanitize_command(cmd)
    assert clean == ['yt-dlp', '--password', '***', 'https://example.com']


def test_sanitize_command_equal_syntax():
    cmd = ['yt-dlp', '--password=supersecret', '--video-password=vidsecret']
    clean = sanitize_command(cmd)
    assert clean == ['yt-dlp', '--password=***', '--video-password=***']


def test_sanitize_command_all_sensitive_flags():
    cmd = [
        'yt-dlp',
        '--ap-password', 'ap_pass',
        '--twofactor', '123456',
        '-p', 'short_p',
        '--token', 'tok_abc',
        '--client-certificate-password', 'cert_pass',
    ]
    clean = sanitize_command(cmd)
    assert clean == [
        'yt-dlp',
        '--ap-password', '***',
        '--twofactor', '***',
        '-p', '***',
        '--token', '***',
        '--client-certificate-password', '***',
    ]


def test_sanitize_command_proxy_with_credentials():
    cmd = ['yt-dlp', '--proxy', 'http://user:mypassword@proxy.corp.com:8080', 'https://example.com']
    clean = sanitize_command(cmd)
    assert clean == ['yt-dlp', '--proxy', 'http://user:***@proxy.corp.com:8080', 'https://example.com']


def test_sanitize_command_proxy_equal_syntax():
    cmd = ['yt-dlp', '--proxy=socks5://admin:secret123@127.0.0.1:1080']
    clean = sanitize_command(cmd)
    assert clean == ['yt-dlp', '--proxy=socks5://admin:***@127.0.0.1:1080']


def test_sanitize_command_clean_args_untouched():
    cmd = ['yt-dlp', '-f', 'bv*+ba', '--write-subs', '--embed-thumbnail', 'https://example.com']
    clean = sanitize_command(cmd)
    assert clean == cmd


def test_sanitize_command_edge_cases():
    assert sanitize_command([]) == []
    assert sanitize_command(['--password']) == ['--password']


# ---------------------------------------------------------------------------
# Tests for build_command_args (Task 3: Safety Net)
# ---------------------------------------------------------------------------

def test_build_command_args_default():
    app = StubYtDlpGUI(url='https://www.youtube.com/watch?v=default')
    args = app.build_command_args()
    assert '--extractor-args' in args
    assert 'youtube:lang=en' in args
    assert 'https://www.youtube.com/watch?v=default' in args


def test_build_command_args_custom_format():
    app = StubYtDlpGUI(
        format='bv*[height<=1080]+ba/b',
        merge_output_format='mkv',
        check_formats=True,
    )
    args = app.build_command_args()
    assert '-f' in args
    assert args[args.index('-f') + 1] == 'bv*[height<=1080]+ba/b'
    assert '--merge-output-format' in args
    assert args[args.index('--merge-output-format') + 1] == 'mkv'
    assert '--check-formats' in args


def test_build_command_args_audio_extraction():
    app = StubYtDlpGUI(
        extract_audio=True,
        audio_format='mp3',
        audio_quality='0',
    )
    args = app.build_command_args()
    assert '-x' in args
    assert '--audio-format' in args
    assert args[args.index('--audio-format') + 1] == 'mp3'
    assert '--audio-quality' in args
    assert args[args.index('--audio-quality') + 1] == '0'


def test_build_command_args_subtitles():
    app = StubYtDlpGUI(
        write_subs=True,
        sub_langs='en.*,zh.*',
        embed_subs=True,
    )
    args = app.build_command_args()
    assert '--write-subs' in args
    assert '--sub-langs' in args
    assert args[args.index('--sub-langs') + 1] == 'en.*,zh.*'
    assert '--embed-subs' in args


def test_build_command_args_sponsorblock():
    app = StubYtDlpGUI(
        sb_remove_vars={'sponsor': DummyVar(True), 'intro': DummyVar(True)},
        sb_mark_vars={'outro': DummyVar(True)},
    )
    args = app.build_command_args()
    assert '--sponsorblock-remove' in args
    assert args[args.index('--sponsorblock-remove') + 1] == 'sponsor,intro'
    assert '--sponsorblock-mark' in args
    assert args[args.index('--sponsorblock-mark') + 1] == 'outro'


def test_build_command_args_auth_and_sanitization():
    app = StubYtDlpGUI(
        username='myuser',
        password='mypassword',
        twofactor='999888',
    )
    args = app.build_command_args()
    assert '--username' in args
    assert args[args.index('--username') + 1] == 'myuser'
    assert '--password' in args
    assert args[args.index('--password') + 1] == 'mypassword'
    assert '--twofactor' in args
    assert args[args.index('--twofactor') + 1] == '999888'

    # Verify that sanitizing this command masks credentials
    sanitized = sanitize_command(args)
    assert 'mypassword' not in sanitized
    assert '999888' not in sanitized
    assert sanitized[sanitized.index('--password') + 1] == '***'
    assert sanitized[sanitized.index('--twofactor') + 1] == '***'
    assert sanitized[sanitized.index('--username') + 1] == 'myuser'


def test_build_command_args_network_and_proxy():
    app = StubYtDlpGUI(
        proxy='socks5://127.0.0.1:1080',
        socket_timeout='60',
        retries='10',
    )
    args = app.build_command_args()
    assert '--proxy' in args
    assert args[args.index('--proxy') + 1] == 'socks5://127.0.0.1:1080'
    assert '--socket-timeout' in args
    assert args[args.index('--socket-timeout') + 1] == '60'
    assert '--retries' in args
    assert args[args.index('--retries') + 1] == '10'


def test_build_command_args_raw_args():
    app = StubYtDlpGUI(raw_args='--limit-rate 500K --no-mtime')
    args = app.build_command_args()
    assert '--limit-rate' in args
    assert args[args.index('--limit-rate') + 1] == '500K'
    assert '--no-mtime' in args


def test_command_builder_from_plain_dict():
    from guiapi.command_builder import build_command_args_from_app

    config = {
        'url_entry': 'https://www.youtube.com/watch?v=dict_test',
        'format': 'bestvideo+bestaudio',
        'extract_audio': True,
        'audio_format': 'flac',
        'proxy': 'http://127.0.0.1:8888',
        'ignore_errors': True,
        'metadata_lang': 'ja',
    }
    args = build_command_args_from_app(config)
    assert 'https://www.youtube.com/watch?v=dict_test' in args
    assert '-f' in args and args[args.index('-f') + 1] == 'bestvideo+bestaudio'
    assert '-x' in args
    assert '--audio-format' in args and args[args.index('--audio-format') + 1] == 'flac'
    assert '--proxy' in args and args[args.index('--proxy') + 1] == 'http://127.0.0.1:8888'
    assert '--ignore-errors' in args
    assert '--extractor-args' in args and 'youtube:lang=ja' in args


def test_sub_builders_direct():
    from guiapi.command_builder import (
        OptionGetter,
        build_auth_options,
        build_format_options,
        build_general_options,
        parse_raw_args,
    )

    getter = OptionGetter({'ignore_errors': True, 'abort_on_error': True})
    assert build_general_options(getter) == [
        '--ignore-errors',
        '--abort-on-error',
        '--compat-options',
        'no-youtube-unavailable-videos',
    ]

    fmt_getter = OptionGetter({'format': 'bv*', 'video_multistreams': 'yes'})
    assert build_format_options(fmt_getter) == ['-f', 'bv*', '--video-multistreams']

    auth_getter = OptionGetter({'username': 'bob', 'netrc': True})
    assert build_auth_options(auth_getter) == ['--username', 'bob', '--netrc']

    assert parse_raw_args('--geo-bypass --retries 5') == ['--geo-bypass', '--retries', '5']

