"""Tab: sponsorblock"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

from guiapi.constants import SB_CATEGORIES

if TYPE_CHECKING:
    pass


class SponsorblockTabMixin:
    """Mixin for sponsorblock tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        sponsorblock_mark: Any
        sponsorblock_remove: Any
        sponsorblock_chapter_title: Any
        sponsorblock_api: Any
        no_sponsorblock: Any
        sb_remove_vars: Any
        sb_mark_vars: Any
        _stateful_controls: Any

    def create_sponsorblock_tab(self, frame=None):
        """Create SponsorBlock Options tab with category checkboxes and selection controls"""
        frame = frame or ttk.Frame(self.notebook, padding='10')

        # Scrollable container for many options
        canvas = tk.Canvas(frame, highlightthickness=0)
        vsb = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        c_win = canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(c_win, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        row = 0

        # Main switches
        self.sponsorblock_mark = tk.BooleanVar()
        cb_m = ttk.Checkbutton(scroll_frame, text='Mark SponsorBlock chapters (--sponsorblock-mark)', variable=self.sponsorblock_mark)
        cb_m.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        self.register_translatable_widget(cb_m, 'Mark SponsorBlock chapters (--sponsorblock-mark)')
        row += 1

        self.sponsorblock_remove = tk.BooleanVar()
        cb_r = ttk.Checkbutton(scroll_frame, text='Remove SponsorBlock segments (--sponsorblock-remove)', variable=self.sponsorblock_remove)
        cb_r.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        self.register_translatable_widget(cb_r, 'Remove SponsorBlock segments (--sponsorblock-remove)')
        row += 1

        self.no_sponsorblock = tk.BooleanVar()
        cb_nosb = ttk.Checkbutton(scroll_frame, text='Disable SponsorBlock (--no-sponsorblock)', variable=self.no_sponsorblock)
        cb_nosb.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        self.register_translatable_widget(cb_nosb, 'Disable SponsorBlock (--no-sponsorblock)')
        row += 1

        ttk.Separator(scroll_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky='ew', pady=10)
        row += 1

        # Categories to REMOVE
        rem_lf = ttk.LabelFrame(scroll_frame, text='SponsorBlock categories to remove:', padding=10)
        rem_lf.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        self.register_translatable_widget(rem_lf, 'SponsorBlock categories to remove:')

        # Selection buttons for Remove group
        rem_ctrl = ttk.Frame(rem_lf)
        rem_ctrl.pack(fill=tk.X, pady=(0, 5))

        btn_rm_all = ttk.Button(rem_ctrl, text='Select All', command=lambda: self._set_sb_group('remove', True))
        btn_rm_all.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_rm_all, 'Select All')

        btn_rm_none = ttk.Button(rem_ctrl, text='Deselect All', command=lambda: self._set_sb_group('remove', False))
        btn_rm_none.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_rm_none, 'Deselect All')

        btn_rm_inv = ttk.Button(rem_ctrl, text='Invert Select', command=lambda: self._set_sb_group('remove', 'invert'))
        btn_rm_inv.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_rm_inv, 'Invert Select')

        rem_grid = ttk.Frame(rem_lf)
        rem_grid.pack(fill=tk.X)
        self.sb_remove_vars = {}
        for idx, cat in enumerate(SB_CATEGORIES):
            var = tk.BooleanVar()
            self.sb_remove_vars[cat] = var
            self._stateful_controls[f'sb_remove_{cat}'] = var
            cb = ttk.Checkbutton(rem_grid, text=cat, variable=var)
            cb.grid(row=idx // 2, column=idx % 2, sticky=tk.W, padx=10, pady=2)
            self.register_translatable_widget(cb, cat)
        row += 1

        # Categories to MARK
        mark_lf = ttk.LabelFrame(scroll_frame, text='SponsorBlock categories to mark:', padding=10)
        mark_lf.grid(row=row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        self.register_translatable_widget(mark_lf, 'SponsorBlock categories to mark:')

        # Selection buttons for Mark group
        mark_ctrl = ttk.Frame(mark_lf)
        mark_ctrl.pack(fill=tk.X, pady=(0, 5))

        btn_mk_all = ttk.Button(mark_ctrl, text='Select All', command=lambda: self._set_sb_group('mark', True))
        btn_mk_all.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_mk_all, 'Select All')

        btn_mk_none = ttk.Button(mark_ctrl, text='Deselect All', command=lambda: self._set_sb_group('mark', False))
        btn_mk_none.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_mk_none, 'Deselect All')

        btn_mk_inv = ttk.Button(mark_ctrl, text='Invert Select', command=lambda: self._set_sb_group('mark', 'invert'))
        btn_mk_inv.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_mk_inv, 'Invert Select')

        mark_grid = ttk.Frame(mark_lf)
        mark_grid.pack(fill=tk.X)
        self.sb_mark_vars = {}
        for idx, cat in enumerate(SB_CATEGORIES):
            var = tk.BooleanVar()
            self.sb_mark_vars[cat] = var
            self._stateful_controls[f'sb_mark_{cat}'] = var
            cb = ttk.Checkbutton(mark_grid, text=cat, variable=var)
            cb.grid(row=idx // 2, column=idx % 2, sticky=tk.W, padx=10, pady=2)
            self.register_translatable_widget(cb, cat)
        row += 1

        # Other SB settings
        ttk.Label(scroll_frame, text='SponsorBlock chapter title:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.sponsorblock_chapter_title = ttk.Entry(scroll_frame, width=40)
        self.sponsorblock_chapter_title.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        self.register_translatable_widget(scroll_frame.grid_slaves(row=row, column=0)[0], 'SponsorBlock chapter title:')
        row += 1

        ttk.Label(scroll_frame, text='SponsorBlock API URL:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.sponsorblock_api = ttk.Entry(scroll_frame, width=50)
        self.sponsorblock_api.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        self.register_translatable_widget(scroll_frame.grid_slaves(row=row, column=0)[0], 'SponsorBlock API URL:')
        row += 1

    def _set_sb_group(self, group, state):
        vars_dict = self.sb_remove_vars if group == 'remove' else self.sb_mark_vars
        for var in vars_dict.values():
            if state == 'invert':
                var.set(not var.get())
            else:
                var.set(state)
