"""Tab: filesystem"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class FilesystemTabMixin:
    """Mixin for filesystem tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        browse_output_dir: Any
        browse_info_json: Any
        browse_cache_dir: Any
        output_template: Any
        output_dir: Any
        paths: Any
        load_info_json: Any
        cache_dir: Any
        restrict_filenames: Any
        no_restrict_filenames: Any
        windows_filenames: Any
        no_overwrites: Any
        force_overwrites: Any
        continue_dl: Any
        no_continue: Any
        no_part: Any
        no_mtime: Any
        write_description: Any
        write_info_json: Any
        write_annotations: Any
        write_comments: Any
        no_cache_dir: Any
        rm_cache_dir: Any
        playlist_subdir: Any
        _stateful_controls: Any

    def create_filesystem_tab(self, frame=None):
        """Create Filesystem Options tab"""
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

        ttk.Label(scrollable_frame, text='Output template:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.output_template = ttk.Entry(scrollable_frame, width=50)
        self.output_template.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        ttk.Label(scrollable_frame, text='(e.g., "%(title)s.%(ext)s")').grid(row=row, column=3, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(scrollable_frame, text='Output directory:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        output_frame = ttk.Frame(scrollable_frame)
        output_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
        self.output_dir = ttk.Entry(output_frame, width=50)
        self.output_dir.pack(side=tk.LEFT)
        ttk.Button(output_frame, text='Browse...', command=self.browse_output_dir).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        ttk.Label(scrollable_frame, text='Paths configuration:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.paths = ttk.Entry(scrollable_frame, width=50)
        self.paths.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        row += 1

        self.restrict_filenames = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Restrict filenames to ASCII (--restrict-filenames)',
                        variable=self.restrict_filenames).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_restrict_filenames = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Allow Unicode in filenames (--no-restrict-filenames)',
                        variable=self.no_restrict_filenames).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.playlist_subdir = tk.BooleanVar()
        ttk.Checkbutton(
            scrollable_frame,
            text='Create playlist subfolder for playlist downloads',
            variable=self.playlist_subdir,
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.windows_filenames = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Force Windows-compatible filenames (--windows-filenames)',
                        variable=self.windows_filenames).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_overwrites = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Do not overwrite files (--no-overwrites)',
                        variable=self.no_overwrites).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.force_overwrites = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Force overwrite files (--force-overwrites)',
                        variable=self.force_overwrites).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.continue_dl = tk.BooleanVar(value=True)
        ttk.Checkbutton(scrollable_frame, text='Continue partially downloaded files (--continue)',
                        variable=self.continue_dl).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_continue = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Do not continue downloads (--no-continue)',
                        variable=self.no_continue).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_part = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Do not use .part files (--no-part)',
                        variable=self.no_part).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_mtime = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Do not use Last-modified header (--no-mtime)',
                        variable=self.no_mtime).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.write_description = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Write description to .description file (--write-description)',
                        variable=self.write_description).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.write_info_json = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Write metadata to .info.json file (--write-info-json)',
                        variable=self.write_info_json).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.write_annotations = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Write annotations to .annotations.xml (--write-annotations)',
                        variable=self.write_annotations).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.write_comments = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Write comments to .comments.json (--write-comments)',
                        variable=self.write_comments).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Load info JSON:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        load_frame = ttk.Frame(scrollable_frame)
        load_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
        self.load_info_json = ttk.Entry(load_frame, width=50)
        self.load_info_json.pack(side=tk.LEFT)
        ttk.Button(load_frame, text='Browse...', command=self.browse_info_json).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        ttk.Label(scrollable_frame, text='Cache directory:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        cache_frame = ttk.Frame(scrollable_frame)
        cache_frame.grid(row=row, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
        self.cache_dir = ttk.Entry(cache_frame, width=50)
        self.cache_dir.pack(side=tk.LEFT)
        ttk.Button(cache_frame, text='Browse...', command=self.browse_cache_dir).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        self.no_cache_dir = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Disable filesystem caching (--no-cache-dir)',
                        variable=self.no_cache_dir).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.rm_cache_dir = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Delete cache directory contents (--rm-cache-dir)',
                        variable=self.rm_cache_dir).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1
