"""Tab: geo"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class GeoRestrictionMixin:
    """Mixin for geo tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        geo_bypass: Any
        geo_bypass_country: Any
        geo_bypass_ip_block: Any
        geo_verification_proxy: Any
        _stateful_controls: Any

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
