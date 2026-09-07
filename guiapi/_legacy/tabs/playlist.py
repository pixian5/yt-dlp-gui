"""Tab: playlist"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class PlaylistTabMixin:
    """Mixin for playlist tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        root: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        playlist_tree: Any
        playlist_tab_frame: Any
        playlist_entries_data: Any
        playlist_exclude_private_var: Any
        playlist_reverse_var: Any
        select_all_playlist: Any
        deselect_all_playlist: Any
        invert_selection_playlist: Any
        quick_resolution_select: Any
        res_selector: Any
        _show_playlist_tab: Any
        _stateful_controls: Any

    def create_playlist_tab(self, frame=None):
        """Create Playlist Select tab using efficient Treeview"""
        frame = frame or ttk.Frame(self.notebook, padding='10')

        # Top control frame
        top_ctrl = ttk.Frame(frame)
        top_ctrl.pack(fill=tk.X, pady=(0, 5))

        # Use three buttons for better control
        btn_sel_all = ttk.Button(top_ctrl, text='Select All', command=lambda: self._on_playlist_select_all('all'))
        btn_sel_all.pack(side=tk.LEFT, padx=(0, 2))
        self.register_translatable_widget(btn_sel_all, 'Select All')

        btn_sel_none = ttk.Button(top_ctrl, text='Deselect All', command=lambda: self._on_playlist_select_all('none'))
        btn_sel_none.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_sel_none, 'Deselect All')

        btn_sel_inv = ttk.Button(top_ctrl, text='Invert Select', command=lambda: self._on_playlist_select_all('invert'))
        btn_sel_inv.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_sel_inv, 'Invert Select')

        # Restore playlist option checkboxes (deduplicated) so they are visible once
        # again in the playlist tab. Keep behavior consistent with internal vars.
        self.playlist_reverse_var = tk.BooleanVar(value=False)
        cb_rev = ttk.Checkbutton(
            top_ctrl,
            text='Reverse order',
            variable=self.playlist_reverse_var,
            command=self._on_playlist_option_changed,
        )
        cb_rev.pack(side=tk.LEFT, padx=(20, 0))
        self.register_translatable_widget(cb_rev, 'Reverse order')

        self.playlist_exclude_private_var = tk.BooleanVar(value=True)
        cb_priv = ttk.Checkbutton(
            top_ctrl,
            text='Exclude private videos',
            variable=self.playlist_exclude_private_var,
            command=self._on_playlist_option_changed,
        )
        cb_priv.pack(side=tk.LEFT, padx=(20, 0))
        self.register_translatable_widget(cb_priv, 'Exclude private videos')

        # TREEVIEW for heavy listing
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('status', 'index', 'title')
        self.playlist_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='extended')

        # Define headings
        self.playlist_tree.heading('status', text=' ', anchor=tk.CENTER)
        self.playlist_tree.heading('index', text='#')
        self.playlist_tree.heading('title', text='Title')

        # Define columns
        self.playlist_tree.column('status', width=40, anchor=tk.CENTER, stretch=False)
        self.playlist_tree.column('index', width=60, anchor=tk.CENTER, stretch=False)
        self.playlist_tree.column('title', width=400, anchor=tk.W)

        # Scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.playlist_tree.yview)
        self.playlist_tree.configure(yscrollcommand=tree_scroll.set)

        self.playlist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events for interaction
        self.playlist_tree.bind('<ButtonRelease-1>', self._on_tree_click)
        self.playlist_tree.bind('<space>', self._on_tree_space)

        return frame

    def _on_tree_click(self, event):
        item = self.playlist_tree.identify_row(event.y)
        if item:
            self._toggle_tree_item(item)

    def _on_tree_space(self, event):
        items = self.playlist_tree.selection()
        if items:
            for item in items:
                self._toggle_tree_item(item)

    def _toggle_tree_item(self, item):
        values = list(self.playlist_tree.item(item, 'values'))
        if values:
            values[0] = '☐' if values[0] == '☑' else '☑'
            self.playlist_tree.item(item, values=values)

    def _on_playlist_select_all(self, mode='all'):
        for item in self.playlist_tree.get_children():
            values = list(self.playlist_tree.item(item, 'values'))
            if mode == 'all':
                values[0] = '☑'
            elif mode == 'none':
                values[0] = '☐'
            elif mode == 'invert':
                values[0] = '☐' if values[0] == '☑' else '☑'
            self.playlist_tree.item(item, values=values)

    def _on_playlist_mousewheel(self, event):
        # Only scroll if the playlist tab is active
        if self.notebook.select() == str(self.playlist_tab_frame):
            if event.num == 4:  # Linux scroll up
                self.playlist_tree.yview_scroll(-1, 'units')
            elif event.num == 5:  # Linux scroll down
                self.playlist_tree.yview_scroll(1, 'units')
            else:  # Windows/Mac
                self.playlist_tree.yview_scroll(int(-1 * (event.delta)), 'units')

    def _on_playlist_option_changed(self):
        if hasattr(self, 'playlist_entries_data') and self.playlist_entries_data:
            self.root.after(0, self._show_playlist_tab, 'Playlist')
