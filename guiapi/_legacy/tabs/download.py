"""Tab: download"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class DownloadTabMixin:
    """Mixin for download tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        concurrent_fragments: Any
        limit_rate: Any
        buffer_size: Any
        http_chunk_size: Any
        external_downloader: Any
        external_downloader_args: Any
        no_resize_buffer: Any
        test: Any
        hls_prefer_native: Any
        hls_prefer_ffmpeg: Any
        hls_use_mpegts: Any
        _stateful_controls: Any

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

        ttk.Label(scrollable_frame, text='Limit download rate:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.limit_rate = ttk.Entry(scrollable_frame, width=15)
        self.limit_rate.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(scrollable_frame, text='(e.g., 50K or 4.2M)').grid(row=row, column=2, sticky=tk.W, pady=5)
        row += 1

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
