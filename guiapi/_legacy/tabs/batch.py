"""Tab: batch"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk, scrolledtext

if TYPE_CHECKING:
    pass


class BatchDownloadMixin:
    """Mixin for batch download tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        browse_batch_file: Any
        clear_all_bulk_rows: Any
        _parse_single_row_url: Any
        localize_widget_tree: Any
        bulk_scroll_frame: Any
        bulk_rows: list

    def create_batch_download_tab(self, frame=None):
        """Create Batch Download tab."""
        frame = frame or ttk.Frame(self.notebook, padding='10')

        file_row = ttk.Frame(frame)
        file_row.pack(fill=tk.X, pady=(0, 8))
        lbl_file = ttk.Label(file_row, text=self.tr('Batch file path:'))
        lbl_file.pack(side=tk.LEFT)
        self.register_translatable_widget(lbl_file, 'Batch file path:')

        self.batch_file_var = tk.StringVar()
        self.batch_file_var.trace_add('write', self.trigger_autosave)
        self.batch_file_input = ttk.Entry(file_row, textvariable=self.batch_file_var)
        self.batch_file_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 5))
        btn_browse = ttk.Button(file_row, text=self.tr('Browse...'), command=self.browse_batch_file)
        btn_browse.pack(side=tk.LEFT)
        self.register_translatable_widget(btn_browse, 'Browse...')

        list_row = ttk.Frame(frame)
        list_row.pack(fill=tk.BOTH, expand=False, pady=(0, 8))

        header_row = ttk.Frame(list_row)
        header_row.pack(fill=tk.X, pady=(0, 5))

        lbl_list = ttk.Label(header_row, text=self.tr('Batch URLs (one per line):'))
        lbl_list.pack(side=tk.LEFT)
        self.register_translatable_widget(lbl_list, 'Batch URLs (one per line):')

        # Control buttons will be placed below the batch URLs text area (added after the text widget)

        # Keep clear pool in header row to the right
        btn_clear = ttk.Button(header_row, text=self.tr('Clear Pool'), command=self.clear_all_bulk_rows)
        btn_clear.pack(side=tk.RIGHT)
        self.register_translatable_widget(btn_clear, 'Clear Pool')

        self.batch_urls_text = scrolledtext.ScrolledText(list_row, height=5, wrap=tk.WORD)
        self.batch_urls_text.pack(fill=tk.X, expand=True)
        self.batch_urls_text.bind('<KeyRelease>', self.trigger_autosave)

        # NOTE: Controls row for paste/parse will be placed after the dynamic rows

        dyn_container = ttk.Frame(frame)
        dyn_container.pack(fill=tk.BOTH, expand=True)
        self.bulk_canvas = tk.Canvas(dyn_container, highlightthickness=0)
        vsb = ttk.Scrollbar(dyn_container, orient='vertical', command=self.bulk_canvas.yview)
        self.bulk_scroll_frame = ttk.Frame(self.bulk_canvas)
        self.bulk_scroll_frame.bind(
            '<Configure>',
            lambda e: self.bulk_canvas.configure(scrollregion=self.bulk_canvas.bbox('all')))
        c_win = self.bulk_canvas.create_window((0, 0), window=self.bulk_scroll_frame, anchor='nw')
        self.bulk_canvas.bind('<Configure>', lambda e: self.bulk_canvas.itemconfig(c_win, width=e.width))
        self.bulk_canvas.configure(yscrollcommand=vsb.set)
        self.bulk_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Controls row removed: Bulk Paste and Parse Batch buttons were intentionally deleted
        # per user request. Keep dynamic rows and clear button intact.
        self.bulk_rows = []
        self.add_bulk_row()

        return frame

    def add_bulk_row(self, initial_text=''):
        row = ttk.Frame(self.bulk_scroll_frame)
        row.pack(fill=tk.X, pady=2)
        var = tk.StringVar(value=initial_text)
        var.trace_add('write', self.trigger_autosave)
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # USE PLAIN ENGLISH FOR REGISTRATION - TRANSLATION HAPPENS IN apply_localization
        btn_parse = ttk.Button(row, text=self.tr('Parse'), width=8, command=lambda v=var: self._parse_single_row_url(v.get()))
        btn_parse.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_parse, 'Parse')

        if len(self.bulk_rows) == 0:
            btn_add = ttk.Button(row, text='+', width=3, command=self.add_bulk_row)
            btn_add.pack(side=tk.LEFT)
        else:
            btn_remove = ttk.Button(row, text='-', width=3, command=lambda r=row: self.remove_bulk_row(r))
            btn_remove.pack(side=tk.LEFT)
        self.bulk_rows.append({'frame': row, 'var': var})

        # Immediate sync for this newly added row
        self.localize_widget_tree(row)

    def remove_bulk_row(self, frame):
        frame.destroy()
        self.bulk_rows = [r for r in self.bulk_rows if r['frame'] != frame]
        if not self.bulk_rows:
            self.add_bulk_row()

    def remove_batch_row(self, frame):
        """Compatibility alias for previous function name."""
        self.remove_bulk_row(frame)
