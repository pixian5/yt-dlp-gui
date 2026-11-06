"""Lazy tab builder functions for yt-dlp GUI."""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from guiapi.constants import QUICK_RESOLUTION_FORMATS, SB_CATEGORIES
from guiapi.core import core_launcher

_QUICK_RESOLUTION_FORMATS = QUICK_RESOLUTION_FORMATS


def create_general_tab(self, frame=None):
    """Create General Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    # Scrollable frame
    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        '<Configure>',
        lambda e: canvas.configure(scrollregion=canvas.bbox('all')),
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # General options
    row = 0

    self.ignore_errors = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Ignore errors (--ignore-errors)',
                    variable=self.ignore_errors).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_warnings = self.get_or_create_boolvar('no_warnings')
    ttk.Checkbutton(scrollable_frame, text='Ignore warnings (--no-warnings)',
                    variable=self.no_warnings).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.abort_on_error = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Abort on error (--abort-on-error)',
                    variable=self.abort_on_error).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_playlist = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Download only video, not playlist (--no-playlist)',
                    variable=self.no_playlist).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.yes_playlist = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Download playlist (--yes-playlist)',
                    variable=self.yes_playlist).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.include_private_videos = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        scrollable_frame,
        text='Include private/unavailable videos in YouTube playlists',
        variable=self.include_private_videos,
    ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.mark_watched = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Mark videos as watched (--mark-watched)',
                    variable=self.mark_watched).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_mark_watched = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not mark videos as watched (--no-mark-watched)',
                    variable=self.no_mark_watched).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Default search prefix:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.default_search = ttk.Entry(scrollable_frame, width=40)
    self.default_search.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(e.g., "ytsearch5:")').grid(row=row, column=2, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Configuration file:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    config_frame = ttk.Frame(scrollable_frame)
    config_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    self.config_location = ttk.Entry(config_frame, width=40)
    self.config_location.pack(side=tk.LEFT)
    ttk.Button(config_frame, text='Browse...', command=self.browse_config_file).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    ttk.Label(scrollable_frame, text='Flat playlist extraction:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.extract_flat = ttk.Combobox(
        scrollable_frame,
        width=20,
        # CLI only supports --flat-playlist (const in_playlist). Discard modes are API-only.
        values=['', 'in_playlist'],
        state='readonly',
    )
    self.extract_flat.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(empty=default, in_playlist=--flat-playlist)').grid(
        row=row, column=2, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Age limit (years):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.age_limit = ttk.Entry(scrollable_frame, width=10)
    self.age_limit.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Download archive file:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    archive_frame = ttk.Frame(scrollable_frame)
    archive_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    self.download_archive = ttk.Entry(archive_frame, width=40)
    self.download_archive.pack(side=tk.LEFT)
    ttk.Button(archive_frame, text='Browse...', command=self.browse_archive_file).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    ttk.Label(scrollable_frame, text='Max downloads:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.max_downloads = ttk.Entry(scrollable_frame, width=10)
    self.max_downloads.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

def create_network_tab(self, frame=None):
    """Create Network Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    ttk.Label(scrollable_frame, text='Proxy URL:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.proxy = ttk.Entry(scrollable_frame, width=50)
    self.proxy.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Socket timeout (seconds):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.socket_timeout = ttk.Entry(scrollable_frame, width=10)
    self.socket_timeout.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Source address (bind to):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.source_address = ttk.Entry(scrollable_frame, width=30)
    self.source_address.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.force_ipv4 = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Force IPv4 (--force-ipv4)',
                    variable=self.force_ipv4).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.force_ipv6 = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Force IPv6 (--force-ipv6)',
                    variable=self.force_ipv6).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.enable_file_urls = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Enable file:// URLs (--enable-file-urls)',
                    variable=self.enable_file_urls).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Sleep interval (seconds):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.sleep_interval = ttk.Entry(scrollable_frame, width=10)
    self.sleep_interval.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Max sleep interval (seconds):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.max_sleep_interval = ttk.Entry(scrollable_frame, width=10)
    self.max_sleep_interval.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Sleep between requests (--sleep-requests):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.sleep_interval_requests = ttk.Entry(scrollable_frame, width=10)
    self.sleep_interval_requests.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Sleep interval for subtitles (seconds):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.sleep_interval_subtitles = ttk.Entry(scrollable_frame, width=10)
    self.sleep_interval_subtitles.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Rate limit (--limit-rate):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.rate_limit = ttk.Entry(scrollable_frame, width=15)
    self.rate_limit.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(e.g., 50K or 4.2M)').grid(row=row, column=2, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Throttled rate (minimum rate):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.throttled_rate = ttk.Entry(scrollable_frame, width=15)
    self.throttled_rate.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Retries:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.retries = ttk.Entry(scrollable_frame, width=10)
    self.retries.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Fragment retries:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.fragment_retries = ttk.Entry(scrollable_frame, width=10)
    self.fragment_retries.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

def create_geo_restriction_tab(self, frame=None):
    """Create Geo-restriction tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    row = 0

    ttk.Label(frame, text='Geo verification proxy:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.geo_verification_proxy = ttk.Entry(frame, width=50)
    self.geo_verification_proxy.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.geo_bypass = tk.BooleanVar()
    ttk.Checkbutton(frame, text='Bypass geo restriction (--geo-bypass)',
                    variable=self.geo_bypass).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_geo_bypass = tk.BooleanVar()
    ttk.Checkbutton(frame, text='Do not bypass geo restriction (--no-geo-bypass)',
                    variable=self.no_geo_bypass).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(frame, text='Geo bypass country:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.geo_bypass_country = ttk.Entry(frame, width=10)
    self.geo_bypass_country.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    ttk.Label(frame, text='(ISO 3166-2 code)').grid(row=row, column=2, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(frame, text='Geo bypass IP block:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.geo_bypass_ip_block = ttk.Entry(frame, width=30)
    self.geo_bypass_ip_block.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    ttk.Label(frame, text='(CIDR notation)').grid(row=row, column=2, sticky=tk.W, pady=5)
    row += 1

def create_video_selection_tab(self, frame=None):
    """Create Video Selection tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    ttk.Label(scrollable_frame, text='Playlist items:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.playlist_items = ttk.Entry(scrollable_frame, width=30)
    self.playlist_items.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(e.g., "1-5,10,15-20")').grid(row=row, column=2, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Playlist start:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.playlist_start = ttk.Entry(scrollable_frame, width=10)
    self.playlist_start.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Playlist end:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.playlist_end = ttk.Entry(scrollable_frame, width=10)
    self.playlist_end.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Match title (regex):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.match_title = ttk.Entry(scrollable_frame, width=40)
    self.match_title.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Reject title (regex):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.reject_title = ttk.Entry(scrollable_frame, width=40)
    self.reject_title.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Min filesize (e.g., 50k or 1M):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.min_filesize = ttk.Entry(scrollable_frame, width=15)
    self.min_filesize.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Max filesize (e.g., 50M or 1G):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.max_filesize = ttk.Entry(scrollable_frame, width=15)
    self.max_filesize.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Date (YYYYMMDD):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.date = ttk.Entry(scrollable_frame, width=15)
    self.date.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Date before (YYYYMMDD):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.datebefore = ttk.Entry(scrollable_frame, width=15)
    self.datebefore.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Date after (YYYYMMDD):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.dateafter = ttk.Entry(scrollable_frame, width=15)
    self.dateafter.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Min views:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.min_views = ttk.Entry(scrollable_frame, width=15)
    self.min_views.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Max views:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.max_views = ttk.Entry(scrollable_frame, width=15)
    self.max_views.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Match filter:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.match_filter = ttk.Entry(scrollable_frame, width=40)
    self.match_filter.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.break_on_existing = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Break on existing (--break-on-existing)',
                    variable=self.break_on_existing).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.break_on_reject = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Break on reject (--break-on-reject)',
                    variable=self.break_on_reject).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_break_on_existing = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='No break on existing (--no-break-on-existing)',
                    variable=self.no_break_on_existing).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

def create_download_tab(self, frame=None):
    """Create Download Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    ttk.Label(scrollable_frame, text='Concurrent fragments:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.concurrent_fragments = ttk.Entry(scrollable_frame, width=10)
    self.concurrent_fragments.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    # Rate limit lives only on Network tab (self.rate_limit) to avoid dual --limit-rate sources.

    ttk.Label(scrollable_frame, text='Buffer size:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.buffer_size = ttk.Entry(scrollable_frame, width=15)
    self.buffer_size.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='HTTP chunk size:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.http_chunk_size = ttk.Entry(scrollable_frame, width=15)
    self.http_chunk_size.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.no_resize_buffer = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not resize buffer (--no-resize-buffer)',
                    variable=self.no_resize_buffer).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.test = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Test mode - do not download (--test)',
                    variable=self.test).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='External downloader:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.external_downloader = ttk.Combobox(scrollable_frame, width=20,
                                            values=['', 'aria2c', 'avconv', 'axel', 'curl', 'ffmpeg', 'httpie', 'wget'],
                                            state='readonly')
    self.external_downloader.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='External downloader args:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.external_downloader_args = ttk.Entry(scrollable_frame, width=40)
    self.external_downloader_args.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.hls_prefer_native = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Prefer native HLS downloader (--hls-prefer-native)',
                    variable=self.hls_prefer_native).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.hls_prefer_ffmpeg = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Prefer ffmpeg for HLS (--hls-prefer-ffmpeg)',
                    variable=self.hls_prefer_ffmpeg).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.hls_use_mpegts = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Use MPEG-TS container for HLS (--hls-use-mpegts)',
                    variable=self.hls_use_mpegts).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

def create_filesystem_tab(self, frame=None):
    """Create Filesystem Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    ttk.Label(scrollable_frame, text='Output template:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.output_template = ttk.Entry(scrollable_frame, width=50)
    self.output_template.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(e.g., "%(title)s.%(ext)s")').grid(row=row, column=3, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Output directory:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    output_frame = ttk.Frame(scrollable_frame)
    output_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
    self.output_dir = ttk.Entry(output_frame, width=50)
    self.output_dir.pack(side=tk.LEFT)
    ttk.Button(output_frame, text='Browse...', command=self.browse_output_dir).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    ttk.Label(scrollable_frame, text='Paths configuration:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.paths = ttk.Entry(scrollable_frame, width=50)
    self.paths.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.restrict_filenames = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Restrict filenames to ASCII (--restrict-filenames)',
                    variable=self.restrict_filenames).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_restrict_filenames = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Allow Unicode in filenames (--no-restrict-filenames)',
                    variable=self.no_restrict_filenames).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.playlist_subdir = tk.BooleanVar()
    ttk.Checkbutton(
        scrollable_frame,
        text='Create playlist subfolder for playlist downloads',
        variable=self.playlist_subdir,
    ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.windows_filenames = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Force Windows-compatible filenames (--windows-filenames)',
                    variable=self.windows_filenames).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_overwrites = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not overwrite files (--no-overwrites)',
                    variable=self.no_overwrites).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.force_overwrites = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Force overwrite files (--force-overwrites)',
                    variable=self.force_overwrites).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.continue_dl = tk.BooleanVar(value=True)
    ttk.Checkbutton(scrollable_frame, text='Continue partially downloaded files (--continue)',
                    variable=self.continue_dl).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_continue = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not continue downloads (--no-continue)',
                    variable=self.no_continue).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_part = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not use .part files (--no-part)',
                    variable=self.no_part).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_mtime = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not use Last-modified header (--no-mtime)',
                    variable=self.no_mtime).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.write_description = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Write description to .description file (--write-description)',
                    variable=self.write_description).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.write_info_json = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Write metadata to .info.json file (--write-info-json)',
                    variable=self.write_info_json).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.write_annotations = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Write annotations to .annotations.xml (--write-annotations)',
                    variable=self.write_annotations).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.write_comments = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Write comments to .comments.json (--write-comments)',
                    variable=self.write_comments).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Load info JSON:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    load_frame = ttk.Frame(scrollable_frame)
    load_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
    self.load_info_json = ttk.Entry(load_frame, width=50)
    self.load_info_json.pack(side=tk.LEFT)
    ttk.Button(load_frame, text='Browse...', command=self.browse_info_json).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    ttk.Label(scrollable_frame, text='Cache directory:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    cache_frame = ttk.Frame(scrollable_frame)
    cache_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
    self.cache_dir = ttk.Entry(cache_frame, width=50)
    self.cache_dir.pack(side=tk.LEFT)
    ttk.Button(cache_frame, text='Browse...', command=self.browse_cache_dir).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    self.no_cache_dir = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Disable filesystem caching (--no-cache-dir)',
                    variable=self.no_cache_dir).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.rm_cache_dir = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Delete cache directory contents (--rm-cache-dir)',
                    variable=self.rm_cache_dir).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

def create_video_format_tab(self, frame=None):
    """Create Video Format Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    ttk.Label(scrollable_frame, text='Format selection:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    # Keep the free-form field and quick selector on a shared Tcl variable;
    # this makes the overwrite visible even on Tk builds with unreliable
    # ComboboxSelected/trace ordering.
    self.format_var = tk.StringVar()
    self.format = ttk.Entry(scrollable_frame, textvariable=self.format_var, width=50)
    self.format.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(e.g., "bestvideo+bestaudio")').grid(row=row, column=3, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Quick Select Resolution:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.res_var = tk.StringVar()
    self.res_selector = ttk.Combobox(scrollable_frame, textvariable=self.res_var, width=30,
                                     values=[self.tr(opt) for opt in _QUICK_RESOLUTION_FORMATS], state='readonly')
    self.res_selector.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    # Trace every value update rather than only <<ComboboxSelected>>. This
    # covers mouse/keyboard selection and programmatic combobox updates.
    self.res_var.trace_add('write', self._on_res_selected)
    # ttk emits this event after the native dropdown commits a selection;
    # keep it as a second path because some Tk builds do not fire a
    # variable trace for readonly combobox mouse selections.
    # Pass the combobox itself: macOS Tk can update the visible readonly
    # value without updating its linked StringVar.
    self.res_selector.bind(
        '<<ComboboxSelected>>',
        lambda _event, selector=self.res_selector: self._on_res_selected(selector),
    )
    # macOS Tk can update the native readonly value without emitting
    # ``<<ComboboxSelected>>``.  Read the committed value after the mouse
    # release as a final UI path so a real click always updates the field.
    self.res_selector.bind('<ButtonRelease-1>', self._on_res_mouse_release, add='+')
    self.register_translatable_widget(self.res_selector, 'Quick Select Resolution Selector')  # Placeholder to trigger refresh
    row += 1

    ttk.Label(scrollable_frame, text='Format sort:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.format_sort = ttk.Entry(scrollable_frame, width=50)
    self.format_sort.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.prefer_free_formats = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Prefer free formats (--prefer-free-formats)',
                    variable=self.prefer_free_formats).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.check_formats = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Check available formats (--check-formats)',
                    variable=self.check_formats).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Merge output format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.merge_output_format = ttk.Combobox(scrollable_frame, width=15,
                                            values=['', 'mkv', 'mp4', 'ogg', 'webm', 'flv'],
                                            state='readonly')
    self.merge_output_format.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Video multistreams:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.video_multistreams = ttk.Combobox(scrollable_frame, width=15,
                                           values=['', 'yes', 'no'],
                                           state='readonly')
    self.video_multistreams.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Audio multistreams:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.audio_multistreams = ttk.Combobox(scrollable_frame, width=15,
                                           values=['', 'yes', 'no'],
                                           state='readonly')
    self.audio_multistreams.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

def _on_res_selected(self, *args):
    """Overwrite Format selection with the selected quick-resolution preset."""
    # On some Tk/macOS builds the readonly combobox updates its displayed
    # value before the linked Tcl variable trace runs. Read the event
    # widget first so the actual click always wins; trace callbacks still
    # use res_var as the fallback.
    selector = args[0] if args and hasattr(args[0], 'get') else None
    event = args[0] if args and hasattr(args[0], 'widget') else None
    if selector is None:
        selector = getattr(event, 'widget', None)
    if selector is not None and hasattr(selector, 'get'):
        val = selector.get().strip()
    else:
        val = self.res_var.get().strip()
    preset = next(
        (key for key in _QUICK_RESOLUTION_FORMATS if val == key or val == self.tr(key)),
        None,
    )
    if preset is None or not hasattr(self, 'format'):
        return

    format_value = _QUICK_RESOLUTION_FORMATS[preset]
    if hasattr(self, 'format_var'):
        self.format_var.set(format_value)
    else:
        # Compatibility for callers constructing the tab with a legacy
        # Entry-only test double; the live tab always uses format_var.
        self.format.delete(0, tk.END)
        self.format.insert(0, format_value)
    self.trigger_autosave()

def _on_res_mouse_release(self, event):
    """Apply a native macOS Combobox selection after it is committed."""
    selector = getattr(event, 'widget', None)
    if selector is not None:
        self.root.after_idle(lambda: self._on_res_selected(selector))

def create_subtitle_tab(self, frame=None):
    """Create Subtitle Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    self.write_subs = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Write subtitle file (--write-subs)',
                    variable=self.write_subs).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.write_auto_subs = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Write automatic subtitle file (--write-auto-subs)',
                    variable=self.write_auto_subs).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.list_subs = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='List available subtitles (--list-subs)',
                    variable=self.list_subs).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Subtitle format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.sub_format = ttk.Combobox(scrollable_frame, width=20,
                                   values=['', 'srt', 'vtt', 'ass', 'lrc'],
                                   state='readonly')
    self.sub_format.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Subtitle languages:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.sub_langs = ttk.Entry(scrollable_frame, width=40)
    self.sub_langs.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(comma-separated, e.g., "en,fr,de")').grid(row=row, column=3, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Smart subtitle language:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.smart_subtitle_lang_map = {
        'Disabled': '',
        '中文（简体） (zh-CN)': 'zh-CN',
        'English (en)': 'en',
        '日本語 (ja)': 'ja',
        '한국어 (ko)': 'ko',
        'Español (es)': 'es',
        'Français (fr)': 'fr',
        'Deutsch (de)': 'de',
        'Русский (ru)': 'ru',
    }
    self.smart_subtitle_language = ttk.Combobox(
        scrollable_frame,
        width=30,
        values=list(self.smart_subtitle_lang_map.keys()),
        state='readonly',
    )
    default_smart_lang = 'Disabled'
    # 兼容旧配置：若此前启用了 smart_zh_subs，则迁移为 zh-CN
    if self._pending_gui_state.get('smart_zh_subs') and not self._pending_gui_state.get('smart_subtitle_language'):
        default_smart_lang = '中文（简体） (zh-CN)'
    self.smart_subtitle_language.set(default_smart_lang)
    self.smart_subtitle_language.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(
        scrollable_frame,
        text='Smart subtitle language (download target language; auto-translate when unavailable)',
    ).grid(row=row, column=0, columnspan=4, sticky=tk.W, pady=(0, 5), padx=5)
    row += 1

    self.embed_subs = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Embed subtitles (--embed-subs)',
                    variable=self.embed_subs).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_embed_subs = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not embed subtitles (--no-embed-subs)',
                    variable=self.no_embed_subs).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.embed_thumbnail = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Embed thumbnail (--embed-thumbnail)',
                    variable=self.embed_thumbnail).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_embed_thumbnail = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not embed thumbnail (--no-embed-thumbnail)',
                    variable=self.no_embed_thumbnail).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

def get_smart_subtitle_lang_code(self):
    """Return selected smart subtitle target language code, or empty string if disabled."""
    if not hasattr(self, 'smart_subtitle_language') or not hasattr(self, 'smart_subtitle_lang_map'):
        return ''
    selected = self.smart_subtitle_language.get().strip()
    return self.smart_subtitle_lang_map.get(selected, '')

def build_smart_sub_langs(self, target_lang):
    """Build a robust --sub-langs list: prefer target language, then translated variants to target."""
    if not target_lang:
        return ''

    direct_lang_variants = {
        'zh-CN': ['zh', 'zh-CN', 'zh-TW', 'zh-Hans', 'zh-Hant'],
        'en': ['en', 'en-US', 'en-GB'],
        'ja': ['ja'],
        'ko': ['ko'],
        'es': ['es', 'es-419', 'es-ES'],
        'fr': ['fr', 'fr-FR'],
        'de': ['de', 'de-DE'],
        'ru': ['ru', 'ru-RU'],
    }

    langs = []

    def _append_unique(lang_code):
        if lang_code and lang_code not in langs:
            langs.append(lang_code)

    for lang_code in direct_lang_variants.get(target_lang, [target_lang]):
        _append_unique(lang_code)

    # 常见翻译来源字幕，按“源语-目标语”补充回退
    source_langs = ['en', 'ja', 'ko', 'fr', 'de', 'es', 'ru', 'zh', 'zh-CN', 'zh-TW']
    for src in source_langs:
        if src != target_lang:
            _append_unique(f'{src}-{target_lang}')

    return ','.join(langs)

def create_authentication_tab(self, frame=None):
    """Create Authentication Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    ttk.Label(scrollable_frame, text='Username:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.username = ttk.Entry(scrollable_frame, width=30)
    self.username.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.password = ttk.Entry(scrollable_frame, width=30, show='*')
    self.password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Two-factor code:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.twofactor = ttk.Entry(scrollable_frame, width=20)
    self.twofactor.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.netrc = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Use .netrc authentication (--netrc)',
                    variable=self.netrc).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Video password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.video_password = ttk.Entry(scrollable_frame, width=30, show='*')
    self.video_password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Adobe Pass MSO:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.ap_mso = ttk.Entry(scrollable_frame, width=30)
    self.ap_mso.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Adobe Pass username:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.ap_username = ttk.Entry(scrollable_frame, width=30)
    self.ap_username.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Adobe Pass password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.ap_password = ttk.Entry(scrollable_frame, width=30, show='*')
    self.ap_password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Client certificate:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    cert_frame = ttk.Frame(scrollable_frame)
    cert_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    self.client_certificate = ttk.Entry(cert_frame, width=40)
    self.client_certificate.pack(side=tk.LEFT)
    ttk.Button(cert_frame, text='Browse...', command=self.browse_client_cert).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    ttk.Label(scrollable_frame, text='Client certificate key:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    key_frame = ttk.Frame(scrollable_frame)
    key_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    self.client_certificate_key = ttk.Entry(key_frame, width=40)
    self.client_certificate_key.pack(side=tk.LEFT)
    ttk.Button(key_frame, text='Browse...', command=self.browse_client_key).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    ttk.Label(scrollable_frame, text='Client certificate password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.client_certificate_password = ttk.Entry(scrollable_frame, width=30, show='*')
    self.client_certificate_password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

def create_postprocessing_tab(self, frame=None):
    """Create Post-processing Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    self.extract_audio = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Extract audio (-x, --extract-audio)',
                    variable=self.extract_audio).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Audio format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.audio_format = ttk.Combobox(scrollable_frame, width=15,
                                     values=['', 'best', 'aac', 'm4a', 'mp3', 'opus', 'vorbis', 'wav', 'flac', 'alac'],
                                     state='readonly')
    self.audio_format.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Audio quality:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.audio_quality = ttk.Entry(scrollable_frame, width=10)
    self.audio_quality.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    ttk.Label(scrollable_frame, text='(0-10, 0 = best)').grid(row=row, column=2, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(scrollable_frame, text='Recode video format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.recode_video = ttk.Combobox(scrollable_frame, width=15,
                                     values=['', 'mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi'],
                                     state='readonly')
    self.recode_video.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Remux video format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.remux_video = ttk.Combobox(scrollable_frame, width=15,
                                    values=['', 'mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi', 'mov'],
                                    state='readonly')
    self.remux_video.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.keep_video = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Keep video file after conversion (--keep-video)',
                    variable=self.keep_video).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_keep_video = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Do not keep video file (--no-keep-video)',
                    variable=self.no_keep_video).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.embed_metadata = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Embed metadata (--embed-metadata)',
                    variable=self.embed_metadata).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.embed_chapters = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Embed chapter markers (--embed-chapters)',
                    variable=self.embed_chapters).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.embed_info_json = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Embed info.json (--embed-info-json)',
                    variable=self.embed_info_json).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.add_metadata = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Add metadata to file (--add-metadata)',
                    variable=self.add_metadata).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Metadata fields:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.metadata_from_title = ttk.Entry(scrollable_frame, width=40)
    self.metadata_from_title.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Parse metadata:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.parse_metadata = ttk.Entry(scrollable_frame, width=40)
    self.parse_metadata.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='FFmpeg location:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    ffmpeg_frame = ttk.Frame(scrollable_frame)
    ffmpeg_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    self.ffmpeg_location = ttk.Entry(ffmpeg_frame, width=40)
    self.ffmpeg_location.pack(side=tk.LEFT)
    ttk.Button(ffmpeg_frame, text='Browse...', command=self.browse_ffmpeg).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

    ttk.Label(scrollable_frame, text='Post-processor args:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.postprocessor_args = ttk.Entry(scrollable_frame, width=50)
    self.postprocessor_args.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

def create_thumbnail_tab(self, frame=None):
    """Create Thumbnail Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    row = 0

    self.write_thumbnail = tk.BooleanVar()
    ttk.Checkbutton(frame, text='Write thumbnail image (--write-thumbnail)',
                    variable=self.write_thumbnail).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.write_all_thumbnails = tk.BooleanVar()
    ttk.Checkbutton(frame, text='Write all thumbnail formats (--write-all-thumbnails)',
                    variable=self.write_all_thumbnails).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.list_thumbnails = tk.BooleanVar()
    ttk.Checkbutton(frame, text='List available thumbnails (--list-thumbnails)',
                    variable=self.list_thumbnails).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(frame, text='Convert thumbnails format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.convert_thumbnails = ttk.Combobox(frame, width=15,
                                           values=['', 'jpg', 'png', 'webp'],
                                           state='readonly')
    self.convert_thumbnails.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

def create_verbosity_tab(self, frame=None):
    """Create Verbosity and Simulation tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    self.quiet = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Quiet mode (-q, --quiet)',
                    variable=self.quiet).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_warnings = self.get_or_create_boolvar('no_warnings')
    ttk.Checkbutton(scrollable_frame, text='No warnings (--no-warnings)',
                    variable=self.no_warnings).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.verbose = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Verbose output (-v, --verbose)',
                    variable=self.verbose).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.simulate = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Simulate, do not download (-s, --simulate)',
                    variable=self.simulate).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.skip_download = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Skip download (--skip-download)',
                    variable=self.skip_download).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_title = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get title (--get-title)',
                    variable=self.get_title).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_id = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get ID (--get-id)',
                    variable=self.get_id).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_url = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get URL (--get-url)',
                    variable=self.get_url).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_thumbnail = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get thumbnail URL (--get-thumbnail)',
                    variable=self.get_thumbnail).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_description = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get description (--get-description)',
                    variable=self.get_description).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_duration = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get duration (--get-duration)',
                    variable=self.get_duration).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_filename = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get filename (--get-filename)',
                    variable=self.get_filename).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.get_format = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Get format (--get-format)',
                    variable=self.get_format).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.dump_json = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Dump JSON info (--dump-json)',
                    variable=self.dump_json).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.dump_single_json = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Dump single JSON (--dump-single-json)',
                    variable=self.dump_single_json).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.print_json = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Print JSON info (--print-json)',
                    variable=self.print_json).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.progress = tk.BooleanVar(value=True)
    ttk.Checkbutton(scrollable_frame, text='Show progress (--progress)',
                    variable=self.progress).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.no_progress = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Hide progress (--no-progress)',
                    variable=self.no_progress).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.console_title = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Display progress in console title (--console-title)',
                    variable=self.console_title).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
    row += 1

    before = set(self.__dict__)
    self.progress_template = ttk.Entry(scrollable_frame, width=50)
    ttk.Label(scrollable_frame, text=self.tr('Progress template:')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.progress_template.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    self.register_stateful_controls(set(self.__dict__) - before)
    row += 1

    before2 = set(self.__dict__)
    ttk.Label(scrollable_frame, text=self.tr('Metadata language:')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.metadata_lang = ttk.Combobox(
        scrollable_frame,
        values=[self.tr('Default (Auto)'), 'zh-CN', 'zh-TW', 'zh-HK', 'en', 'ja', 'ko'],
        state='readonly',
        width=20,
    )
    self.metadata_lang.set('zh-CN')
    self.metadata_lang.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    self.register_stateful_controls(set(self.__dict__) - before2)
    row += 1

def create_workarounds_tab(self, frame=None):
    """Create Workarounds tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    ttk.Label(scrollable_frame, text='Encoding:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.encoding = ttk.Entry(scrollable_frame, width=20)
    self.encoding.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.no_check_certificate = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Skip SSL certificate validation (--no-check-certificate)',
                    variable=self.no_check_certificate).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.prefer_insecure = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Prefer insecure connections (--prefer-insecure)',
                    variable=self.prefer_insecure).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='User agent:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.user_agent = ttk.Entry(scrollable_frame, width=50)
    self.user_agent.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Referer:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.referer = ttk.Entry(scrollable_frame, width=50)
    self.referer.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(scrollable_frame, text='Add header:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.add_header = ttk.Entry(scrollable_frame, width=50)
    self.add_header.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.bidi_workaround = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Bidirectional text workaround (--bidi-workaround)',
                    variable=self.bidi_workaround).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    # Sleep-before-requests lives only on Network tab (self.sleep_interval_requests).

    self.legacy_server_connect = tk.BooleanVar()
    ttk.Checkbutton(scrollable_frame, text='Use legacy server connect (--legacy-server-connect)',
                    variable=self.legacy_server_connect).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

def create_sponsorblock_tab(self, frame=None):
    """Create SponsorBlock Options tab with category checkboxes and selection controls"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    # Scrollable container for many options
    canvas = tk.Canvas(frame, highlightthickness=0)
    vsb = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    scroll_frame = ttk.Frame(canvas)
    scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    c_win = canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
    canvas.bind('<Configure>', lambda e: canvas.itemconfig(c_win, width=e.width))
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    row = 0

    # Main switches
    self.sponsorblock_mark = tk.BooleanVar()
    cb_m = ttk.Checkbutton(scroll_frame, text='Mark SponsorBlock chapters (--sponsorblock-mark)', variable=self.sponsorblock_mark)
    cb_m.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    self.register_translatable_widget(cb_m, 'Mark SponsorBlock chapters (--sponsorblock-mark)')
    row += 1

    self.sponsorblock_remove = tk.BooleanVar()
    cb_r = ttk.Checkbutton(scroll_frame, text='Remove SponsorBlock segments (--sponsorblock-remove)', variable=self.sponsorblock_remove)
    cb_r.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    self.register_translatable_widget(cb_r, 'Remove SponsorBlock segments (--sponsorblock-remove)')
    row += 1

    self.no_sponsorblock = tk.BooleanVar()
    cb_nosb = ttk.Checkbutton(scroll_frame, text='Disable SponsorBlock (--no-sponsorblock)', variable=self.no_sponsorblock)
    cb_nosb.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    self.register_translatable_widget(cb_nosb, 'Disable SponsorBlock (--no-sponsorblock)')
    row += 1

    ttk.Separator(scroll_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
    row += 1

    # Categories to REMOVE
    rem_lf = ttk.LabelFrame(scroll_frame, text='SponsorBlock categories to remove:', padding=10)
    rem_lf.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
    self.register_translatable_widget(rem_lf, 'SponsorBlock categories to remove:')

    # Selection buttons for Remove group
    rem_ctrl = ttk.Frame(rem_lf)
    rem_ctrl.pack(fill=tk.X, pady=(0, 5))

    btn_rm_all = ttk.Button(rem_ctrl, text='Select All', command=lambda: self._set_sb_group('remove', True))
    btn_rm_all.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_rm_all, 'Select All')

    btn_rm_none = ttk.Button(rem_ctrl, text='Deselect All', command=lambda: self._set_sb_group('remove', False))
    btn_rm_none.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_rm_none, 'Deselect All')

    btn_rm_inv = ttk.Button(rem_ctrl, text='Invert Select', command=lambda: self._set_sb_group('remove', 'invert'))
    btn_rm_inv.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_rm_inv, 'Invert Select')

    rem_grid = ttk.Frame(rem_lf)
    rem_grid.pack(fill=tk.X)
    self.sb_remove_vars = {}
    for idx, cat in enumerate(SB_CATEGORIES):
        var = tk.BooleanVar()
        self.sb_remove_vars[cat] = var
        self._stateful_controls[f'sb_remove_{cat}'] = var
        cb = ttk.Checkbutton(rem_grid, text=cat, variable=var)
        cb.grid(row=idx // 2, column=idx % 2, sticky=tk.W, padx=10, pady=2)
        self.register_translatable_widget(cb, cat)
    row += 1

    # Categories to MARK
    mark_lf = ttk.LabelFrame(scroll_frame, text='SponsorBlock categories to mark:', padding=10)
    mark_lf.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
    self.register_translatable_widget(mark_lf, 'SponsorBlock categories to mark:')

    # Selection buttons for Mark group
    mark_ctrl = ttk.Frame(mark_lf)
    mark_ctrl.pack(fill=tk.X, pady=(0, 5))

    btn_mk_all = ttk.Button(mark_ctrl, text='Select All', command=lambda: self._set_sb_group('mark', True))
    btn_mk_all.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_mk_all, 'Select All')

    btn_mk_none = ttk.Button(mark_ctrl, text='Deselect All', command=lambda: self._set_sb_group('mark', False))
    btn_mk_none.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_mk_none, 'Deselect All')

    btn_mk_inv = ttk.Button(mark_ctrl, text='Invert Select', command=lambda: self._set_sb_group('mark', 'invert'))
    btn_mk_inv.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_mk_inv, 'Invert Select')

    mark_grid = ttk.Frame(mark_lf)
    mark_grid.pack(fill=tk.X)
    self.sb_mark_vars = {}
    for idx, cat in enumerate(SB_CATEGORIES):
        var = tk.BooleanVar()
        self.sb_mark_vars[cat] = var
        self._stateful_controls[f'sb_mark_{cat}'] = var
        cb = ttk.Checkbutton(mark_grid, text=cat, variable=var)
        cb.grid(row=idx // 2, column=idx % 2, sticky=tk.W, padx=10, pady=2)
        self.register_translatable_widget(cb, cat)
    row += 1

    # Other SB settings
    ttk.Label(scroll_frame, text='SponsorBlock chapter title:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.sponsorblock_chapter_title = ttk.Entry(scroll_frame, width=40)
    self.sponsorblock_chapter_title.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    self.register_translatable_widget(scroll_frame.grid_slaves(row=row, column=0)[0], 'SponsorBlock chapter title:')
    row += 1

    ttk.Label(scroll_frame, text='SponsorBlock API URL:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.sponsorblock_api = ttk.Entry(scroll_frame, width=50)
    self.sponsorblock_api.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    self.register_translatable_widget(scroll_frame.grid_slaves(row=row, column=0)[0], 'SponsorBlock API URL:')
    row += 1

def _set_sb_group(self, group, state):
    vars_dict = self.sb_remove_vars if group == 'remove' else self.sb_mark_vars
    for var in vars_dict.values():
        if state == 'invert':
            var.set(not var.get())
        else:
            var.set(state)

def create_extractor_tab(self, frame=None):
    """Create Extractor Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    row = 0

    ttk.Label(frame, text='Extractor arguments:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.extractor_args = ttk.Entry(frame, width=60)
    self.extractor_args.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
    ttk.Label(frame, text='(key:val[,val] format)').grid(row=row, column=3, sticky=tk.W, pady=5)
    row += 1

    ttk.Label(frame, text='Extractor retries:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.extractor_retries = ttk.Entry(frame, width=10)
    self.extractor_retries.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    self.allow_dynamic_mpd = tk.BooleanVar()
    ttk.Checkbutton(frame, text='Allow dynamic MPD manifests (--allow-dynamic-mpd)',
                    variable=self.allow_dynamic_mpd).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.ignore_dynamic_mpd = tk.BooleanVar()
    ttk.Checkbutton(frame, text='Ignore dynamic MPD manifests (--ignore-dynamic-mpd)',
                    variable=self.ignore_dynamic_mpd).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    self.hls_split_discontinuity = tk.BooleanVar()
    ttk.Checkbutton(frame, text='Split HLS segments on discontinuity (--hls-split-discontinuity)',
                    variable=self.hls_split_discontinuity).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
    row += 1

    ttk.Label(frame, text='Cookies from browser:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    self.cookies_from_browser = ttk.Combobox(frame, width=20,
                                             values=['', 'chrome', 'firefox', 'safari', 'edge', 'opera', 'brave', 'chromium', 'vivaldi'],
                                             state='readonly')
    self.cookies_from_browser.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
    row += 1

    ttk.Label(frame, text='Cookies file:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
    cookies_frame = ttk.Frame(frame)
    cookies_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
    self.cookies = ttk.Entry(cookies_frame, width=50)
    self.cookies.pack(side=tk.LEFT)
    ttk.Button(cookies_frame, text='Browse...', command=self.browse_cookies).pack(side=tk.LEFT, padx=(5, 0))
    row += 1

def create_advanced_tab(self, frame=None):
    """Create Advanced Options tab"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    row = 0

    ttk.Label(frame, text='Raw command-line arguments:').grid(row=row, column=0, sticky=tk.NW, pady=5, padx=5)
    self.raw_args = scrolledtext.ScrolledText(frame, width=80, height=10, wrap=tk.WORD)
    self.raw_args.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
    ttk.Label(frame, text='(One argument per line or space-separated)').grid(row=row + 1, column=1, sticky=tk.W, padx=5)
    row += 2

    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
    row += 1

    ttk.Label(frame, text='Generated command:').grid(row=row, column=0, sticky=tk.NW, pady=5, padx=5)
    self.generated_cmd = scrolledtext.ScrolledText(frame, width=80, height=8, wrap=tk.WORD, state=tk.DISABLED)
    self.generated_cmd.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
    row += 1

    button_frame = ttk.Frame(frame)
    button_frame.grid(row=row, column=1, pady=10)
    ttk.Button(button_frame, text='Generate Command', command=self.generate_command).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text='Copy to Clipboard', command=self.copy_command).pack(side=tk.LEFT, padx=5)
    row += 1


def create_batch_download_tab(self, frame=None):
    """Create Batch Download tab."""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    file_row = ttk.Frame(frame)
    file_row.pack(fill=tk.X, pady=(0, 8))
    lbl_file = ttk.Label(file_row, text=self.tr('Batch file path:'))
    lbl_file.pack(side=tk.LEFT)
    self.register_translatable_widget(lbl_file, 'Batch file path:')

    self.batch_file_var = tk.StringVar()
    self.batch_file_var.trace_add('write', self.trigger_autosave)
    self.batch_file_input = ttk.Entry(file_row, textvariable=self.batch_file_var)
    self.batch_file_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 5))
    btn_browse = ttk.Button(file_row, text=self.tr('Browse...'), command=self.browse_batch_file)
    btn_browse.pack(side=tk.LEFT)
    self.register_translatable_widget(btn_browse, 'Browse...')

    list_row = ttk.Frame(frame)
    list_row.pack(fill=tk.BOTH, expand=False, pady=(0, 8))

    header_row = ttk.Frame(list_row)
    header_row.pack(fill=tk.X, pady=(0, 5))

    lbl_list = ttk.Label(header_row, text=self.tr('Batch URLs (one per line):'))
    lbl_list.pack(side=tk.LEFT)
    self.register_translatable_widget(lbl_list, 'Batch URLs (one per line):')

    btn_paste_top = ttk.Button(header_row, text=self.tr('Paste to Top'), command=self.paste_bulk_to_top)
    btn_paste_top.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_paste_top, 'Paste to Top')
    btn_paste_bottom = ttk.Button(header_row, text=self.tr('Paste to Bottom'), command=self.paste_bulk_to_bottom)
    btn_paste_bottom.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_paste_bottom, 'Paste to Bottom')
    btn_parse_all = ttk.Button(header_row, text=self.tr('Parse All'), command=self.parse_all_bulk_urls)
    btn_parse_all.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_parse_all, 'Parse All')

    # Keep clear pool in header row to the right
    btn_clear = ttk.Button(header_row, text=self.tr('Clear Pool'), command=self.clear_all_bulk_rows)
    btn_clear.pack(side=tk.RIGHT)
    self.register_translatable_widget(btn_clear, 'Clear Pool')

    dyn_container = ttk.Frame(frame)
    dyn_container.pack(fill=tk.BOTH, expand=True)
    self.bulk_canvas = tk.Canvas(dyn_container, highlightthickness=0)
    vsb = ttk.Scrollbar(dyn_container, orient='vertical', command=self.bulk_canvas.yview)
    self.bulk_scroll_frame = ttk.Frame(self.bulk_canvas)
    self.bulk_scroll_frame.bind(
        '<Configure>',
        lambda e: self.bulk_canvas.configure(scrollregion=self.bulk_canvas.bbox('all')))
    c_win = self.bulk_canvas.create_window((0, 0), window=self.bulk_scroll_frame, anchor='nw')
    self.bulk_canvas.bind('<Configure>', lambda e: self.bulk_canvas.itemconfig(c_win, width=e.width))
    self.bulk_canvas.configure(yscrollcommand=vsb.set)
    self.bulk_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)

    # Bind mousewheel events for smooth scrolling on this canvas
    self._bind_batch_mousewheel()

    # Controls row removed: Bulk Paste and Parse Batch buttons were intentionally deleted
    # per user request. Keep dynamic rows and clear button intact.
    self.bulk_rows = []
    self.add_bulk_row()

    return frame


def _bind_batch_mousewheel(self):
    self.bulk_canvas.bind('<Enter>', lambda e: self.bulk_canvas.bind_all('<MouseWheel>', self._on_batch_mousewheel))
    self.bulk_canvas.bind('<Leave>', lambda e: self.bulk_canvas.unbind_all('<MouseWheel>'))
    self.bulk_canvas.bind('<Enter>', lambda e: [
        self.bulk_canvas.bind_all('<Button-4>', self._on_batch_mousewheel),
        self.bulk_canvas.bind_all('<Button-5>', self._on_batch_mousewheel),
    ], add='+')
    self.bulk_canvas.bind('<Leave>', lambda e: [
        self.bulk_canvas.unbind_all('<Button-4>'),
        self.bulk_canvas.unbind_all('<Button-5>'),
    ], add='+')


def _on_batch_mousewheel(self, event):
    if event.num == 4:
        self.bulk_canvas.yview_scroll(-2, 'units')
    elif event.num == 5:
        self.bulk_canvas.yview_scroll(2, 'units')
    else:
        if abs(event.delta) >= 120:
            scroll_units = -2 * int(event.delta / 120)
        else:
            scroll_units = -2 * event.delta
        self.bulk_canvas.yview_scroll(scroll_units, 'units')


def _on_drag_start(self, event, row_frame):
    self._drag_data = {
        'row': row_frame,
        'y': event.y_root,
    }


def _on_drag_motion(self, event, row_frame):
    if not hasattr(self, '_drag_data') or not self._drag_data:
        return
    delta_y = event.y_root - self._drag_data['y']
    if abs(delta_y) < 10:
        return
    children = self.bulk_scroll_frame.winfo_children()
    try:
        idx = children.index(row_frame)
    except ValueError:
        return
    if delta_y > 0 and idx < len(children) - 1:
        next_row = children[idx + 1]
        if event.y_root > next_row.winfo_rooty() + (next_row.winfo_height() / 2):
            self._swap_rows(idx, idx + 1)
            self._drag_data['y'] = event.y_root
    elif delta_y < 0 and idx > 0:
        prev_row = children[idx - 1]
        if event.y_root < prev_row.winfo_rooty() + (prev_row.winfo_height() / 2):
            self._swap_rows(idx - 1, idx)
            self._drag_data['y'] = event.y_root


def _on_drag_stop(self, event, row_frame):
    self._drag_data = None
    self.trigger_autosave()


def _swap_rows(self, idx1, idx2):
    self.bulk_rows[idx1], self.bulk_rows[idx2] = self.bulk_rows[idx2], self.bulk_rows[idx1]
    for r in self.bulk_rows:
        r['frame'].pack_forget()
    for r in self.bulk_rows:
        r['frame'].pack(fill=tk.X, pady=2)


def add_bulk_row(self, initial_text='', initial_playlist='', auto_parse_playlist=False):
    row = ttk.Frame(self.bulk_scroll_frame)
    row.pack(fill=tk.X, pady=2)

    # Add drag handle
    lbl_drag = ttk.Label(row, text=' ☰ ', cursor='fleur')
    lbl_drag.pack(side=tk.LEFT, padx=(5, 2))
    lbl_drag.bind('<Button-1>', lambda e, r=row: self._on_drag_start(e, r))
    lbl_drag.bind('<B1-Motion>', lambda e, r=row: self._on_drag_motion(e, r))
    lbl_drag.bind('<ButtonRelease-1>', lambda e, r=row: self._on_drag_stop(e, r))

    var = tk.StringVar(value=initial_text)
    var.trace_add('write', self.trigger_autosave)
    entry = ttk.Entry(row, textvariable=var)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    playlist_var = tk.StringVar(value=initial_playlist)
    playlist_var.trace_add('write', self.trigger_autosave)
    playlist_entry = ttk.Entry(row, textvariable=playlist_var, width=20)
    playlist_entry.pack(side=tk.LEFT, padx=(0, 5))

    entry.bind('<Return>', lambda e: self._on_bulk_url_return(var.get().strip(), playlist_var) if var.get().strip() else None)

    # USE PLAIN ENGLISH FOR REGISTRATION - TRANSLATION HAPPENS IN apply_localization
    btn_parse = ttk.Button(row, text=self.tr('Parse'), width=8, command=lambda v=var: self._parse_single_row_url(v.get()))
    btn_parse.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_parse, 'Parse')

    if len(self.bulk_rows) == 0:
        btn_add = ttk.Button(row, text='+', width=3, command=self.add_bulk_row)
        btn_add.pack(side=tk.LEFT)
    else:
        btn_remove = ttk.Button(row, text='-', width=3, command=lambda r=row: self.remove_bulk_row(r))
        btn_remove.pack(side=tk.LEFT)
    self.bulk_rows.append({'frame': row, 'var': var, 'playlist_var': playlist_var})

    if auto_parse_playlist and initial_text.strip():
        self._fetch_playlist_title_async(initial_text.strip(), playlist_var)

    # Immediate sync for this newly added row
    self.localize_widget_tree(row)


def remove_bulk_row(self, frame):
    frame.destroy()
    self.bulk_rows = [r for r in self.bulk_rows if r['frame'] != frame]
    if not self.bulk_rows:
        self.add_bulk_row()
    self.trigger_autosave()


def remove_batch_row(self, frame):
    """Compatibility alias for previous function name."""
    self.remove_bulk_row(frame)


def _extract_urls_from_clipboard(self):
    """Extract HTTP URLs from clipboard text (case insensitive)."""
    try:
        raw = self.root.clipboard_get()
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', raw, re.IGNORECASE)
        return [u.strip() for u in urls if u.strip()]
    except Exception:
        return []


def paste_bulk_to_top(self):
    """Paste URLs from clipboard to the top of bulk rows."""
    urls = self._extract_urls_from_clipboard()
    if not urls:
        self.log_message(self.tr('No HTTP URLs found in clipboard'))
        return
    # Insert at beginning
    for url in reversed(urls):
        self.add_bulk_row_at_index(0, url, auto_parse_playlist=True)
    self.log_message(self.translate_concat('Pasted ', f'{len(urls)}') + self.tr(' URL(s) to top'))
    self.trigger_autosave()


def paste_bulk_to_bottom(self):
    """Paste URLs from clipboard to the bottom of bulk rows."""
    urls = self._extract_urls_from_clipboard()
    if not urls:
        self.log_message(self.tr('No HTTP URLs found in clipboard'))
        return
    for url in urls:
        self.add_bulk_row(url, auto_parse_playlist=True)
    self.log_message(self.translate_concat('Pasted ', f'{len(urls)}') + self.tr(' URL(s) to bottom'))
    self.trigger_autosave()


def parse_all_bulk_urls(self):
    """Serially resolve bulk-row titles; full playlist tree parse only for a single URL.

    Multiple concurrent parse_playlist threads share one tree and race. For many bulk
    URLs we fetch titles one-by-one into each row. With exactly one URL we still open
    the full playlist selector.
    """
    if getattr(self, '_parse_all_running', False):
        self.log_message(self.tr('[DEBUG] Parse All already running — ignored.'))
        return

    targets = []
    for row in getattr(self, 'bulk_rows', []):
        url = (row.get('var').get() if row.get('var') is not None else '').strip()
        if url:
            targets.append((row, url))

    if not targets:
        self.log_message(self.tr('No valid batch URLs found.'))
        return

    if len(targets) == 1:
        self._parse_single_row_url(targets[0][1])
        return

    parse_options = self.collect_parse_options()
    self.status_var.set(self.tr('Checking URL...'))
    self.log_message(self.translate_concat('Parsing bulk URLs: ', f'{len(targets)}'))
    self._parse_all_running = True

    def worker():
        ok = 0
        try:
            for index, (row, url) in enumerate(targets, start=1):
                if not getattr(self, '_parse_all_running', False):
                    break
                title_var = row.get('playlist_var')
                try:
                    cmd = [
                        *core_launcher(),
                        '--flat-playlist', '--dump-single-json', '--no-cache-dir',
                        '--ignore-no-formats-error',
                        '--remote-components', 'ejs:github',
                    ]
                    self.apply_parse_options_to_cmd(cmd, parse_options)
                    cmd.append(url)
                    env = self._subprocess_env()
                    popen_kwargs = {
                        'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE,
                        'env': env,
                        **self._subprocess_text_kwargs(),
                    }
                    if os.name == 'nt':
                        popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                    else:
                        popen_kwargs['start_new_session'] = True
                    proc = subprocess.Popen(cmd, **popen_kwargs)
                    self._parse_all_process = proc
                    try:
                        stdout_data, _stderr_data = proc.communicate(timeout=45)
                    except subprocess.TimeoutExpired:
                        self._terminate_process(proc)
                        raise
                    finally:
                        if getattr(self, '_parse_all_process', None) is proc:
                            self._parse_all_process = None

                    if not getattr(self, '_parse_all_running', False):
                        break

                    title = ''
                    if stdout_data:
                        info = json.loads(stdout_data)
                        title = (info.get('title') or info.get('id') or '').strip()
                    if title and title_var is not None:
                        self.root.after(0, lambda t=title, v=title_var: v.set(t))
                        ok += 1
                    self.log_message(f'[{index}/{len(targets)}] {title or url}')
                except Exception as e:
                    self.log_message(self.translate_concat(f'[{index}/{len(targets)}] ', str(e)))
            self.log_message(
                self.translate_concat('Batch parsed: ', f'{ok}/{len(targets)}')
                + self.tr(' URL(s) ready.'))
        finally:
            self._parse_all_running = False
            self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))

    threading.Thread(target=worker, daemon=True).start()


def add_bulk_row_at_index(self, index, initial_text='', initial_playlist='', auto_parse_playlist=False):
    """Add a bulk row at specific index position."""
    row = ttk.Frame(self.bulk_scroll_frame)

    # Add drag handle
    lbl_drag = ttk.Label(row, text=' ☰ ', cursor='fleur')
    lbl_drag.pack(side=tk.LEFT, padx=(5, 2))
    lbl_drag.bind('<Button-1>', lambda e, r=row: self._on_drag_start(e, r))
    lbl_drag.bind('<B1-Motion>', lambda e, r=row: self._on_drag_motion(e, r))
    lbl_drag.bind('<ButtonRelease-1>', lambda e, r=row: self._on_drag_stop(e, r))

    var = tk.StringVar(value=initial_text)
    var.trace_add('write', self.trigger_autosave)
    entry = ttk.Entry(row, textvariable=var)
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    playlist_var = tk.StringVar(value=initial_playlist)
    playlist_var.trace_add('write', self.trigger_autosave)
    playlist_entry = ttk.Entry(row, textvariable=playlist_var, width=20)
    playlist_entry.pack(side=tk.LEFT, padx=(0, 5))

    entry.bind('<Return>', lambda e: self._on_bulk_url_return(var.get().strip(), playlist_var) if var.get().strip() else None)

    btn_parse = ttk.Button(row, text=self.tr('Parse'), width=8, command=lambda v=var: self._parse_single_row_url(v.get()))
    btn_parse.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_parse, 'Parse')

    btn_remove = ttk.Button(row, text='-', width=3, command=lambda r=row: self.remove_bulk_row(r))
    btn_remove.pack(side=tk.LEFT)

    # Insert into list at index
    self.bulk_rows.insert(index, {'frame': row, 'var': var, 'playlist_var': playlist_var})
    self.localize_widget_tree(row)

    if auto_parse_playlist and initial_text.strip():
        self._fetch_playlist_title_async(initial_text.strip(), playlist_var)

    # Re-pack all rows in order
    for r in self.bulk_rows:
        r['frame'].pack_forget()
    for r in self.bulk_rows:
        r['frame'].pack(fill=tk.X, pady=2)


def clear_all_bulk_rows(self):
    for row in self.bulk_rows[1:]:
        row['frame'].destroy()
    if self.bulk_rows:
        self.bulk_rows = self.bulk_rows[:1]
        self.bulk_rows[0]['var'].set('')
        if 'playlist_var' in self.bulk_rows[0]:
            self.bulk_rows[0]['playlist_var'].set('')
    self.trigger_autosave()


def _restore_bulk_rows(self, urls, playlists=None):
    """Restore bulk_rows from saved URLs."""
    if not urls:
        return
    if playlists is None:
        playlists = []

    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    unique_playlists = []
    for i, url in enumerate(urls):
        norm_url = url.strip()
        if not norm_url:
            continue
        if norm_url in seen:
            continue
        seen.add(norm_url)
        unique_urls.append(url)
        pl = playlists[i] if i < len(playlists) else ''
        unique_playlists.append(pl)

    urls = unique_urls
    playlists = unique_playlists

    # Clear existing rows first
    for row in self.bulk_rows[1:]:
        row['frame'].destroy()
    if self.bulk_rows:
        self.bulk_rows[0]['var'].set(urls[0] if urls else '')
        if 'playlist_var' in self.bulk_rows[0]:
            self.bulk_rows[0]['playlist_var'].set(playlists[0] if playlists else '')
        self.bulk_rows = self.bulk_rows[:1]
        urls = urls[1:]
        playlists = playlists[1:] if playlists else []
    for i, url in enumerate(urls):
        pl = playlists[i] if i < len(playlists) else ''
        self.add_bulk_row(url, initial_playlist=pl)


def _on_bulk_url_return(self, url, title_var):
    if url:
        self._fetch_playlist_title_async(url, title_var)


def _fetch_playlist_title_async(self, url, title_var):
    cookies_from_browser = self.get_control_text('cookies_from_browser')
    cookies = self.get_control_text('cookies')

    def worker():
        try:
            cmd = [*core_launcher(), '--flat-playlist', '--dump-single-json', url]
            if cookies_from_browser:
                cmd.extend(['--cookies-from-browser', cookies_from_browser])
            if cookies:
                cmd.extend(['--cookies', cookies])

            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=15, env=self._subprocess_env(), **self._subprocess_text_kwargs())
            if result.stdout:
                info = json.loads(result.stdout)
                title = info.get('title')
                if title:
                    self.root.after(0, lambda: title_var.set(title))
        except Exception:
            pass
    threading.Thread(target=worker, daemon=True).start()


def _parse_single_row_url(self, url):
    url = (url or '').strip()
    if not url:
        return
    self._is_from_bulk_parse_flag = True
    self.url_var.set(url)
    self.parse_playlist()


def parse_single_url(self, url):
    """Compatibility alias for previous function name."""
    self._parse_single_row_url(url)


def parse_batch(self):
    """Parse all batch inputs and normalize them into the main batch input box."""
    file_path = self.get_batch_file_value()
    row_urls = self.get_bulk_urls()
    thread = threading.Thread(target=self._parse_batch_worker, args=(file_path, row_urls), daemon=True)
    thread.start()


def _parse_batch_worker(self, file_path, row_urls):
    urls = []

    if file_path and os.path.isfile(file_path):
        try:
            urls.extend(self.read_batch_file_urls(file_path))
        except Exception as e:
            self.log_message(self.translate_concat('Error reading batch file: ', str(e)))
    elif file_path:
        urls.extend(line.strip() for line in file_path.splitlines() if line.strip())

    urls.extend(row_urls)

    normalized = self.dedupe_preserve_order(urls)

    if not normalized:
        self.log_message(self.tr('No valid batch URLs found.'))
        self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))
        return

    self.root.after(0, lambda: self._restore_bulk_rows(normalized))
    self.root.after(0, lambda: self.batch_file_var.set(''))
    self.log_message(self.translate_concat('Batch parsed: ', f'{len(normalized)}') + self.tr(' URL(s) ready.'))
    self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))


def create_playlist_tab(self, frame=None):
    """Create Playlist Select tab using efficient Treeview"""
    frame = frame or ttk.Frame(self.notebook, padding='10')

    # Top control frame
    top_ctrl = ttk.Frame(frame)
    top_ctrl.pack(fill=tk.X, pady=(0, 5))

    # Use three buttons for better control
    btn_sel_all = ttk.Button(top_ctrl, text='Select All', command=lambda: self._on_playlist_select_all('all'))
    btn_sel_all.pack(side=tk.LEFT, padx=(0, 2))
    self.register_translatable_widget(btn_sel_all, 'Select All')

    btn_sel_none = ttk.Button(top_ctrl, text='Deselect All', command=lambda: self._on_playlist_select_all('none'))
    btn_sel_none.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_sel_none, 'Deselect All')

    btn_sel_inv = ttk.Button(top_ctrl, text='Invert Select', command=lambda: self._on_playlist_select_all('invert'))
    btn_sel_inv.pack(side=tk.LEFT, padx=2)
    self.register_translatable_widget(btn_sel_inv, 'Invert Select')

    # Restore playlist option checkboxes (deduplicated) so they are visible once
    # again in the playlist tab. Keep behavior consistent with internal vars.
    self.playlist_reverse_var = tk.BooleanVar(value=False)
    cb_rev = ttk.Checkbutton(
        top_ctrl,
        text='Reverse order',
        variable=self.playlist_reverse_var,
        command=self._on_playlist_option_changed,
    )
    cb_rev.pack(side=tk.LEFT, padx=(20, 0))
    self.register_translatable_widget(cb_rev, 'Reverse order')

    self.playlist_exclude_private_var = tk.BooleanVar(value=True)
    cb_priv = ttk.Checkbutton(
        top_ctrl,
        text='Exclude private videos',
        variable=self.playlist_exclude_private_var,
        command=self._on_playlist_option_changed,
    )
    cb_priv.pack(side=tk.LEFT, padx=(20, 0))
    self.register_translatable_widget(cb_priv, 'Exclude private videos')

    # TREEVIEW for heavy listing
    tree_frame = ttk.Frame(frame)
    tree_frame.pack(fill=tk.BOTH, expand=True)

    columns = ('status', 'index', 'title')
    self.playlist_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='extended')

    # Define headings
    self.playlist_tree.heading('status', text=' ', anchor=tk.CENTER)
    self.playlist_tree.heading('index', text='#')
    self.playlist_tree.heading('title', text='Title')

    # Define columns
    self.playlist_tree.column('status', width=40, anchor=tk.CENTER, stretch=False)
    self.playlist_tree.column('index', width=60, anchor=tk.CENTER, stretch=False)
    self.playlist_tree.column('title', width=400, anchor=tk.W)

    # Scrollbar
    tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.playlist_tree.yview)
    self.playlist_tree.configure(yscrollcommand=tree_scroll.set)

    self.playlist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Bind events for interaction
    self.playlist_tree.bind('<ButtonRelease-1>', self._on_tree_click)
    self.playlist_tree.bind('<space>', self._on_tree_space)

    return frame


def _on_tree_click(self, event):
    item = self.playlist_tree.identify_row(event.y)
    if item:
        self._toggle_tree_item(item)


def _on_tree_space(self, event):
    items = self.playlist_tree.selection()
    if items:
        for item in items:
            self._toggle_tree_item(item)


def _toggle_tree_item(self, item):
    values = list(self.playlist_tree.item(item, 'values'))
    if values:
        values[0] = '☐' if values[0] == '☑' else '☑'
        self.playlist_tree.item(item, values=values)


def _on_playlist_select_all(self, mode='all'):
    for item in self.playlist_tree.get_children():
        values = list(self.playlist_tree.item(item, 'values'))
        if mode == 'all':
            values[0] = '☑'
        elif mode == 'none':
            values[0] = '☐'
        elif mode == 'invert':
            values[0] = '☐' if values[0] == '☑' else '☑'
        self.playlist_tree.item(item, values=values)


def _on_playlist_mousewheel(self, event):
    # Only scroll if the playlist tab is active
    if self.notebook.select() == str(self.playlist_tab_frame):
        if event.num == 4:  # Linux scroll up
            self.playlist_tree.yview_scroll(-1, 'units')
        elif event.num == 5:  # Linux scroll down
            self.playlist_tree.yview_scroll(1, 'units')
        else:  # Windows/Mac
            self.playlist_tree.yview_scroll(int(-1 * (event.delta)), 'units')


def _on_playlist_option_changed(self):
    if hasattr(self, 'playlist_entries_data') and self.playlist_entries_data:
        self.root.after(0, self._show_playlist_tab, 'Playlist')


