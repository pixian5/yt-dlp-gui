"""yt-dlp CLI command builder module.

Decouples GUI state mapping from the Tkinter UI hierarchy.
Translates user configurations, tab controls, and batch settings into
executable yt-dlp arguments.
"""

from __future__ import annotations

import os
import shlex
from collections.abc import Mapping
from typing import Any


class OptionGetter:
    """Universal option extractor supporting App instances, Test stubs, and plain Dicts."""

    def __init__(self, source: Any):
        self.source = source

    def get_str(self, name: str, default: str = '') -> str:
        if isinstance(self.source, Mapping):
            val = self.source.get(name, default)
            if val is None or val is False:
                return default
            return str(val).strip()

        widget = getattr(self.source, name, None)
        if widget is not None:
            if hasattr(widget, 'get'):
                try:
                    val = widget.get()
                    if val is None or val is False:
                        return default
                    return str(val).strip()
                except Exception:
                    pass
            if widget is False:
                return default
            return str(widget).strip()

        if hasattr(self.source, 'get_control_text'):
            return self.source.get_control_text(name, default)
        return default

    def get_bool(self, name: str, default: bool = False) -> bool:
        if isinstance(self.source, Mapping):
            return bool(self.source.get(name, default))

        widget = getattr(self.source, name, None)
        if widget is not None:
            if hasattr(widget, 'get'):
                try:
                    return bool(widget.get())
                except Exception:
                    pass
            return bool(widget)

        if hasattr(self.source, 'get_control_bool'):
            return self.source.get_control_bool(name, default)
        return default

    def get_raw_text(self, name: str = 'raw_args', default: str = '') -> str:
        if isinstance(self.source, Mapping):
            return str(self.source.get(name, default)).strip()

        widget = getattr(self.source, name, None)
        if widget is not None and hasattr(widget, 'get'):
            try:
                # Tk Text widget takes ('1.0', tk.END)
                return widget.get('1.0', 'end').strip()
            except TypeError:
                try:
                    return widget.get().strip()
                except Exception:
                    pass
            except Exception:
                pass
        return default

    def get_sb_cats(self, attr_name: str) -> list[str]:
        if isinstance(self.source, Mapping):
            val = self.source.get(attr_name, {})
            if isinstance(val, (list, tuple, set)):
                return [str(c) for c in val]
            if isinstance(val, Mapping):
                return [str(cat) for cat, active in val.items() if active]
            return []

        vars_dict = getattr(self.source, attr_name, None)
        if isinstance(vars_dict, Mapping):
            selected = []
            for cat, var in vars_dict.items():
                if hasattr(var, 'get'):
                    try:
                        if var.get():
                            selected.append(str(cat))
                    except Exception:
                        pass
                elif bool(var):
                    selected.append(str(cat))
            return selected
        return []


def build_general_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    if getter.get_bool('ignore_errors'):
        args.append('--ignore-errors')
    if getter.get_bool('no_warnings'):
        args.append('--no-warnings')
    if getter.get_bool('abort_on_error'):
        args.append('--abort-on-error')
    if getter.get_bool('no_playlist'):
        args.append('--no-playlist')
    if getter.get_bool('yes_playlist'):
        args.append('--yes-playlist')
    if not getter.get_bool('include_private_videos'):
        args.extend(['--compat-options', 'no-youtube-unavailable-videos'])
    if getter.get_bool('mark_watched'):
        args.append('--mark-watched')
    if getter.get_bool('no_mark_watched'):
        args.append('--no-mark-watched')

    val = getter.get_str('default_search')
    if val:
        args.extend(['--default-search', val])
    val = getter.get_str('config_location')
    if val:
        args.extend(['--config-location', val])
    if getter.get_str('extract_flat') == 'in_playlist':
        args.append('--flat-playlist')
    val = getter.get_str('age_limit')
    if val:
        args.extend(['--age-limit', val])
    val = getter.get_str('download_archive')
    if val:
        args.extend(['--download-archive', val])
    val = getter.get_str('max_downloads')
    if val:
        args.extend(['--max-downloads', val])
    return args


def build_network_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    val = getter.get_str('proxy')
    if val:
        args.extend(['--proxy', val])
    val = getter.get_str('socket_timeout')
    if val:
        args.extend(['--socket-timeout', val])
    val = getter.get_str('source_address')
    if val:
        args.extend(['--source-address', val])
    if getter.get_bool('force_ipv4'):
        args.append('--force-ipv4')
    if getter.get_bool('force_ipv6'):
        args.append('--force-ipv6')
    if getter.get_bool('enable_file_urls'):
        args.append('--enable-file-urls')
    val = getter.get_str('sleep_interval')
    if val:
        args.extend(['--sleep-interval', val])
    val = getter.get_str('max_sleep_interval')
    if val:
        args.extend(['--max-sleep-interval', val])

    sleep_requests_val = getter.get_str('sleep_interval_requests')
    if not sleep_requests_val:
        sleep_requests_val = getter.get_str('sleep_requests')
    if sleep_requests_val:
        args.extend(['--sleep-requests', sleep_requests_val])

    val = getter.get_str('sleep_interval_subtitles')
    if val:
        args.extend(['--sleep-subtitles', val])

    limit_rate_val = getter.get_str('rate_limit')
    if not limit_rate_val:
        limit_rate_val = getter.get_str('limit_rate')
    if limit_rate_val:
        args.extend(['--limit-rate', limit_rate_val])

    val = getter.get_str('throttled_rate')
    if val:
        args.extend(['--throttled-rate', val])
    val = getter.get_str('retries')
    if val:
        args.extend(['--retries', val])
    val = getter.get_str('fragment_retries')
    if val:
        args.extend(['--fragment-retries', val])
    return args


def build_geo_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    val = getter.get_str('geo_verification_proxy')
    if val:
        args.extend(['--geo-verification-proxy', val])
    if getter.get_bool('geo_bypass'):
        args.append('--geo-bypass')
    if getter.get_bool('no_geo_bypass'):
        args.append('--no-geo-bypass')
    val = getter.get_str('geo_bypass_country')
    if val:
        args.extend(['--geo-bypass-country', val])
    val = getter.get_str('geo_bypass_ip_block')
    if val:
        args.extend(['--geo-bypass-ip-block', val])
    return args


def build_video_selection_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    for field in ('playlist_items', 'playlist_start', 'playlist_end', 'match_title',
                  'reject_title', 'min_filesize', 'max_filesize', 'date',
                  'datebefore', 'dateafter', 'min_views', 'max_views', 'match_filter'):
        val = getter.get_str(field)
        if val:
            args.extend([f'--{field.replace("_", "-")}', val])

    if getter.get_bool('break_on_existing'):
        args.append('--break-on-existing')
    if getter.get_bool('break_on_reject'):
        args.append('--break-on-reject')
    if getter.get_bool('no_break_on_existing'):
        args.append('--no-break-on-existing')
    return args


def build_download_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    for field in ('concurrent_fragments', 'buffer_size', 'http_chunk_size',
                  'external_downloader', 'external_downloader_args'):
        val = getter.get_str(field)
        if val:
            args.extend([f'--{field.replace("_", "-")}', val])

    if getter.get_bool('no_resize_buffer'):
        args.append('--no-resize-buffer')
    if getter.get_bool('test'):
        args.append('--test')
    if getter.get_bool('hls_prefer_native'):
        args.append('--hls-prefer-native')
    if getter.get_bool('hls_prefer_ffmpeg'):
        args.append('--hls-prefer-ffmpeg')
    if getter.get_bool('hls_use_mpegts'):
        args.append('--hls-use-mpegts')
    return args


def build_filesystem_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    output_template = getter.get_str('output_template')
    output_dir = getter.get_str('output_dir')
    playlist_subdir = getter.get_bool('playlist_subdir')

    if output_template and playlist_subdir and '%(playlist)s/' not in output_template and '%(playlist)s\\' not in output_template and '%(playlist&' not in output_template:
        output_template = f'%(playlist&{{}}/|)s{output_template}'

    if output_dir and output_template:
        args.extend(['-o', os.path.join(output_dir, output_template)])
    elif output_template:
        args.extend(['-o', output_template])
    elif output_dir:
        args.extend(['-P', output_dir])

    val = getter.get_str('paths')
    if val:
        args.extend(['--paths', val])

    flags = (
        ('restrict_filenames', '--restrict-filenames'),
        ('no_restrict_filenames', '--no-restrict-filenames'),
        ('windows_filenames', '--windows-filenames'),
        ('no_overwrites', '--no-overwrites'),
        ('force_overwrites', '--force-overwrites'),
        ('continue_dl', '--continue'),
        ('no_continue', '--no-continue'),
        ('no_part', '--no-part'),
        ('no_mtime', '--no-mtime'),
        ('write_description', '--write-description'),
        ('write_info_json', '--write-info-json'),
        ('write_annotations', '--write-annotations'),
        ('write_comments', '--write-comments'),
        ('no_cache_dir', '--no-cache-dir'),
        ('rm_cache_dir', '--rm-cache-dir'),
    )
    for attr, flag in flags:
        if getter.get_bool(attr):
            args.append(flag)

    for field in ('load_info_json', 'cache_dir'):
        val = getter.get_str(field)
        if val:
            args.extend([f'--{field.replace("_", "-")}', val])

    return args


def build_format_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    format_value = getter.get_str('format')
    if format_value:
        args.extend(['-f', format_value])

    val = getter.get_str('format_sort')
    if val:
        args.extend(['--format-sort', val])

    if getter.get_bool('prefer_free_formats'):
        args.append('--prefer-free-formats')
    if getter.get_bool('check_formats'):
        args.append('--check-formats')

    val = getter.get_str('merge_output_format')
    if val:
        args.extend(['--merge-output-format', val])

    video_ms = getter.get_str('video_multistreams').lower()
    if video_ms in ('yes', 'true', '1', 'on'):
        args.append('--video-multistreams')
    elif video_ms in ('no', 'false', '0', 'off'):
        args.append('--no-video-multistreams')

    audio_ms = getter.get_str('audio_multistreams').lower()
    if audio_ms in ('yes', 'true', '1', 'on'):
        args.append('--audio-multistreams')
    elif audio_ms in ('no', 'false', '0', 'off'):
        args.append('--no-audio-multistreams')

    return args


def build_subtitle_options(getter: OptionGetter, app_instance: Any = None) -> list[str]:
    args: list[str] = []
    if getter.get_bool('write_subs'):
        args.append('--write-subs')
    if getter.get_bool('write_auto_subs'):
        args.append('--write-auto-subs')
    if getter.get_bool('list_subs'):
        args.append('--list-subs')

    val = getter.get_str('sub_format')
    if val:
        args.extend(['--sub-format', val])

    smart_target_lang = ''
    if app_instance is not None and hasattr(app_instance, 'get_smart_subtitle_lang_code'):
        smart_target_lang = app_instance.get_smart_subtitle_lang_code()
    else:
        smart_target_lang = getter.get_str('smart_subtitle_lang_code')

    if smart_target_lang:
        sub_langs = ''
        if app_instance is not None and hasattr(app_instance, 'build_smart_sub_langs'):
            sub_langs = app_instance.build_smart_sub_langs(smart_target_lang)
        else:
            sub_langs = f'{smart_target_lang}.*'
        args.extend(['--sub-langs', sub_langs])
        if not getter.get_bool('write_auto_subs'):
            args.append('--write-auto-subs')
        if not getter.get_bool('write_subs'):
            args.append('--write-subs')
    else:
        sub_langs_val = getter.get_str('sub_langs')
        if sub_langs_val:
            args.extend(['--sub-langs', sub_langs_val])

    if getter.get_bool('embed_subs'):
        args.append('--embed-subs')
    if getter.get_bool('no_embed_subs'):
        args.append('--no-embed-subs')
    if getter.get_bool('embed_thumbnail'):
        args.append('--embed-thumbnail')
    if getter.get_bool('no_embed_thumbnail'):
        args.append('--no-embed-thumbnail')

    return args


def build_auth_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    fields = (
        'username', 'password', 'twofactor', 'video_password', 'ap_mso',
        'ap_username', 'ap_password', 'client_certificate',
        'client_certificate_key', 'client_certificate_password',
    )
    for field in fields:
        val = getter.get_str(field)
        if val:
            args.extend([f'--{field.replace("_", "-")}', val])

    if getter.get_bool('netrc'):
        args.append('--netrc')
    return args


def build_postprocessing_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    if getter.get_bool('extract_audio'):
        args.append('-x')

    fields = (
        'audio_format', 'audio_quality', 'recode_video', 'remux_video',
        'metadata_from_title', 'parse_metadata', 'ffmpeg_location',
        'postprocessor_args',
    )
    for field in fields:
        val = getter.get_str(field)
        if val:
            args.extend([f'--{field.replace("_", "-")}', val])

    flags = (
        ('keep_video', '--keep-video'),
        ('no_keep_video', '--no-keep-video'),
        ('embed_metadata', '--embed-metadata'),
        ('embed_chapters', '--embed-chapters'),
        ('embed_info_json', '--embed-info-json'),
        ('add_metadata', '--add-metadata'),
    )
    for attr, flag in flags:
        if getter.get_bool(attr):
            args.append(flag)

    return args


def build_thumbnail_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    if getter.get_bool('write_thumbnail'):
        args.append('--write-thumbnail')
    if getter.get_bool('write_all_thumbnails'):
        args.append('--write-all-thumbnails')
    if getter.get_bool('list_thumbnails'):
        args.append('--list-thumbnails')
    val = getter.get_str('convert_thumbnails')
    if val:
        args.extend(['--convert-thumbnails', val])
    return args


def build_verbosity_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    flags = (
        ('quiet', '--quiet'),
        ('verbose', '--verbose'),
        ('simulate', '--simulate'),
        ('skip_download', '--skip-download'),
        ('get_title', '--get-title'),
        ('get_id', '--get-id'),
        ('get_url', '--get-url'),
        ('get_thumbnail', '--get-thumbnail'),
        ('get_description', '--get-description'),
        ('get_duration', '--get-duration'),
        ('get_filename', '--get-filename'),
        ('get_format', '--get-format'),
        ('dump_json', '--dump-json'),
        ('dump_single_json', '--dump-single-json'),
        ('print_json', '--print-json'),
        ('no_progress', '--no-progress'),
        ('console_title', '--console-title'),
    )
    for attr, flag in flags:
        if getter.get_bool(attr):
            args.append(flag)

    val = getter.get_str('progress_template')
    if val:
        args.extend(['--progress-template', val])
    return args


def build_workarounds_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    for field in ('encoding', 'user_agent', 'referer', 'add_header'):
        val = getter.get_str(field)
        if val:
            args.extend([f'--{field.replace("_", "-")}', val])

    flags = (
        ('no_check_certificate', '--no-check-certificate'),
        ('prefer_insecure', '--prefer-insecure'),
        ('bidi_workaround', '--bidi-workaround'),
        ('legacy_server_connect', '--legacy-server-connect'),
    )
    for attr, flag in flags:
        if getter.get_bool(attr):
            args.append(flag)
    return args


def build_sponsorblock_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    selected_remove_cats = getter.get_sb_cats('sb_remove_vars')
    selected_mark_cats = getter.get_sb_cats('sb_mark_vars')

    if getter.get_bool('no_sponsorblock'):
        args.append('--no-sponsorblock')
    else:
        if getter.get_bool('sponsorblock_remove') or selected_remove_cats:
            args.extend(['--sponsorblock-remove', ','.join(selected_remove_cats) if selected_remove_cats else 'default'])
        if getter.get_bool('sponsorblock_mark') or selected_mark_cats:
            args.extend(['--sponsorblock-mark', ','.join(selected_mark_cats) if selected_mark_cats else 'default'])

    val = getter.get_str('sponsorblock_chapter_title')
    if val:
        args.extend(['--sponsorblock-chapter-title', val])
    val = getter.get_str('sponsorblock_api')
    if val:
        args.extend(['--sponsorblock-api', val])
    return args


def build_extractor_options(getter: OptionGetter) -> list[str]:
    args: list[str] = []
    extractor_args: list[str] = []
    user_extractor_args = getter.get_str('extractor_args')
    if user_extractor_args:
        extractor_args.append(user_extractor_args)

    normalized_extractor_args = user_extractor_args.lower().replace(' ', '')
    if 'youtubetab:' not in normalized_extractor_args:
        extractor_args.append('youtubetab:skip=authcheck')

    for extractor_arg in extractor_args:
        args.extend(['--extractor-args', extractor_arg])

    val = getter.get_str('extractor_retries')
    if val:
        args.extend(['--extractor-retries', val])

    if getter.get_bool('allow_dynamic_mpd'):
        args.append('--allow-dynamic-mpd')
    if getter.get_bool('ignore_dynamic_mpd'):
        args.append('--ignore-dynamic-mpd')
    if getter.get_bool('hls_split_discontinuity'):
        args.append('--hls-split-discontinuity')

    val = getter.get_str('cookies_from_browser')
    if val:
        args.extend(['--cookies-from-browser', val])
    val = getter.get_str('cookies')
    if val:
        args.extend(['--cookies', val])

    return args


def parse_raw_args(raw_text: str) -> list[str]:
    if not raw_text:
        return []
    try:
        return shlex.split(raw_text, posix=(os.name != 'nt'))
    except ValueError:
        return raw_text.split()


def build_command_args_from_app(app: Any) -> list[str]:
    """Build full command args by reading from YtDlpGUI instance."""
    if hasattr(app, 'ensure_all_tabs_built'):
        app.ensure_all_tabs_built()

    getter = OptionGetter(app)
    args: list[str] = []

    # Metadata language & Accept-Language headers
    if hasattr(app, 'get_metadata_language'):
        lang_to_use, _metadata_lang_selected = app.get_metadata_language()
    else:
        lang_to_use = getter.get_str('metadata_lang', 'en')

    args.extend(['--extractor-args', f'youtube:lang={lang_to_use}'])
    args.extend(['--add-header', f'Accept-Language:{lang_to_use},zh;q=0.9,en-US;q=0.8,en;q=0.7'])

    # URL or batch file
    url = getter.get_str('url_entry')
    batch_file = app.get_batch_file_value() if hasattr(app, 'get_batch_file_value') else getter.get_str('batch_file')
    if hasattr(app, 'collect_batch_targets'):
        batch_file_path, batch_urls = app.collect_batch_targets(batch_file=batch_file)
    else:
        batch_file_path, batch_urls = '', []

    args.extend(build_general_options(getter))
    args.extend(build_network_options(getter))
    args.extend(build_geo_options(getter))
    args.extend(build_video_selection_options(getter))
    args.extend(build_download_options(getter))
    args.extend(build_filesystem_options(getter))
    args.extend(build_format_options(getter))
    args.extend(build_subtitle_options(getter, app_instance=app))
    args.extend(build_auth_options(getter))
    args.extend(build_postprocessing_options(getter))
    args.extend(build_thumbnail_options(getter))
    args.extend(build_verbosity_options(getter))
    args.extend(build_workarounds_options(getter))
    args.extend(build_sponsorblock_options(getter))
    args.extend(build_extractor_options(getter))

    raw_args_text = getter.get_raw_text('raw_args')
    if raw_args_text:
        args.extend(parse_raw_args(raw_args_text))

    # Target resolution: Batch targets win over top URL
    if batch_file_path or batch_urls:
        combined_urls: list[str] = []
        if batch_file_path and os.path.isfile(batch_file_path):
            try:
                if hasattr(app, 'read_batch_file_urls'):
                    combined_urls.extend(app.read_batch_file_urls(batch_file_path))
                else:
                    with open(batch_file_path, encoding='utf-8') as f:
                        combined_urls.extend(line.strip() for line in f if line.strip() and not line.startswith('#'))
            except Exception as e:
                if hasattr(app, 'log_message') and hasattr(app, 'translate_concat'):
                    app.log_message(app.translate_concat('Error reading batch file: ', str(e)))
                if not batch_urls:
                    args.extend(['-a', batch_file_path])
        elif batch_file_path and not batch_urls:
            args.extend(['-a', batch_file_path])

        combined_urls.extend(batch_urls)
        if hasattr(app, 'dedupe_preserve_order'):
            combined_urls = app.dedupe_preserve_order(combined_urls)
        else:
            combined_urls = list(dict.fromkeys(combined_urls))

        if combined_urls:
            if len(combined_urls) == 1 and not batch_file_path:
                args.append(combined_urls[0])
            else:
                try:
                    if hasattr(app, 'create_temp_batch_file'):
                        args.extend(['-a', app.create_temp_batch_file(combined_urls)])
                    else:
                        args.extend(['-a', batch_file_path] if batch_file_path else combined_urls)
                except Exception as e:
                    if hasattr(app, 'log_message') and hasattr(app, 'translate_concat'):
                        app.log_message(app.translate_concat('Error creating temporary batch file: ', str(e)))
                    if batch_file_path:
                        args.extend(['-a', batch_file_path])
                    elif combined_urls:
                        args.append(combined_urls[0])
        elif batch_file_path:
            args.extend(['-a', batch_file_path])
    elif url:
        args.append(url)

    return args
