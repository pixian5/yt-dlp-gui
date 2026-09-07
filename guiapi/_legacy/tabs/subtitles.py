"""Tab: subtitles"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class SubtitleTabMixin:
    """Mixin for subtitles tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        write_subs: Any
        write_auto_subs: Any
        list_subs: Any
        sub_format: Any
        sub_langs: Any
        embed_subs: Any
        no_embed_subs: Any
        embed_thumbnail: Any
        no_embed_thumbnail: Any
        _stateful_controls: Any

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
