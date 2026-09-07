"""Tab: advanced"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk, scrolledtext

if TYPE_CHECKING:
    pass


class AdvancedTabMixin:
    """Mixin for advanced tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        generate_command: Any
        copy_command: Any
        raw_args: Any
        generated_cmd: Any
        _stateful_controls: Any

    def create_advanced_tab(self, frame=None):
        """Create Advanced Options tab"""
        frame = frame or ttk.Frame(self.notebook, padding='10')

        row = 0

        ttk.Label(frame, text='Raw command-line arguments:').grid(row=row, column=0, sticky=tk.NW, pady=5, padx=5)
        self.raw_args = scrolledtext.ScrolledText(frame, width=80, height=10, wrap=tk.WORD)
        self.raw_args.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(frame, text='(One argument per line or space-separated)').grid(row=row + 1, column=1, sticky=tk.W, padx=5)
        row += 2

        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        row += 1

        ttk.Label(frame, text='Generated command:').grid(row=row, column=0, sticky=tk.NW, pady=5, padx=5)
        self.generated_cmd = scrolledtext.ScrolledText(frame, width=80, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.generated_cmd.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=5)
        row += 1

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=1, pady=10)
        ttk.Button(button_frame, text='Generate Command', command=self.generate_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='Copy to Clipboard', command=self.copy_command).pack(side=tk.LEFT, padx=5)
        row += 1

    # File browser methods
