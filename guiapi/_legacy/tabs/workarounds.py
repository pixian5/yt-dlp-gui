"""Tab: workarounds"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class WorkaroundsTabMixin:
    """Mixin for workarounds tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        encoding: Any
        no_check_certificate: Any
        prefer_insecure: Any
        user_agent: Any
        referer: Any
        add_header: Any
        bidi_workaround: Any
        sleep_requests: Any
        legacy_server_connect: Any
        _stateful_controls: Any

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

        ttk.Label(scrollable_frame, text='Sleep before requests:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.sleep_requests = ttk.Entry(scrollable_frame, width=10)
        self.sleep_requests.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        self.legacy_server_connect = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Use legacy server connect (--legacy-server-connect)',
                        variable=self.legacy_server_connect).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1
