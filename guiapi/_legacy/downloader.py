"""Download execution logic"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import atexit
import contextlib
import json
import os
import signal
import subprocess
import sys
import threading
import tempfile
import tkinter as tk
from tkinter import messagebox

if TYPE_CHECKING:
    pass


class DownloaderMixin:
    """Mixin for download execution. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    # Using __getattr__ pattern to allow dynamic attribute access
    if TYPE_CHECKING:
        # Core methods and attributes
        tr: Any
        translate_concat: Any
        status_var: Any
        progress_var: Any
        console: Any
        download_btn: Any
        _translatable_widgets: Any
        url_entry: Any
        batch_file_entry: Any
        output_dir: Any
        playlist_parsed_url: Any
        playlist_tree: Any
        vis_to_orig: Any
        current_playlist_metadata_title: Any
        playlist_subdir: Any
        ensure_all_tabs_built: Any
        root: Any
        _download_process: Any
        _temp_files: Any
        url_var: Any
        save_config: Any
        current_language: Any
        # All GUI control variables
        metadata_lang: Any
        ignore_errors: Any
        no_warnings: Any
        abort_on_error: Any
        no_playlist: Any
        yes_playlist: Any
        include_private_videos: Any
        mark_watched: Any
        no_mark_watched: Any
        default_search: Any
        config_location: Any
        extract_flat: Any
        age_limit: Any
        download_archive: Any
        max_downloads: Any
        proxy: Any
        socket_timeout: Any
        source_address: Any
        force_ipv4: Any
        force_ipv6: Any
        enable_file_urls: Any
        sleep_interval: Any
        max_sleep_interval: Any
        sleep_interval_requests: Any
        sleep_interval_subtitles: Any
        rate_limit: Any
        throttled_rate: Any
        retries: Any
        fragment_retries: Any
        geo_verification_proxy: Any
        geo_bypass: Any
        no_geo_bypass: Any
        geo_bypass_country: Any
        geo_bypass_ip_block: Any
        playlist_items: Any
        playlist_start: Any
        playlist_end: Any
        match_title: Any
        reject_title: Any
        min_filesize: Any
        max_filesize: Any
        date: Any
        datebefore: Any
        dateafter: Any
        min_views: Any
        max_views: Any
        match_filter: Any
        break_on_existing: Any
        break_on_reject: Any
        no_break_on_existing: Any
        concurrent_fragments: Any
        buffer_size: Any
        http_chunk_size: Any
        external_downloader: Any
        external_downloader_args: Any
        no_resize_buffer: Any
        test: Any
        hls_prefer_native: Any
        hls_prefer_ffmpeg: Any
        hls_use_mpegts: Any
        output_template: Any
        paths: Any
        restrict_filenames: Any
        no_restrict_filenames: Any
        windows_filenames: Any
        no_overwrites: Any
        force_overwrites: Any
        continue_dl: Any
        no_continue: Any
        no_part: Any
        no_mtime: Any
        write_description: Any
        write_info_json: Any
        write_annotations: Any
        write_comments: Any
        load_info_json: Any
        cache_dir: Any
        no_cache_dir: Any
        rm_cache_dir: Any
        format: Any
        format_sort: Any
        prefer_free_formats: Any
        check_formats: Any
        merge_output_format: Any
        video_multistreams: Any
        audio_multistreams: Any
        write_subs: Any
        write_auto_subs: Any
        list_subs: Any
        sub_format: Any
        sub_langs: Any
        embed_subs: Any
        no_embed_subs: Any
        embed_thumbnail: Any
        no_embed_thumbnail: Any
        username: Any
        password: Any
        twofactor: Any
        netrc: Any
        video_password: Any
        ap_mso: Any
        ap_username: Any
        ap_password: Any
        client_certificate: Any
        client_certificate_key: Any
        client_certificate_password: Any
        extract_audio: Any
        audio_format: Any
        audio_quality: Any
        recode_video: Any
        remux_video: Any
        keep_video: Any
        no_keep_video: Any
        embed_metadata: Any
        embed_chapters: Any
        embed_info_json: Any
        add_metadata: Any
        metadata_from_title: Any
        parse_metadata: Any
        ffmpeg_location: Any
        postprocessor_args: Any
        write_thumbnail: Any
        write_all_thumbnails: Any
        list_thumbnails: Any
        convert_thumbnails: Any
        quiet: Any
        verbose: Any
        simulate: Any
        skip_download: Any
        get_title: Any
        get_id: Any
        get_url: Any
        get_thumbnail: Any
        get_description: Any
        get_duration: Any
        get_filename: Any
        get_format: Any
        dump_json: Any
        dump_single_json: Any
        print_json: Any
        no_progress: Any
        console_title: Any
        progress_template: Any
        encoding: Any
        no_check_certificate: Any
        prefer_insecure: Any
        user_agent: Any
        referer: Any
        add_header: Any
        bidi_workaround: Any
        sleep_requests: Any
        legacy_server_connect: Any
        sponsorblock_mark: Any
        sponsorblock_remove: Any
        sponsorblock_chapter_title: Any
        sponsorblock_api: Any
        no_sponsorblock: Any
        sb_remove_vars: Any
        sb_mark_vars: Any
        extractor_args: Any
        extractor_retries: Any
        allow_dynamic_mpd: Any
        ignore_dynamic_mpd: Any
        hls_split_discontinuity: Any
        cookies_from_browser: Any
        cookies: Any
        raw_args: Any
        generated_cmd: Any
        log_queue: Any
        limit_rate: Any
        notebook: Any
        playlist_tab_frame: Any
        playlist_entries_data: Any
        playlist_exclude_private_var: Any
        playlist_reverse_var: Any

    def build_command_args(self):
        """Build yt-dlp command arguments from GUI settings"""
        self.ensure_all_tabs_built()
        args = []

        # Map GUI internal language codes to metadata language codes
        lang_map = {
            'zh': 'zh-CN',
            'en': 'en',
            'ru': 'ru',
            'ja': 'ja',
            'ko': 'ko',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
        }
        gui_lang_code = getattr(self, 'current_language', 'zh')
        lang_to_use = lang_map.get(gui_lang_code, 'zh-CN')

        if hasattr(self, 'metadata_lang') and self.metadata_lang.get() and self.metadata_lang.get() != self.tr('Default (Auto)'):
            lang_to_use = self.metadata_lang.get().split('(')[-1].split(')')[0]

        args.extend(['--extractor-args', f'youtube:lang={lang_to_use}'])
        # SHOTGUN APPROACH: Inject HTTP header to force server response language
        args.extend(['--add-header', f'Accept-Language:{lang_to_use},zh;q=0.9,en-US;q=0.8,en;q=0.7'])

        # URL or batch file
        url = self.url_entry.get().strip()
        batch_file = self.batch_file_entry.get().strip()

        # General options
        if self.ignore_errors.get():
            args.append('--ignore-errors')
        if self.no_warnings.get():
            args.append('--no-warnings')
        if self.abort_on_error.get():
            args.append('--abort-on-error')
        if self.no_playlist.get():
            args.append('--no-playlist')
        if self.yes_playlist.get():
            args.append('--yes-playlist')
        if not self.include_private_videos.get():
            args.extend(['--compat-options', 'no-youtube-unavailable-videos'])
        if self.mark_watched.get():
            args.append('--mark-watched')
        if self.no_mark_watched.get():
            args.append('--no-mark-watched')

        if self.default_search.get():
            args.extend(['--default-search', self.default_search.get()])
        if self.config_location.get():
            args.extend(['--config-location', self.config_location.get()])
        if self.extract_flat.get():
            args.extend(['--flat-playlist', self.extract_flat.get()])
        if self.age_limit.get():
            args.extend(['--age-limit', self.age_limit.get()])
        if self.download_archive.get():
            args.extend(['--download-archive', self.download_archive.get()])
        if self.max_downloads.get():
            args.extend(['--max-downloads', self.max_downloads.get()])

        # Network options
        if self.proxy.get():
            args.extend(['--proxy', self.proxy.get()])
        if self.socket_timeout.get():
            args.extend(['--socket-timeout', self.socket_timeout.get()])
        if self.source_address.get():
            args.extend(['--source-address', self.source_address.get()])
        if self.force_ipv4.get():
            args.append('--force-ipv4')
        if self.force_ipv6.get():
            args.append('--force-ipv6')
        if self.enable_file_urls.get():
            args.append('--enable-file-urls')
        if self.sleep_interval.get():
            args.extend(['--sleep-interval', self.sleep_interval.get()])
        if self.max_sleep_interval.get():
            args.extend(['--max-sleep-interval', self.max_sleep_interval.get()])
        if self.sleep_interval_requests.get():
            args.extend(['--sleep-requests', self.sleep_interval_requests.get()])
        if self.sleep_interval_subtitles.get():
            args.extend(['--sleep-subtitles', self.sleep_interval_subtitles.get()])
        if self.rate_limit.get():
            args.extend(['--limit-rate', self.rate_limit.get()])
        if self.throttled_rate.get():
            args.extend(['--throttled-rate', self.throttled_rate.get()])
        if self.retries.get():
            args.extend(['--retries', self.retries.get()])
        if self.fragment_retries.get():
            args.extend(['--fragment-retries', self.fragment_retries.get()])

        # Geo-restriction
        if self.geo_verification_proxy.get():
            args.extend(['--geo-verification-proxy', self.geo_verification_proxy.get()])
        if self.geo_bypass.get():
            args.append('--geo-bypass')
        if self.no_geo_bypass.get():
            args.append('--no-geo-bypass')
        if self.geo_bypass_country.get():
            args.extend(['--geo-bypass-country', self.geo_bypass_country.get()])
        if self.geo_bypass_ip_block.get():
            args.extend(['--geo-bypass-ip-block', self.geo_bypass_ip_block.get()])

        # Video selection
        if self.playlist_items.get():
            args.extend(['--playlist-items', self.playlist_items.get()])
        if self.playlist_start.get():
            args.extend(['--playlist-start', self.playlist_start.get()])
        if self.playlist_end.get():
            args.extend(['--playlist-end', self.playlist_end.get()])
        if self.match_title.get():
            args.extend(['--match-title', self.match_title.get()])
        if self.reject_title.get():
            args.extend(['--reject-title', self.reject_title.get()])
        if self.min_filesize.get():
            args.extend(['--min-filesize', self.min_filesize.get()])
        if self.max_filesize.get():
            args.extend(['--max-filesize', self.max_filesize.get()])
        if self.date.get():
            args.extend(['--date', self.date.get()])
        if self.datebefore.get():
            args.extend(['--datebefore', self.datebefore.get()])
        if self.dateafter.get():
            args.extend(['--dateafter', self.dateafter.get()])
        if self.min_views.get():
            args.extend(['--min-views', self.min_views.get()])
        if self.max_views.get():
            args.extend(['--max-views', self.max_views.get()])
        if self.match_filter.get():
            args.extend(['--match-filter', self.match_filter.get()])
        if self.break_on_existing.get():
            args.append('--break-on-existing')
        if self.break_on_reject.get():
            args.append('--break-on-reject')
        if self.no_break_on_existing.get():
            args.append('--no-break-on-existing')

        # Download options
        if self.concurrent_fragments.get():
            args.extend(['--concurrent-fragments', self.concurrent_fragments.get()])
        if self.limit_rate.get():
            args.extend(['--limit-rate', self.limit_rate.get()])
        if self.buffer_size.get():
            args.extend(['--buffer-size', self.buffer_size.get()])
        if self.http_chunk_size.get():
            args.extend(['--http-chunk-size', self.http_chunk_size.get()])
        if self.no_resize_buffer.get():
            args.append('--no-resize-buffer')
        if self.test.get():
            args.append('--test')
        if self.external_downloader.get():
            args.extend(['--external-downloader', self.external_downloader.get()])
        if self.external_downloader_args.get():
            args.extend(['--external-downloader-args', self.external_downloader_args.get()])
        if self.hls_prefer_native.get():
            args.append('--hls-prefer-native')
        if self.hls_prefer_ffmpeg.get():
            args.append('--hls-prefer-ffmpeg')
        if self.hls_use_mpegts.get():
            args.append('--hls-use-mpegts')

        # Filesystem options
        output_template = self.output_template.get()
        output_dir = self.output_dir.get()
        if output_template and self.playlist_subdir.get() and '%(playlist' not in output_template:
            # Use conditional template: creates subfolder only when playlist field is truthy (actual playlists).
            # Single videos have playlist=None, so no subfolder is created for them.
            output_template = '%(playlist&{}/|)s' + output_template
        if output_dir and output_template:
            args.extend(['-o', os.path.join(output_dir, output_template)])
        elif output_template:
            args.extend(['-o', output_template])
        elif output_dir:
            args.extend(['-P', output_dir])

        if self.paths.get():
            args.extend(['--paths', self.paths.get()])
        if self.restrict_filenames.get():
            args.append('--restrict-filenames')
        if self.no_restrict_filenames.get():
            args.append('--no-restrict-filenames')
        if self.windows_filenames.get():
            args.append('--windows-filenames')
        if self.no_overwrites.get():
            args.append('--no-overwrites')
        if self.force_overwrites.get():
            args.append('--force-overwrites')
        if self.continue_dl.get():
            args.append('--continue')
        if self.no_continue.get():
            args.append('--no-continue')
        if self.no_part.get():
            args.append('--no-part')
        if self.no_mtime.get():
            args.append('--no-mtime')
        if self.write_description.get():
            args.append('--write-description')
        if self.write_info_json.get():
            args.append('--write-info-json')
        if self.write_annotations.get():
            args.append('--write-annotations')
        if self.write_comments.get():
            args.append('--write-comments')
        if self.load_info_json.get():
            args.extend(['--load-info-json', self.load_info_json.get()])
        if self.cache_dir.get():
            args.extend(['--cache-dir', self.cache_dir.get()])
        if self.no_cache_dir.get():
            args.append('--no-cache-dir')
        if self.rm_cache_dir.get():
            args.append('--rm-cache-dir')

        # Video format options
        if self.format.get():
            args.extend(['-f', self.format.get()])
        if self.format_sort.get():
            args.extend(['--format-sort', self.format_sort.get()])
        if self.prefer_free_formats.get():
            args.append('--prefer-free-formats')
        if self.check_formats.get():
            args.append('--check-formats')
        if self.merge_output_format.get():
            args.extend(['--merge-output-format', self.merge_output_format.get()])
        if self.video_multistreams.get():
            args.extend(['--video-multistreams', self.video_multistreams.get()])
        if self.audio_multistreams.get():
            args.extend(['--audio-multistreams', self.audio_multistreams.get()])

        # Subtitle options
        if self.write_subs.get():
            args.append('--write-subs')
        if self.write_auto_subs.get():
            args.append('--write-auto-subs')
        if self.list_subs.get():
            args.append('--list-subs')
        if self.sub_format.get():
            args.extend(['--sub-format', self.sub_format.get()])
        if self.sub_langs.get():
            args.extend(['--sub-langs', self.sub_langs.get()])
        if self.embed_subs.get():
            args.append('--embed-subs')
        if self.no_embed_subs.get():
            args.append('--no-embed-subs')
        if self.embed_thumbnail.get():
            args.append('--embed-thumbnail')
        if self.no_embed_thumbnail.get():
            args.append('--no-embed-thumbnail')

        # Authentication options
        if self.username.get():
            args.extend(['--username', self.username.get()])
        if self.password.get():
            args.extend(['--password', self.password.get()])
        if self.twofactor.get():
            args.extend(['--twofactor', self.twofactor.get()])
        if self.netrc.get():
            args.append('--netrc')
        if self.video_password.get():
            args.extend(['--video-password', self.video_password.get()])
        if self.ap_mso.get():
            args.extend(['--ap-mso', self.ap_mso.get()])
        if self.ap_username.get():
            args.extend(['--ap-username', self.ap_username.get()])
        if self.ap_password.get():
            args.extend(['--ap-password', self.ap_password.get()])
        if self.client_certificate.get():
            args.extend(['--client-certificate', self.client_certificate.get()])
        if self.client_certificate_key.get():
            args.extend(['--client-certificate-key', self.client_certificate_key.get()])
        if self.client_certificate_password.get():
            args.extend(['--client-certificate-password', self.client_certificate_password.get()])

        # Post-processing options
        if self.extract_audio.get():
            args.append('-x')
        if self.audio_format.get():
            args.extend(['--audio-format', self.audio_format.get()])
        if self.audio_quality.get():
            args.extend(['--audio-quality', self.audio_quality.get()])
        if self.recode_video.get():
            args.extend(['--recode-video', self.recode_video.get()])
        if self.remux_video.get():
            args.extend(['--remux-video', self.remux_video.get()])
        if self.keep_video.get():
            args.append('--keep-video')
        if self.no_keep_video.get():
            args.append('--no-keep-video')
        if self.embed_metadata.get():
            args.append('--embed-metadata')
        if self.embed_chapters.get():
            args.append('--embed-chapters')
        if self.embed_info_json.get():
            args.append('--embed-info-json')
        if self.add_metadata.get():
            args.append('--add-metadata')
        if self.metadata_from_title.get():
            args.extend(['--metadata-from-title', self.metadata_from_title.get()])
        if self.parse_metadata.get():
            args.extend(['--parse-metadata', self.parse_metadata.get()])
        if self.ffmpeg_location.get():
            args.extend(['--ffmpeg-location', self.ffmpeg_location.get()])
        if self.postprocessor_args.get():
            args.extend(['--postprocessor-args', self.postprocessor_args.get()])

        # Thumbnail options
        if self.write_thumbnail.get():
            args.append('--write-thumbnail')
        if self.write_all_thumbnails.get():
            args.append('--write-all-thumbnails')
        if self.list_thumbnails.get():
            args.append('--list-thumbnails')
        if self.convert_thumbnails.get():
            args.extend(['--convert-thumbnails', self.convert_thumbnails.get()])

        # Verbosity options
        if self.quiet.get():
            args.append('--quiet')
        if self.verbose.get():
            args.append('--verbose')
        if self.simulate.get():
            args.append('--simulate')
        if self.skip_download.get():
            args.append('--skip-download')
        if self.get_title.get():
            args.append('--get-title')
        if self.get_id.get():
            args.append('--get-id')
        if self.get_url.get():
            args.append('--get-url')
        if self.get_thumbnail.get():
            args.append('--get-thumbnail')
        if self.get_description.get():
            args.append('--get-description')
        if self.get_duration.get():
            args.append('--get-duration')
        if self.get_filename.get():
            args.append('--get-filename')
        if self.get_format.get():
            args.append('--get-format')
        if self.dump_json.get():
            args.append('--dump-json')
        if self.dump_single_json.get():
            args.append('--dump-single-json')
        if self.print_json.get():
            args.append('--print-json')
        if self.no_progress.get():
            args.append('--no-progress')
        if self.console_title.get():
            args.append('--console-title')
        if self.progress_template.get():
            args.extend(['--progress-template', self.progress_template.get()])

        # Workarounds
        if self.encoding.get():
            args.extend(['--encoding', self.encoding.get()])
        if self.no_check_certificate.get():
            args.append('--no-check-certificate')
        if self.prefer_insecure.get():
            args.append('--prefer-insecure')
        if self.user_agent.get():
            args.extend(['--user-agent', self.user_agent.get()])
        if self.referer.get():
            args.extend(['--referer', self.referer.get()])
        if self.add_header.get():
            args.extend(['--add-header', self.add_header.get()])
        if self.bidi_workaround.get():
            args.append('--bidi-workaround')
        if self.sleep_requests.get():
            args.extend(['--sleep-requests', self.sleep_requests.get()])
        if self.legacy_server_connect.get():
            args.append('--legacy-server-connect')

        # SponsorBlock options
        if self.sponsorblock_mark.get():
            args.append('--sponsorblock-mark')
        if self.sponsorblock_remove.get():
            args.append('--sponsorblock-remove')

        # Collect categories from checkboxes
        selected_remove_cats = [cat for cat, var in self.sb_remove_vars.items() if var.get()]
        if selected_remove_cats:
            args.extend(['--sponsorblock-remove', ','.join(selected_remove_cats)])

        selected_mark_cats = [cat for cat, var in self.sb_mark_vars.items() if var.get()]
        if selected_mark_cats:
            args.extend(['--sponsorblock-mark', ','.join(selected_mark_cats)])

        if self.sponsorblock_chapter_title.get():
            args.extend(['--sponsorblock-chapter-title', self.sponsorblock_chapter_title.get()])
        if self.no_sponsorblock.get():
            args.append('--no-sponsorblock')
        if self.sponsorblock_api.get():
            args.extend(['--sponsorblock-api', self.sponsorblock_api.get()])

        # Extractor options
        extractor_args = []
        if hasattr(self, 'metadata_lang') and self.metadata_lang.get() and self.metadata_lang.get() != self.tr('Default (Auto)'):
            extractor_args.append(f'youtube:lang={self.metadata_lang.get()}')

        if self.extractor_args.get():
            extractor_args.append(self.extractor_args.get())

        if extractor_args:
            args.extend(['--extractor-args', '; '.join(extractor_args)])

        if self.extractor_retries.get():
            args.extend(['--extractor-retries', self.extractor_retries.get()])
        if self.allow_dynamic_mpd.get():
            args.append('--allow-dynamic-mpd')
        if self.ignore_dynamic_mpd.get():
            args.append('--ignore-dynamic-mpd')
        if self.hls_split_discontinuity.get():
            args.append('--hls-split-discontinuity')
        if self.cookies_from_browser.get():
            args.extend(['--cookies-from-browser', self.cookies_from_browser.get()])
        if self.cookies.get():
            args.extend(['--cookies', self.cookies.get()])

        # Raw arguments
        raw_args_text = self.raw_args.get('1.0', tk.END).strip()
        if raw_args_text:
            import shlex
            try:
                raw_args_list = shlex.split(raw_args_text)
                args.extend(raw_args_list)
            except ValueError:
                # If shlex fails, try splitting by whitespace
                args.extend(raw_args_text.split())

        # Batch file or URL
        if batch_file:
            if batch_file.startswith('http') and '\n' not in batch_file:
                # Single URL in batch field
                args.append(batch_file)
            elif '\n' in batch_file or (not os.path.exists(batch_file) and batch_file.startswith('http')):
                # Multi-line URLs or non-existent path that looks like URL/list
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
                        tf.write(batch_file)
                        temp_path = tf.name
                    args.extend(['-a', temp_path])
                    # Register for cleanup
                    if not hasattr(self, '_temp_batch_files'):
                        self._temp_batch_files = []
                        atexit.register(self._cleanup_temp_files)
                    self._temp_batch_files.append(temp_path)
                except Exception as e:
                    self.log_message(f'Error creating temporary batch file: {e}')
                    args.extend(['-a', batch_file])  # Fallback
            else:
                args.extend(['-a', batch_file])
        elif url:
            args.append(url)

        return args

    def _cleanup_temp_files(self):
        if hasattr(self, '_temp_batch_files'):
            for f in self._temp_batch_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
            self._temp_batch_files.clear()

    def generate_command(self):
        """Generate and display the yt-dlp command"""
        args = self.build_command_args()
        cmd = [sys.executable, '-m', 'yt_dlp', *args]
        cmd_str = ' '.join(f'"{arg}"' if ' ' in arg else arg for arg in cmd)

        self.generated_cmd.config(state=tk.NORMAL)
        self.generated_cmd.delete('1.0', tk.END)
        self.generated_cmd.insert('1.0', cmd_str)
        self.generated_cmd.config(state=tk.DISABLED)

    def copy_command(self):
        """Copy generated command to clipboard"""
        self.generate_command()
        cmd_text = self.generated_cmd.get('1.0', tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd_text)
        self.log_message('Command copied to clipboard!')

    def run_ytdlp(self, tasks):
        """Run a list of yt-dlp tasks (args sets) sequentially"""
        try:
            total = len(tasks)
            for i, (idx, args) in enumerate(tasks):
                self.log_message(self.translate_concat(f'[{i + 1}/{total}] Download Task: Index ', idx))
                self.root.after(0, lambda: self.status_var.set(f'{self.tr("Downloading")} {i + 1}/{total}'))

                full_cmd = [sys.executable, '-m', 'yt_dlp', '--remote-components', 'ejs:github', *args]

                popen_kwargs = {
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.STDOUT,
                    'universal_newlines': True,
                    'bufsize': 1,
                }
                if os.name == 'nt':
                    popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    popen_kwargs['start_new_session'] = True
                self.current_process = subprocess.Popen(full_cmd, **popen_kwargs)
                process = self.current_process

                if process.stdout:
                    for line in process.stdout:
                        if line:
                            self.log_message(line.rstrip())

                process.wait()

                if process.returncode != 0 and process.returncode not in (15, -15):
                    self.log_message(self.translate_concat('Task failed with code ', process.returncode))
                    if 'n challenge solving failed' in ''.join(self.console.get('1.0', tk.END)):
                        self.log_message('\n[!] 提示：检测到 JavaScript 运行环境缺失。')
                        self.log_message("[!] 请在终端运行 'brew install node' 以修复此下载报错。")
                    # We continue even if one fails

                if not hasattr(self, 'current_process') or self.current_process is None:
                    # User likely clicked Stop
                    break

            self.log_message(self.tr('All tasks processed.'))
            self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))

        except Exception as e:
            self.log_message(self.translate_concat('ERROR in runner: ', str(e)))
            self.root.after(0, lambda: self.status_var.set(self.tr('Error')))
        finally:
            self.current_process = None
            self.root.after(0, self._restore_download_button)

    def _restore_download_button(self):
        if hasattr(self, 'download_btn'):
            # 恢复为绿色
            def _restore():
                self.download_btn.config(text=self.tr('Download'), background='#28a745', bg='#28a745')
                self.download_btn.update()
            self.after(10, _restore)
            self._translatable_widgets[self.download_btn] = 'Download'

    def on_download_btn_click(self):
        if hasattr(self, 'current_process') and self.current_process:
            self.stop_download()
        else:
            self.start_download()

    def stop_download(self):
        if hasattr(self, 'current_process') and self.current_process:
            p = self.current_process
            self.current_process = None  # Signal to stop loop
            self.log_message(self.tr('Stopping download...'))

            try:
                # Kill the entire process group (including child processes like ffmpeg)
                if os.name != 'nt':
                    with contextlib.suppress(ProcessLookupError, OSError):
                        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                with contextlib.suppress(ProcessLookupError):
                    p.terminate()
                    p.kill()
            except Exception as e:
                self.log_message(f'[DEBUG] Stop error: {e}')

            # Popup for cleanup
            msg = self.tr('Download stopped. Would you like to delete partially downloaded files?')
            if messagebox.askyesno(self.tr('Stop'), msg):
                self.cleanup_partial_files()
        else:
            self.log_message(self.tr('No download currently running.'))

    def cleanup_partial_files(self):
        """Scan output directory and remove .part, .ytdl and temporary fragment files."""
        output_dir = self.output_dir.get().strip()
        if not output_dir or not os.path.exists(output_dir):
            return

        count = 0
        self.log_message(self.tr('Cleaning up partial files...'))
        try:
            for filename in os.listdir(output_dir):
                # yt-dlp partial files usually end with .part, .ytdl
                # or have fragments like .f137.part
                if filename.endswith(('.part', '.ytdl')) or ('.f' in filename and '.part' in filename):
                    file_path = os.path.join(output_dir, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            self.log_message(f'Failed to remove {filename}: {e}')
            self.log_message(f'Cleanup finished. Removed {count} files.')
        except Exception as e:
            self.log_message(f'Error during cleanup: {e}')

    def start_download(self):
        """Start download in a separate thread"""
        self.log_message('[DEBUG] start_download called')
        url = self.url_entry.get().strip()
        self.log_message(f'[DEBUG] url={url!r}')
        try:
            base_args = self.build_command_args()
            self.log_message(f'[DEBUG] base_args count={len(base_args) if base_args else 0}')
        except Exception as e:
            import traceback
            self.log_message(f'[DEBUG] build_command_args CRASHED: {e}')
            self.log_message(traceback.format_exc())
            self._restore_download_button()
            return

        if not base_args or (not url and not self.batch_file_entry.get().strip()):
            self.log_message('[DEBUG] No URL or args — showing warning')
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL or batch file to download.'))
            return

        # Change button to Stop - 变为红色
        def _to_stop():
            print(f"[DEBUG] Changing button to RED. Current: {self.download_btn.cget('bg')}")
            self.download_btn.config(text=self.tr('Stop'), background='#dc3545', bg='#dc3545')
            self.download_btn.update()
            print(f"[DEBUG] Changed to: {self.download_btn.cget('bg')}")

        self.after(10, _to_stop)
        self._translatable_widgets[self.download_btn] = 'Stop'

        output_dir = self.output_dir.get().strip()
        self.log_message(f'[DEBUG] output_dir={output_dir!r}')

        playlist_parsed_url = getattr(self, 'playlist_parsed_url', None)
        self.log_message(f'[DEBUG] URL match check: Input="{url}", Parsed="{playlist_parsed_url}"')

        tasks = []
        # ONLY use playlist tasks if the URL matches what we parsed!
        if hasattr(self, 'playlist_tree') and playlist_parsed_url and url == playlist_parsed_url:
            items = self.playlist_tree.get_children()
            # SIMPLICITY: Just follow the tree from TOP TO BOTTOM as shown in GUI.
            vis_to_orig_map = getattr(self, 'vis_to_orig', {})
            for item in items:
                vals = self.playlist_tree.item(item, 'values')
                checked = vals[0] == '☑'
                visual_idx = int(vals[1])

                if checked:
                    gui_title = str(vals[2])
                    original_idx = vis_to_orig_map.get(visual_idx, visual_idx)
                    task_args = []
                    skip = False
                    for arg in base_args:
                        if skip:
                            skip = False
                            continue
                        # EXCLUDE batch file and redundant playlist items from individual tasks
                        if arg in ('--playlist-items', '--playlist-reverse', '--no-playlist-reverse',
                                   '-o', '-P', '--paths', '-a', '--batch-file'):
                            if arg in ('--playlist-items', '-o', '-P', '--paths', '-a', '--batch-file'):
                                skip = True
                            continue
                        if arg == url:  # Don't add the main URL yet
                            continue
                        task_args.append(arg)

                    # Always use the specific playlist URL for individual tasks
                    task_args.append(url)
                    filename_tpl = f'{visual_idx:03d}-{gui_title}.%(ext)s'
                    # Remove unsafe characters
                    filename_tpl = ''.join([c for c in filename_tpl if c not in '<>:"/\\|?*']).strip()

                    # Handle playlist subfolder (only for actual playlists, not single videos)
                    final_output_dir = output_dir
                    if self.playlist_subdir.get() and getattr(self, 'current_playlist_metadata_title', None):
                        # Skip subfolder for single videos (playlist with only 1 entry)
                        entry_count = len(getattr(self, 'playlist_entries_data', []) or [])
                        if entry_count > 1:
                            folder_name = ''.join([c for c in self.current_playlist_metadata_title if c not in '<>:"/\\|?*']).strip()
                            if folder_name:
                                final_output_dir = os.path.join(output_dir, folder_name)
                                if not os.path.exists(final_output_dir):
                                    os.makedirs(final_output_dir, exist_ok=True)

                    out_path = os.path.join(final_output_dir, filename_tpl) if final_output_dir else filename_tpl
                    task_args.extend(['--playlist-items', str(original_idx)])
                    task_args.extend(['-o', out_path])
                    tasks.append((visual_idx, task_args))

        # If no playlist tasks were built (not a playlist or nothing checked), treat as single/batch
        if not tasks:
            tasks.append(('Single', base_args))

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.run_ytdlp, args=(tasks,), daemon=True)
        thread.start()

    def parse_playlist(self):
        url = self.url_entry.get().strip()
        batch = self.batch_file_entry.get().strip()

        # If main URL is empty but batch has a URL, use it
        if not url and batch.startswith('http') and '\n' not in batch:
            url = batch
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

        if not url:
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL.'))
            return

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)
        self.status_var.set(self.tr('Checking URL...'))
        thread = threading.Thread(target=self._parse_playlist_only, args=(url,), daemon=True)
        thread.start()

    def _parse_playlist_only(self, url):
        try:
            self.ensure_all_tabs_built()
            self.log_message(self.tr('Checking if URL is a playlist...'))
            # ADDED --no-cache-dir to ensure we get fresh language-specific metadata
            cmd = [sys.executable, '-m', 'yt_dlp', '-J', '--flat-playlist', '--no-cache-dir']

            # MAP GUI Language to Metadata Language
            lang_map = {'zh': 'zh-CN', 'en': 'en', 'ru': 'ru', 'ja': 'ja', 'ko': 'ko', 'es': 'es', 'fr': 'fr', 'de': 'de'}
            gui_lang_code = getattr(self, 'current_language', 'zh')
            lang_to_use = lang_map.get(gui_lang_code, 'zh-CN')

            self.log_message(f'[DEBUG] Parsing playlist metadata using interface-linked language: {lang_to_use}')
            cmd.extend(['--extractor-args', f'youtube:lang={lang_to_use}'])
            cmd.extend(['--add-header', f'Accept-Language:{lang_to_use},zh-CN;q=0.9,zh;q=0.8'])
            cmd.extend(['--geo-bypass'])

            # Keep playlist parsing aligned with the actual download/auth context.
            # Otherwise YouTube may reject the preflight parse while normal downloads
            # would have succeeded with the user's browser session.
            if self.cookies_from_browser.get():
                cmd.extend(['--cookies-from-browser', self.cookies_from_browser.get()])
            if self.cookies.get():
                cmd.extend(['--cookies', self.cookies.get()])
            if self.user_agent.get():
                cmd.extend(['--user-agent', self.user_agent.get()])
            if self.referer.get():
                cmd.extend(['--referer', self.referer.get()])
            if self.add_header.get():
                cmd.extend(['--add-header', self.add_header.get()])

            cmd.append(url)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                info = json.loads(stdout)
                if info.get('_type') in ('playlist', 'multi_video') and 'entries' in info:
                    self.playlist_parsed_url = url
                    self.playlist_entries_data = info['entries']
                    self.current_playlist_metadata_title = info.get('title', 'Playlist')
                    self.root.after(0, self._show_playlist_tab, self.current_playlist_metadata_title)
                    return
                else:
                    self.log_message(self.tr('Not a playlist or no entries found.'))
            else:
                self.log_message(f'[ERROR] Parsing failed: {stderr.strip()}')
                self.log_message(self.tr('Failed to parse playlist.'))
        except Exception as e:
            self.log_message(self.translate_concat('Error checking playlist: ', str(e)))
        self.status_var.set(self.tr('Ready'))

    def _show_playlist_tab(self, temp_title):
        self.log_message(self.tr('Playlist detected. Please select videos to download.'))
        self.status_var.set(self.tr('Playlist detected'))
        if hasattr(self, 'playlist_tree'):
            self.notebook.select(self.playlist_tab_frame)
            self.playlist_tree.delete(*self.playlist_tree.get_children())

            entries = self.playlist_entries_data
            filtered_entries = []
            for i, entry in enumerate(entries):
                title = entry.get('title') or entry.get('id') or f'Video {i + 1}'
                availability = entry.get('availability', '')
                is_private = (
                    title in ('[Private video]', '[私享视频]', '[私有视频]', '[Deleted video]', '[已删除的视频]')
                    or availability == 'private'
                    or entry.get('title') is None
                )
                if is_private and self.playlist_exclude_private_var.get():
                    continue
                filtered_entries.append((i + 1, title))

            if getattr(self, 'playlist_reverse_var', None) and self.playlist_reverse_var.get():
                filtered_entries = list(reversed(filtered_entries))

            total_visible = len(filtered_entries)
            self.vis_to_orig = {}
            for j, (original_idx, title) in enumerate(filtered_entries):
                # FIXED LOGIC: Top row gets the max number, Bottom row gets 1.
                # Top row is ALWAYS downloaded first.
                visual_idx = total_visible - j
                self.vis_to_orig[visual_idx] = original_idx
                status_char = '☐' if getattr(self, '_is_from_bulk_parse', False) else '☑'
                self.playlist_tree.insert('', tk.END, values=(status_char, visual_idx, title))

            # Reset headers
            self.playlist_tree.heading('status', text=' ')
            self.playlist_tree.heading('index', text='#')
            self.playlist_tree.heading('title', text=self.tr('Title'))

    def list_formats(self):
        """List available formats for the video"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL.'))
            return

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.run_ytdlp, args=(['-F', url],), daemon=True)
        thread.start()

    def extract_info(self):
        """Extract video information"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL.'))
            return

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.run_ytdlp, args=(['--dump-json', url],), daemon=True)
        thread.start()

    def _start_log_watcher(self):
        """Poll the log queue and update the UI from the main thread"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._log_message_internal(msg)
        except Exception:  # queue.Empty
            pass
        self.root.after(100, self._start_log_watcher)

    def _log_message_internal(self, message):
        """Internal method to update the console text widget and redirect progress to status bar"""
        clean_msg = message.strip()

        # Redirect [download] progress to the status bar instead of the console
        # Typically looks like: [download]  1.2% of 10.00MiB at ...
        if clean_msg.startswith('[download]') and '%' in clean_msg:
            # Strip '[download]' prefix for a cleaner look as requested
            display_msg = clean_msg.replace('[download]', '').strip()
            self.progress_var.set(display_msg)
            # Clear progress bar once finished or moved to next stage
            if '100%' in clean_msg:
                self.root.after(3000, lambda: self.progress_var.set('') if '100%' in self.progress_var.get() else None)
            return

        self.console.config(state=tk.NORMAL)
        # Check if we were already at the bottom before adding content
        at_bottom = self.console.yview()[1] == 1.0
        self.console.insert(tk.END, message + '\n')
        if at_bottom:
            self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def log_message(self, message):
        """Add message to the thread-safe queue and stdout for debugging."""
        msg_str = str(message)
        # Always output to terminal for visibility if GUI logs are failing or slow
        print(msg_str)

        if hasattr(self, 'log_queue'):
            self.log_queue.put(msg_str)
