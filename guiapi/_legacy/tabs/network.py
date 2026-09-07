"""Tab: network"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class NetworkTabMixin:
    """Mixin for network tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        proxy: Any
        socket_timeout: Any
        source_address: Any
        force_ipv4: Any
        force_ipv6: Any
        enable_file_urls: Any
        _stateful_controls: Any

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

        ttk.Label(scrollable_frame, text='Sleep interval for requests (seconds):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.sleep_interval_requests = ttk.Entry(scrollable_frame, width=10)
        self.sleep_interval_requests.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Sleep interval for subtitles (seconds):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.sleep_interval_subtitles = ttk.Entry(scrollable_frame, width=10)
        self.sleep_interval_subtitles.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Rate limit (e.g., "50K" or "4.2M"):').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.rate_limit = ttk.Entry(scrollable_frame, width=15)
        self.rate_limit.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
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
