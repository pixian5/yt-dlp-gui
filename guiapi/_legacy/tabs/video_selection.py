"""Tab: video_selection"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class VideoSelectionMixin:
    """Mixin for video_selection tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        playlist_items: Any
        playlist_start: Any
        playlist_end: Any
        playlist_reverse: Any
        match_title: Any
        reject_title: Any
        min_filesize: Any
        max_filesize: Any
        date: Any
        date_before: Any
        date_after: Any
        min_views: Any
        max_views: Any
        match_filter: Any
        _stateful_controls: Any

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
