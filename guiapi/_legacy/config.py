"""Configuration management"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import json
import os
from tkinter import filedialog, messagebox

if TYPE_CHECKING:
    pass


class ConfigMixin:
    """Mixin for configuration management. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        tr: Any
        translate_concat: Any
        config: Any
        config_file: Any
        write_config_to_disk: Any
        current_language: Any
        _stateful_controls: Any
        language_var: Any
        get_language_display: Any
        apply_localization: Any
        apply_pending_gui_state: Any
        status_var: Any
        ensure_all_tabs_built: Any

    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f'Error loading config: {e}')

    def save_config(self, silent=False):
        """Save current configuration to file"""
        try:
            self.config = self.get_current_config()
            self.write_config_to_disk(self.config)
        except Exception as e:
            if not silent:
                messagebox.showerror(self.tr('Error'), self.translate_concat('Failed to save configuration: ', e))

    def load_config_dialog(self):
        """Load configuration from a file dialog"""
        filename = filedialog.askopenfilename(
            title=self.tr('Load Configuration'),
            filetypes=[(self.tr('JSON Files'), '*.json'), (self.tr('All Files'), '*.*')])
        if filename:
            try:
                with open(filename, encoding='utf-8') as f:
                    self.config = json.load(f)
                self.apply_config()
                messagebox.showinfo(self.tr('Success'), self.tr('Configuration loaded successfully!'))
            except Exception as e:
                messagebox.showerror(self.tr('Error'), self.translate_concat('Failed to load configuration: ', e))

    def save_config_dialog(self):
        """Save configuration to a file dialog"""
        filename = filedialog.asksaveasfilename(
            title=self.tr('Save Configuration'),
            defaultextension='.json',
            filetypes=[(self.tr('JSON Files'), '*.json'), (self.tr('All Files'), '*.*')])
        if filename:
            try:
                self.config = self.get_current_config()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2)
                messagebox.showinfo(self.tr('Success'), self.tr('Configuration saved successfully!'))
            except Exception as e:
                messagebox.showerror(self.tr('Error'), self.translate_concat('Failed to save configuration: ', e))

    def get_current_config(self):
        """Get current configuration from GUI"""
        import tkinter as tk
        from tkinter import ttk, scrolledtext

        self.ensure_all_tabs_built()

        gui_state = {}
        for name, widget in self._stateful_controls.items():
            if name in {'language_selector', 'console', 'generated_cmd'}:
                continue
            if isinstance(widget, tk.BooleanVar):
                gui_state[name] = bool(widget.get())
            elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                gui_state[name] = widget.get()
            elif isinstance(widget, scrolledtext.ScrolledText):
                gui_state[name] = widget.get('1.0', tk.END).rstrip('\n')

        return {
            'config_version': 1,
            'language': self.current_language,
            'language_initialized': True,
            'gui_state': gui_state,
        }

    def apply_config(self):
        """Apply loaded configuration to GUI"""
        from .constants import LANGUAGE_OPTIONS, GUI_DEFAULT_STATE

        language = self.config.get('language', self.current_language)
        if language not in LANGUAGE_OPTIONS:
            language = 'en'
        self.current_language = language
        gui_state = dict(self.config.get('gui_state', {}))
        for key, value in GUI_DEFAULT_STATE.items():
            if key not in gui_state:
                gui_state[key] = value
        self._pending_gui_state = gui_state
        if hasattr(self, 'language_var'):
            self.language_var.set(self.get_language_display(language))
        self.apply_localization()
        self.apply_pending_gui_state()
        self.status_var.set(self.tr('Ready'))
