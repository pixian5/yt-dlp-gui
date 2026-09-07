"""Tab: extractor"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class ExtractorTabMixin:
    """Mixin for extractor tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        browse_cookies: Any
        extractor_args: Any
        extractor_retries: Any
        allow_dynamic_mpd: Any
        ignore_dynamic_mpd: Any
        hls_split_discontinuity: Any
        cookies_from_browser: Any
        cookies: Any
        _stateful_controls: Any

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
