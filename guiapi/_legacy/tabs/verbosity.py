"""Tab: verbosity"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class VerbosityTabMixin:
    """Mixin for verbosity tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        register_stateful_controls: Any
        trigger_autosave: Any
        quiet: Any
        verbose: Any
        simulate: Any
        skip_download: Any
        get_title: Any
        get_id: Any
        get_url: Any
        get_thumbnail: Any
        get_description: Any
        get_duration: Any
        get_filename: Any
        get_format: Any
        dump_json: Any
        dump_single_json: Any
        print_json: Any
        no_progress: Any
        console_title: Any
        progress_template: Any
        _stateful_controls: Any

    def create_verbosity_tab(self, frame=None):
        """Create Verbosity and Simulation tab"""
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

        self.quiet = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Quiet mode (-q, --quiet)',
                        variable=self.quiet).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_warnings = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='No warnings (--no-warnings)',
                        variable=self.no_warnings).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.verbose = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Verbose output (-v, --verbose)',
                        variable=self.verbose).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.simulate = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Simulate, do not download (-s, --simulate)',
                        variable=self.simulate).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.skip_download = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Skip download (--skip-download)',
                        variable=self.skip_download).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_title = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get title (--get-title)',
                        variable=self.get_title).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_id = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get ID (--get-id)',
                        variable=self.get_id).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_url = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get URL (--get-url)',
                        variable=self.get_url).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_thumbnail = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get thumbnail URL (--get-thumbnail)',
                        variable=self.get_thumbnail).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_description = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get description (--get-description)',
                        variable=self.get_description).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_duration = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get duration (--get-duration)',
                        variable=self.get_duration).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_filename = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get filename (--get-filename)',
                        variable=self.get_filename).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.get_format = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Get format (--get-format)',
                        variable=self.get_format).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.dump_json = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Dump JSON info (--dump-json)',
                        variable=self.dump_json).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.dump_single_json = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Dump single JSON (--dump-single-json)',
                        variable=self.dump_single_json).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.print_json = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Print JSON info (--print-json)',
                        variable=self.print_json).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.progress = tk.BooleanVar(value=True)
        ttk.Checkbutton(scrollable_frame, text='Show progress (--progress)',
                        variable=self.progress).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_progress = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Hide progress (--no-progress)',
                        variable=self.no_progress).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.console_title = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Display progress in console title (--console-title)',
                        variable=self.console_title).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        row += 1

        before = set(self.__dict__)
        self.progress_template = ttk.Entry(scrollable_frame, width=50)
        ttk.Label(scrollable_frame, text=self.tr('Progress template:')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.progress_template.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        self.register_stateful_controls(set(self.__dict__) - before)
        row += 1

        before2 = set(self.__dict__)
        ttk.Label(scrollable_frame, text=self.tr('Metadata language:')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.metadata_lang = ttk.Combobox(
            scrollable_frame,
            values=[self.tr('Default (Auto)'), 'zh-CN', 'zh-TW', 'zh-HK', 'en', 'ja', 'ko'],
            state='readonly',
            width=20,
        )
        self.metadata_lang.set('zh-CN')
        self.metadata_lang.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        self.register_stateful_controls(set(self.__dict__) - before2)
        row += 1
