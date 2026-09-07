"""Tab: thumbnail"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class ThumbnailTabMixin:
    """Mixin for thumbnail tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        write_thumbnail: Any
        write_all_thumbnails: Any
        list_thumbnails: Any
        convert_thumbnails: Any
        _stateful_controls: Any

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
