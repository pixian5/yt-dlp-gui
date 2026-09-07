"""Tab: general"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class GeneralTabMixin:
    """Mixin for general tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        browse_config_file: Any
        browse_archive_file: Any
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
        _stateful_controls: Any

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

        self.no_warnings = tk.BooleanVar()
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
        self.extract_flat = ttk.Combobox(scrollable_frame, width=20,
                                         values=['', 'in_playlist', 'discard_in_playlist'],
                                         state='readonly')
        self.extract_flat.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
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
