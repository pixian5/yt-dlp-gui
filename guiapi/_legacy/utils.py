"""Utility methods for file browsing and clipboard"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import filedialog

if TYPE_CHECKING:
    pass


class UtilsMixin:
    """Mixin for utility methods. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        tr: Any
        log_message: Any
        root: Any
        url_entry: Any
        batch_file_entry: Any
        batch_file_var: Any
        batch_file_input: Any
        batch_urls_text: Any
        config_location: Any
        download_archive: Any
        output_dir: Any
        load_info_json: Any
        cache_dir: Any
        client_certificate: Any
        client_certificate_key: Any
        ffmpeg_location: Any
        cookies: Any
        cookies_from_browser: Any
        current_language: Any
        metadata_lang: Any

    def browse_batch_file(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select Batch File'),
            filetypes=[(self.tr('Text Files'), '*.txt'), (self.tr('All Files'), '*.*')])
        if filename:
            self.batch_file_entry.delete(0, tk.END)
            self.batch_file_entry.insert(0, filename)
            if hasattr(self, 'batch_file_var'):
                self.batch_file_var.set(filename)

    def paste_url_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get().strip()
        except tk.TclError:
            clipboard_text = ''

        if not clipboard_text:
            self.log_message(self.tr('Clipboard is empty.'))
            return

        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, clipboard_text)
        self.url_entry.focus_set()
        self.log_message(self.tr('Pasted link from clipboard.'))

    def paste_playlist_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get().strip()
        except tk.TclError:
            clipboard_text = ''

        if not clipboard_text:
            self.log_message(self.tr('Clipboard is empty.'))
            return

        self.batch_file_entry.delete(0, tk.END)
        self.batch_file_entry.insert(0, clipboard_text)
        self.batch_file_entry.focus_set()

        # If it's a single URL and the main URL entry is empty, duplicate it there for convenience
        lines = [l.strip() for l in clipboard_text.splitlines() if l.strip()]
        if len(lines) == 1 and lines[0].startswith('http') and not self.url_entry.get().strip():
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, lines[0])

        self.log_message(self.tr('Pasted playlist from clipboard.'))

    def browse_config_file(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select Config File'),
            filetypes=[(self.tr('Config Files'), '*.conf'), (self.tr('All Files'), '*.*')])
        if filename:
            self.config_location.delete(0, tk.END)
            self.config_location.insert(0, filename)

    def browse_archive_file(self):
        filename = filedialog.asksaveasfilename(
            title=self.tr('Select Archive File'),
            defaultextension='.txt',
            filetypes=[(self.tr('Text Files'), '*.txt'), (self.tr('All Files'), '*.*')])
        if filename:
            self.download_archive.delete(0, tk.END)
            self.download_archive.insert(0, filename)

    def unify_languages(self):
        """Force metadata language choice to match current GUI language."""
        if not hasattr(self, 'current_language') or not hasattr(self, 'metadata_lang'):
            return

        lang_to_tag = {'zh': 'zh-CN', 'en': 'en', 'ja': 'ja', 'ko': 'ko', 'ru': 'ru', 'es': 'es', 'fr': 'fr', 'de': 'de'}
        target_code = lang_to_tag.get(self.current_language, 'zh-CN')
        self.refresh_metadata_lang_values(force_code=target_code)

    def refresh_metadata_lang_values(self, force_code=None):
        """Update metadata_lang combobox values based on current language translation."""
        if not hasattr(self, 'metadata_lang'):
            return

        current_val = self.metadata_lang.get()
        # Logic: If it's the first value (Default), we consider it "Auto"
        is_auto = False
        try:
            if current_val == self.metadata_lang['values'][0]:
                is_auto = True
        except Exception:
            is_auto = True

        # Keep track of which one was selected
        sel_code = force_code
        if not sel_code and not is_auto and '(' in current_val:
            sel_code = current_val.split('(')[-1].split(')')[0]

        new_values = [
            self.tr('Default (Auto)'),
            'Chinese (Simplified) (zh-CN)',
            'Chinese (Traditional) (zh-TW)',
            'English (en)',
            'Japanese (ja)',
            'Korean (ko)',
            'Russian (ru)',
            'Spanish (es)',
            'French (fr)',
            'German (de)',
            'Portuguese (pt)',
            'Turkish (tr)',
            'Italian (it)',
            'Arabic (ar)',
            'Hindi (hi)',
            'Vietnamese (vi)',
            'Thai (th)',
            'Indonesian (id)',
        ]
        self.metadata_lang['values'] = new_values

        if sel_code:
            for val in new_values:
                if f'({sel_code})' in val:
                    self.metadata_lang.set(val)
                    return

        # If auto or nothing matched
        self.metadata_lang.set(new_values[0])

    def browse_output_dir(self):
        dirname = filedialog.askdirectory(title=self.tr('Select Output Directory'))
        if dirname:
            self.output_dir.delete(0, tk.END)
            self.output_dir.insert(0, dirname)

    def browse_info_json(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select Info JSON'),
            filetypes=[(self.tr('JSON Files'), '*.json'), (self.tr('All Files'), '*.*')])
        if filename:
            self.load_info_json.delete(0, tk.END)
            self.load_info_json.insert(0, filename)

    def browse_cache_dir(self):
        dirname = filedialog.askdirectory(title=self.tr('Select Cache Directory'))
        if dirname:
            self.cache_dir.delete(0, tk.END)
            self.cache_dir.insert(0, dirname)

    def browse_client_cert(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select Client Certificate'),
            filetypes=[(self.tr('PEM Files'), '*.pem'), (self.tr('All Files'), '*.*')])
        if filename:
            self.client_certificate.delete(0, tk.END)
            self.client_certificate.insert(0, filename)

    def browse_client_key(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select Client Certificate Key'),
            filetypes=[
                (self.tr('PEM Files'), '*.pem'),
                (self.tr('Key Files'), '*.key'),
                (self.tr('All Files'), '*.*')])
        if filename:
            self.client_certificate_key.delete(0, tk.END)
            self.client_certificate_key.insert(0, filename)

    def browse_ffmpeg(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select FFmpeg Binary'),
            filetypes=[(self.tr('Executable Files'), '*.exe'), (self.tr('All Files'), '*.*')])
        if filename:
            self.ffmpeg_location.delete(0, tk.END)
            self.ffmpeg_location.insert(0, filename)

    def browse_cookies(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select Cookies File'),
            filetypes=[(self.tr('Text Files'), '*.txt'), (self.tr('All Files'), '*.*')])
        if filename:
            self.cookies.delete(0, tk.END)
            self.cookies.insert(0, filename)
