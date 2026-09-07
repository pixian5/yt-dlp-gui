"""Tab: postprocessing"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class PostprocessingTabMixin:
    """Mixin for postprocessing tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        extract_audio: Any
        audio_format: Any
        audio_quality: Any
        recode_video: Any
        remux_video: Any
        keep_video: Any
        no_keep_video: Any
        embed_metadata: Any
        embed_chapters: Any
        embed_info_json: Any
        add_metadata: Any
        metadata_from_title: Any
        parse_metadata: Any
        ffmpeg_location: Any
        browse_ffmpeg: Any
        postprocessor_args: Any
        _stateful_controls: Any

    def create_postprocessing_tab(self, frame=None):
        """Create Post-processing Options tab"""
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

        self.extract_audio = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Extract audio (-x, --extract-audio)',
                        variable=self.extract_audio).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Audio format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.audio_format = ttk.Combobox(scrollable_frame, width=15,
                                         values=['', 'best', 'aac', 'm4a', 'mp3', 'opus', 'vorbis', 'wav', 'flac', 'alac'],
                                         state='readonly')
        self.audio_format.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Audio quality:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.audio_quality = ttk.Entry(scrollable_frame, width=10)
        self.audio_quality.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(scrollable_frame, text='(0-10, 0 = best)').grid(row=row, column=2, sticky=tk.W, pady=5)
        row += 1

        ttk.Label(scrollable_frame, text='Recode video format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.recode_video = ttk.Combobox(scrollable_frame, width=15,
                                         values=['', 'mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi'],
                                         state='readonly')
        self.recode_video.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Remux video format:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.remux_video = ttk.Combobox(scrollable_frame, width=15,
                                        values=['', 'mp4', 'flv', 'ogg', 'webm', 'mkv', 'avi', 'mov'],
                                        state='readonly')
        self.remux_video.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        self.keep_video = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Keep video file after conversion (--keep-video)',
                        variable=self.keep_video).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.no_keep_video = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Do not keep video file (--no-keep-video)',
                        variable=self.no_keep_video).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.embed_metadata = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Embed metadata (--embed-metadata)',
                        variable=self.embed_metadata).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.embed_chapters = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Embed chapter markers (--embed-chapters)',
                        variable=self.embed_chapters).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.embed_info_json = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Embed info.json (--embed-info-json)',
                        variable=self.embed_info_json).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        self.add_metadata = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Add metadata to file (--add-metadata)',
                        variable=self.add_metadata).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Metadata fields:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.metadata_from_title = ttk.Entry(scrollable_frame, width=40)
        self.metadata_from_title.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Parse metadata:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.parse_metadata = ttk.Entry(scrollable_frame, width=40)
        self.parse_metadata.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='FFmpeg location:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        ffmpeg_frame = ttk.Frame(scrollable_frame)
        ffmpeg_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        self.ffmpeg_location = ttk.Entry(ffmpeg_frame, width=40)
        self.ffmpeg_location.pack(side=tk.LEFT)
        ttk.Button(ffmpeg_frame, text='Browse...', command=self.browse_ffmpeg).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        ttk.Label(scrollable_frame, text='Post-processor args:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.postprocessor_args = ttk.Entry(scrollable_frame, width=50)
        self.postprocessor_args.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        row += 1
