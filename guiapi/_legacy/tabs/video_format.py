"""Tab: video_format"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class VideoFormatMixin:
    """Mixin for video_format tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        format: Any
        format_sort: Any
        prefer_free_formats: Any
        check_formats: Any
        merge_output_format: Any
        video_multistreams: Any
        audio_multistreams: Any
        _stateful_controls: Any

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
        self.format = ttk.Entry(scrollable_frame, width=50)
        self.format.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        ttk.Label(scrollable_frame, text='(e.g., "bestvideo+bestaudio")').grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(scrollable_frame, text='Quick Select Resolution:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.res_var = tk.StringVar()
        res_options = ['Best (Auto)', '4K (2160p)', '2K (1440p)', '1080p 60fps', '1080p', '720p 60fps', '720p', '480p', '360p']
        self.res_selector = ttk.Combobox(scrollable_frame, textvariable=self.res_var, width=30,
                                         values=[self.tr(opt) for opt in res_options], state='readonly')
        self.res_selector.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        self.res_selector.bind('<<ComboboxSelected>>', self._on_res_selected)
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

    def _on_res_selected(self, event=None):
        val = self.res_var.get()
        # Find original key from translated value
        original_key = None
        res_options = ['Best (Auto)', '4K (2160p)', '2K (1440p)', '1080p 60fps', '1080p', '720p 60fps', '720p', '480p', '360p']
        for opt in res_options:
            if self.tr(opt) == val:
                original_key = opt
                break

        if not original_key:
            return

        mapping = {
            'Best (Auto)': 'bestvideo+bestaudio/best',
            '4K (2160p)': 'bv*[height<=2160]+ba',
            '2K (1440p)': 'bv*[height<=1440]+ba',
            '1080p 60fps': 'bv*[height<=1080][fps<=60]+ba',
            '1080p': 'bv*[height<=1080]+ba',
            '720p 60fps': 'bv*[height<=720][fps<=60]+ba',
            '720p': 'bv*[height<=720]+ba',
            '480p': 'bv*[height<=480]+ba',
            '360p': 'bv*[height<=360]+ba',
        }
        res_code = mapping.get(original_key)
        if res_code:
            self.format.delete(0, tk.END)
            self.format.insert(0, res_code)
