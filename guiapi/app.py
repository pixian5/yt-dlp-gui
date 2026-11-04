#!/usr/bin/env python3
"""
Main GUI application for yt-dlp.

Tk widgets are owned by the main thread. Download, inspect, and playlist
preflight work runs in daemon threads and communicates back through
``root.after`` and ``log_queue``. Keep that boundary intact when adding a
new asynchronous action.
"""

import atexit
import contextlib
import json
import locale
import os
import shlex
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from guiapi import tab_builders
from guiapi.command_builder import build_command_args_from_app
from guiapi.config_store import (
    SECRET_CONFIG_KEYS,
    load_config_file,
    save_config_file,
)
from guiapi.constants import GUI_DEFAULT_STATE, LANGUAGE_OPTIONS
from guiapi.core import core_launcher, sanitize_command
from guiapi.runner import (
    augmented_path,
    extra_bin_dirs,
    subprocess_env,
    subprocess_text_kwargs,
    terminate_process,
)
from guiapi.translations import TRANSLATIONS

# Never persist these auth fields to ~/.yt-dlp-gui-config.json
_SECRET_CONFIG_KEYS = SECRET_CONFIG_KEYS

# Windows reserved device names (case-insensitive)
_WINDOWS_RESERVED_NAMES = frozenset({
    'CON', 'PRN', 'AUX', 'NUL',
    *(f'COM{i}' for i in range(1, 10)),
    *(f'LPT{i}' for i in range(1, 10)),
})

# The quick selector is a one-way preset writer: selecting an item replaces
# the free-form ``Format selection`` expression with the value below.
_QUICK_RESOLUTION_FORMATS = {
    'Best (Auto)': 'bestvideo+bestaudio/best',
    '4K (2160p)': 'bv*[height<=2160]+ba',
    '2K (1440p)': 'bv*[height<=1440]+ba',
    '1080p 60fps': 'bv*[height<=1080][fps>=60]+ba',
    '1080p': 'bv*[height<=1080]+ba',
    '720p 60fps': 'bv*[height<=720][fps>=60]+ba',
    '720p': 'bv*[height<=720]+ba',
    '480p': 'bv*[height<=480]+ba',
    '360p': 'bv*[height<=360]+ba',
}


class YtDlpGUI:
    """Main GUI application for yt-dlp configuration and downloading.

    Coordinates modular option building (command_builder), process execution (runner),
    and settings persistence (config_store).
    """

    @staticmethod
    def _subprocess_text_kwargs():
        return subprocess_text_kwargs()

    @staticmethod
    def _extra_bin_dirs():
        return extra_bin_dirs()

    @classmethod
    def _augmented_path(cls, base_path=None):
        return augmented_path(base_path)

    @classmethod
    def _subprocess_env(cls):
        return subprocess_env()

    @staticmethod
    def sanitize_path_component(name, fallback='item'):
        """Sanitize a single path component for cross-platform filenames/folders."""
        if name is None:
            name = ''
        text = str(name)
        # Drop path separators and Windows-forbidden characters
        cleaned = []
        for ch in text:
            if ch in '<>:"/\\|?*' or ord(ch) < 32:
                cleaned.append('_')
            else:
                cleaned.append(ch)
        text = ''.join(cleaned).strip(' .')
        if not text:
            text = fallback
        # Windows reserved basenames (ignore extension for the check)
        stem = text.split('.', 1)[0].upper()
        if stem in _WINDOWS_RESERVED_NAMES:
            text = f'_{text}'
        # Keep names reasonably short for filesystem limits
        if len(text) > 180:
            text = text[:180].rstrip(' .')
        return text or fallback

    def __init__(self, root):
        # Prefer existing tool bins (Homebrew/local) for node/ffmpeg/deno child processes
        os.environ['PATH'] = self._augmented_path()

        self.root = root
        self.base_title = 'yt-dlp GUI - Video Downloader Configuration'
        self._translatable_widgets = {}
        self._notebook_tab_texts = {}
        self._tab_builders = {}
        self._built_tabs = set()
        self._tab_controls = {}
        self._stateful_controls = {}
        self._pending_gui_state = {}
        self._active_tab_frame = None

        self.current_language = 'en'  # Default for very early calls

        # Configuration storage
        self.config = {}
        self.config_file = os.path.expanduser('~/.yt-dlp-gui-config.json')
        self.load_config()
        # Thread-safe logging initialization
        import queue
        self.log_queue = queue.Queue()
        self._last_progress_enqueue = 0.0
        self._last_progress_update = 0.0
        self._start_log_watcher()

        # Runtime state is split by owner: Tk state lives on the main thread;
        # process pointers/cancel flags are shared with worker threads.
        self.batch_file_var = tk.StringVar()
        self.batch_urls_text = None
        self.bulk_rows = []
        self.playlist_parse_is_real_playlist = False
        self.download_after_playlist_parse = False
        self._download_running = False
        self._download_cancel = False
        self._parse_all_running = False
        self._parse_all_process = None
        self.current_process = None
        self._parse_process = None
        self._parse_running = False
        self._parse_cancel = False
        self._parse_generation = 0
        self._closing = False
        # 'download' offers partial-file cleanup on Stop; 'inspect' (formats/info) does not.
        self._runner_kind = None

        # Language selection variable with trace
        self.language_var = tk.StringVar()
        self.language_var.trace_add('write', self.on_language_changed_trace)

        # Create main container
        self.create_widgets()

        # Initialize language values AFTER widgets are created
        self.initialize_language()

        # Ensure the selector matches initial state without triggering trace loop
        pref = self.config.get('language', 'auto')
        self.language_var.set(self.get_language_display(pref))

        self.apply_localization()
        self.apply_config()
        self.unify_languages()

        self.root.after(50, self.present_window)
        self.root.protocol('WM_DELETE_WINDOW', self.on_window_close)
        # Esc = same as pressing the Stop/Download control (cancels a running job)
        self.root.bind_all('<Escape>', self._on_escape_key)

        # Set window icon (if available)
        with contextlib.suppress(Exception):
            self.root.iconname('yt-dlp')

    def tr(self, text):
        """Translate UI text with English fallback."""
        if not text:
            return text
        lang = getattr(self, 'current_language', 'en')
        translations = TRANSLATIONS.get(lang, {})
        result = translations.get(text)
        if result is None:
            # If not found in current language, it returns the key itself
            return text
        return result

    def translate_concat(self, prefix, value):
        """Translate a message prefix while preserving dynamic data."""
        return f'{self.tr(prefix)}{value}'

    def detect_system_language(self):
        """Detect the preferred system language and map it to a supported locale."""
        candidates = []

        # 1. First priority: macOS system defaults (Most reliable for user)
        if sys.platform == 'darwin':
            try:
                # Get the AppleLanguages array (e.g. ("zh-Hans-US", "en-US"))
                output = subprocess.check_output(['defaults', 'read', '-g', 'AppleLanguages'],
                                                 stderr=subprocess.DEVNULL, text=True)
                import re
                matches = re.findall(r'"([^"]+)"', output)
                candidates.extend(matches)
            except Exception:
                pass

        # 2. Local environment variables
        for env_name in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
            value = os.environ.get(env_name)
            if value:
                candidates.append(value)

        # 3. Python standard locale
        try:
            lang, _ = locale.getlocale()
            if lang:
                candidates.append(lang)
        except Exception:
            pass

        for candidate in candidates:
            normalized = candidate.replace('-', '_').lower()
            prefix = normalized.split('_', 1)[0]
            self.log_message(f'[DETECTION] Trying candidate: {candidate} -> prefix: {prefix}')
            if prefix in LANGUAGE_OPTIONS:
                self.log_message(f'[DETECTION] SUCCESS! Matched system language: {prefix}')
                return prefix
        self.log_message('[DETECTION] FAILED. Defaulting to: en')
        return 'en'

    def initialize_language(self):
        """Initialize UI language from config; handle 'auto' by resolving to system language."""
        configured_language = self.config.get('language')

        # If it's auto or not set, always perform fresh detection for the session
        if not configured_language or configured_language == 'auto':
            detected = self.detect_system_language()
            self.current_language = detected
            # Return 'auto' if that was the preference, so the caller knows the mode
            return configured_language if configured_language == 'auto' else detected

        if configured_language in LANGUAGE_OPTIONS:
            self.current_language = configured_language
            return configured_language

        detected = self.detect_system_language()
        self.current_language = detected
        return detected

    def write_config_to_disk(self, config):
        save_config_file(config, self.config_file)

    def persist_language_preference(self):
        """Persist only language-related fields for instant switch without heavy full-state save.

        Keeps the raw preference (including 'auto') already stored in self.config['language'];
        does not overwrite it with the resolved session language.
        """
        try:
            self.config['language_initialized'] = True
            # Preserve explicit preference (e.g. 'auto'); only fill if missing.
            if 'language' not in self.config or self.config['language'] not in LANGUAGE_OPTIONS:
                self.config['language'] = self.current_language
            self.write_config_to_disk(self.config)
        except Exception as e:
            self.log_message(self.translate_concat('Failed to save configuration: ', str(e)))

    def get_language_display(self, code):
        return LANGUAGE_OPTIONS.get(code, LANGUAGE_OPTIONS['en'])

    def get_language_code_from_display(self, display_name):
        for code, name in LANGUAGE_OPTIONS.items():
            if name == display_name:
                return code
        return 'en'

    def register_translatable_widget(self, widget, text):
        self._translatable_widgets[widget] = text
        return widget

    def apply_localization(self):
        """Refresh translated text on widgets that expose a text property."""
        # self.log_message(f"[LOCALIZE] Starting UI localization to: {self.current_language}")
        self.root.title(self.tr(self.base_title))

        if hasattr(self, 'language_label'):
            self.language_label.config(text=self.tr('Language:'))
        if hasattr(self, 'language_selector'):
            # Use the raw config preference (e.g. 'auto') for the selector display
            pref = self.config.get('language', 'auto')
            self.language_selector.set(self.get_language_display(pref))

        # Force refresh status if it's a known state
        if hasattr(self, 'status_var'):
            self.status_var.set(self.tr('Ready'))

        self.localize_widget_tree(self.root)
        self.localize_notebook_tabs()

        # Explicit treeview heading localization
        if hasattr(self, 'playlist_tree'):
            self.playlist_tree.heading('status', text=' ')
            self.playlist_tree.heading('index', text=self.tr('#'))
            self.playlist_tree.heading('title', text=self.tr('Title'))

        # Refresh resolution selector values if it exists
        if hasattr(self, 'res_selector'):
            self.res_selector.config(values=[self.tr(opt) for opt in _QUICK_RESOLUTION_FORMATS])

        # self.log_message("[LOCALIZE] UI localization complete.")
        self.drain_log_queue()

    def drain_log_queue(self):
        """Force process all pending log messages immediately."""
        if not hasattr(self, 'log_queue'):
            return
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self._log_message_internal(msg)
            except Exception:
                break

    def localize_widget_tree(self, widget):
        try:
            text = widget.cget('text')
        except tk.TclError:
            text = None

        if text is not None and text.strip():
            # IMPORTANT: We MUST use the original key.
            # If not in registry, WE DO NOT AUTO-REGISTER if it's not likely English.
            # This prevents capturing already-translated text as a new key.
            if widget not in self._translatable_widgets:
                # Only auto-register if the text looks like an English key (contains ASCII/standard symbols)
                try:
                    text.encode('ascii')
                    self._translatable_widgets[widget] = text
                except UnicodeEncodeError:
                    # If it's already non-ASCII, it's likely already translated.
                    # We can't safely use it as a key unless we find it in TRANSLATIONS backwards.
                    pass

            if widget in self._translatable_widgets:
                key = self._translatable_widgets[widget]
                translated = self.tr(key)
                if translated != text:
                    # self.log_message(f"[LOCALIZE] Widget {widget}: Key='{key}' -> Translated='{translated}'")
                    widget.config(text=translated)

        if isinstance(widget, tk.Canvas):
            for item in widget.find_all():
                if widget.type(item) == 'window':
                    sub_widget = widget.nametowidget(widget.itemcget(item, 'window'))
                    self.localize_widget_tree(sub_widget)
        for child in widget.winfo_children():
            self.localize_widget_tree(child)

    def translate_yt_dlp_line(self, line):
        """Translate common yt-dlp output lines."""
        if 'Extracting cookies from ' in line:
            return line.replace('Extracting cookies from ', self.tr('Extracting cookies from '))
        if 'Extracted ' in line and ' cookies from ' in line:
            return line.replace('Extracted ', self.tr('Extracted ')).replace(' cookies from ', self.tr(' cookies from '))
        if '[download] Downloading playlist: ' in line:
            return line.replace('[download] Downloading playlist: ', self.tr('[download] Downloading playlist: '))
        if '[download] Finished downloading playlist: ' in line:
            return line.replace('[download] Finished downloading playlist: ', self.tr('[download] Finished downloading playlist: '))
        if '[download] Downloading item ' in line and ' of ' in line:
            return line.replace('[download] Downloading item ', self.tr('[download] Downloading item ')).replace(' of ', self.tr(' of '))
        if '[download] Destination: ' in line:
            return line.replace('[download] Destination: ', self.tr('[download] Destination: '))
        if '[Merger] Merging formats into ' in line:
            return line.replace('[Merger] Merging formats into ', self.tr('[Merger] Merging formats into '))
        if 'Deleting original file ' in line:
            return line.replace('Deleting original file ', self.tr('Deleting original file '))
        if ': Downloading webpage' in line:
            return line.replace(': Downloading webpage', self.tr(': Downloading webpage'))
        if '[info] Writing video subtitles to: ' in line:
            return line.replace('[info] Writing video subtitles to: ', self.tr('[info] Writing video subtitles to: '))
        return line

    def localize_notebook_tabs(self):
        if not hasattr(self, 'notebook'):
            return
        for tab_id in self.notebook.tabs():
            child = self.root.nametowidget(tab_id)
            if child not in self._notebook_tab_texts:
                self._notebook_tab_texts[child] = self.notebook.tab(tab_id, 'text')

            key = self._notebook_tab_texts[child]
            translated = self.tr(key)
            # self.log_message(f"[LOCALIZE] Tab {child}: Key='{key}' -> Translated='{translated}'")
            self.notebook.tab(tab_id, text=translated)

    def on_language_changed_trace(self, *args):
        """Wrapper to handle language change from variable trace."""
        # Use root.after to ensure we are outside the trace update cycle if needed
        self.root.after(1, self.on_language_changed)

    def on_language_changed(self, _event=None):
        display_val = self.language_var.get()
        if not display_val:
            return

        print(f'[LANG] on_language_changed triggered. Value: {display_val}')

        raw_code = self.get_language_code_from_display(display_val)
        new_language = raw_code

        if raw_code == 'auto':
            new_language = self.detect_system_language()
            print(f'[LANG] Auto-detected: {new_language}')

        # Check if actually changed to avoid redundant refreshes
        if getattr(self, 'current_language', None) == new_language:
            # Still update config in case raw_code changed (e.g. from specific to 'auto')
            self.config['language'] = raw_code
            self.persist_language_preference()
            return

        self.log_message(f'[EVENT] Switching language to: {new_language} (Choice: {display_val})')
        print(f'[LANG] Setting current_language to {new_language}')

        # 1. Update state
        self.config['language'] = raw_code
        self.current_language = new_language
        self.persist_language_preference()

        # 2. Apply translations
        self.apply_localization()

        # 3. Explicitly re-localize everything again with a fresh tree traversal
        self.localize_widget_tree(self.root)

        # 4. Sync other components
        self.unify_languages()

        # 5. Force update
        self.root.update_idletasks()
        self.drain_log_queue()
        print('[LANG] Language change completed.')

    def maximize_window(self):
        """Open the window in a maximized state with a geometry fallback."""
        self.root.update_idletasks()
        screen_width, screen_height = self.get_effective_screen_size()

        try:
            self.root.state('zoomed')
            self.root.update_idletasks()
            if (self.root.winfo_width() >= int(screen_width * 0.6)
                    and self.root.winfo_height() >= int(screen_height * 0.6)):
                return
        except tk.TclError:
            pass

        try:
            self.root.attributes('-zoomed', True)
            self.root.update_idletasks()
            if (self.root.winfo_width() >= int(screen_width * 0.6)
                    and self.root.winfo_height() >= int(screen_height * 0.6)):
                return
        except tk.TclError:
            pass

        self.root.geometry(f'{screen_width}x{screen_height}+0+0')

    def get_effective_screen_size(self):
        """Return a usable screen size, with a sensible fallback when Tk reports 0x0."""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        if screen_width <= 1 or screen_height <= 1:
            return 1440, 900
        return screen_width, screen_height

    def ensure_window_visible(self):
        """Ensure the window is visible on-screen and has a sane minimum size."""
        self.root.update_idletasks()

        screen_width, screen_height = self.get_effective_screen_size()
        width = max(1, self.root.winfo_width())
        height = max(1, self.root.winfo_height())
        x = self.root.winfo_x()
        y = self.root.winfo_y()

        too_small = width < 900 or height < 600
        offscreen = (
            x <= -(width // 2)
            or y <= -(height // 2)
            or x >= screen_width - 80
            or y >= screen_height - 80
        )

        if not too_small and not offscreen:
            return

        target_width = min(screen_width, max(1100, int(screen_width * 0.9)))
        target_height = min(screen_height, max(720, int(screen_height * 0.85)))
        target_x = max(0, (screen_width - target_width) // 2)
        target_y = max(0, (screen_height - target_height) // 3)

        with contextlib.suppress(tk.TclError):
            self.root.state('normal')

        self.root.geometry(f'{target_width}x{target_height}+{target_x}+{target_y}')
        self.root.deiconify()
        self.root.lift()

    def bring_to_front(self):
        """Request focus and foreground status, especially on macOS."""
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()

        with contextlib.suppress(tk.TclError):
            self.root.focus_force()

        try:
            self.root.attributes('-topmost', True)
            self.root.after(300, lambda: self.root.attributes('-topmost', False))
        except tk.TclError:
            pass

        if sys.platform == 'darwin':
            try:
                script = (
                    'tell application "System Events"\n'
                    f'    set frontmost of the first process whose unix id is {os.getpid()} to true\n'
                    'end tell'
                )
                subprocess.run(
                    ['osascript', '-e', script],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def present_window(self):
        """Maximize and foreground the window on launch."""
        self.maximize_window()
        self.bring_to_front()
        self.root.after(200, self.ensure_window_visible)
        self.root.after(800, self.ensure_window_visible)

    def add_lazy_tab(self, key, title, builder):
        """Register a notebook tab whose contents are built on first access."""
        frame = ttk.Frame(self.notebook, padding='10')
        self.notebook.add(frame, text=title)
        self._tab_builders[key] = (frame, builder, title)
        self._notebook_tab_texts[frame] = title
        return frame

    def ensure_tab_built(self, frame):
        """Build a tab's contents only once."""
        if frame in self._built_tabs:
            return
        for _key, (tab_frame, builder, _title) in self._tab_builders.items():
            if tab_frame == frame:
                before_names = set(self.__dict__)
                builder(frame)
                new_names = self._tab_controls.get(frame) or (set(self.__dict__) - before_names)
                self.register_stateful_controls(new_names)
                self._tab_controls[frame] = new_names
                self._built_tabs.add(frame)
                self.localize_widget_tree(frame)
                self.apply_pending_gui_state()
                return

    def snapshot_control_value(self, widget):
        if isinstance(widget, tk.BooleanVar):
            return bool(widget.get())
        if isinstance(widget, (ttk.Entry, ttk.Combobox)):
            return widget.get()
        if isinstance(widget, scrolledtext.ScrolledText):
            return widget.get('1.0', tk.END).rstrip('\n')
        return None

    def get_or_create_boolvar(self, name, default=False):
        value = getattr(self, name, None)
        if isinstance(value, tk.BooleanVar):
            return value
        value = tk.BooleanVar(value=default)
        setattr(self, name, value)
        self.register_stateful_controls({name})
        return value

    def ensure_named_tab_built(self, key):
        tab_info = self._tab_builders.get(key)
        if tab_info:
            self.ensure_tab_built(tab_info[0])

    def get_control_text(self, name, default=''):
        widget = getattr(self, name, None)
        if widget is not None and hasattr(widget, 'get'):
            try:
                value = widget.get()
                return str(value).strip() if value is not None else default
            except Exception:
                pass
        value = self._pending_gui_state.get(name, default)
        return str(value).strip() if value is not None else default

    def get_control_bool(self, name, default=False):
        """Read a BooleanVar or pending bool state without requiring the tab to be open."""
        widget = getattr(self, name, None)
        if isinstance(widget, tk.BooleanVar):
            try:
                return bool(widget.get())
            except Exception:
                return default
        if name in self._pending_gui_state:
            return bool(self._pending_gui_state.get(name))
        return default

    def get_metadata_language(self):
        """Return the YouTube metadata locale and whether the user selected one.

        Playlist titles become output filenames, so preflight and download must
        resolve this value identically. ``Accept-Language`` alone is not enough
        for YouTube's Innertube API; callers must also pass ``youtube:lang``.
        """
        language_defaults = {
            'zh': 'zh-CN', 'en': 'en', 'ru': 'ru', 'ja': 'ja', 'ko': 'ko',
            'es': 'es', 'fr': 'fr', 'de': 'de',
        }
        default_code = language_defaults.get(getattr(self, 'current_language', 'zh'), 'zh-CN')
        choice = self.get_control_text('metadata_lang')
        auto_label = self.tr('Default (Auto)')
        if not choice or choice == auto_label:
            return default_code, False

        # Combobox entries are either raw tags (``zh-CN``) or labels such as
        # ``Chinese (Simplified) (zh-CN)`` after localization.
        if '(' in choice and choice.endswith(')'):
            choice = choice.rsplit('(', 1)[1][:-1].strip()
        return choice or default_code, True

    def collect_parse_options(self):
        """Snapshot download-aligned options for playlist/info preflight parses.

        Uses live widgets when built, otherwise pending config values — does not
        force-build every lazy tab.
        """
        # Build only the tabs that commonly hold parse/auth options
        for key in ('authentication', 'network', 'geo', 'extractor', 'workarounds', 'general'):
            self.ensure_named_tab_built(key)

        text_keys = (
            'cookies_from_browser', 'cookies', 'user_agent', 'referer', 'add_header',
            'extractor_args', 'proxy', 'socket_timeout', 'source_address',
            'username', 'password', 'twofactor', 'video_password',
            'ap_mso', 'ap_username', 'ap_password',
            'client_certificate', 'client_certificate_key', 'client_certificate_password',
            'geo_verification_proxy', 'geo_bypass_country', 'geo_bypass_ip_block',
        )
        options = {}
        for key in text_keys:
            options[key] = self.get_control_text(key)
        bool_defaults = {
            'netrc': False,
            'force_ipv4': False,
            'force_ipv6': False,
            'geo_bypass': False,
            'no_geo_bypass': False,
            'include_private_videos': True,
        }
        for key, default in bool_defaults.items():
            options[key] = self.get_control_bool(key, default=default)
        return options

    def apply_parse_options_to_cmd(self, cmd, parse_options=None):
        """Append auth/network options used by both download and parse paths."""
        parse_options = parse_options or {}

        if parse_options.get('proxy'):
            cmd.extend(['--proxy', parse_options['proxy']])
        if parse_options.get('socket_timeout'):
            cmd.extend(['--socket-timeout', parse_options['socket_timeout']])
        if parse_options.get('source_address'):
            cmd.extend(['--source-address', parse_options['source_address']])
        if parse_options.get('force_ipv4'):
            cmd.append('--force-ipv4')
        if parse_options.get('force_ipv6'):
            cmd.append('--force-ipv6')

        if parse_options.get('geo_verification_proxy'):
            cmd.extend(['--geo-verification-proxy', parse_options['geo_verification_proxy']])
        if parse_options.get('geo_bypass'):
            cmd.append('--geo-bypass')
        if parse_options.get('no_geo_bypass'):
            cmd.append('--no-geo-bypass')
        if parse_options.get('geo_bypass_country'):
            cmd.extend(['--geo-bypass-country', parse_options['geo_bypass_country']])
        if parse_options.get('geo_bypass_ip_block'):
            cmd.extend(['--geo-bypass-ip-block', parse_options['geo_bypass_ip_block']])

        if parse_options.get('cookies_from_browser'):
            cmd.extend(['--cookies-from-browser', parse_options['cookies_from_browser']])
        if parse_options.get('cookies'):
            cmd.extend(['--cookies', parse_options['cookies']])
        if parse_options.get('user_agent'):
            cmd.extend(['--user-agent', parse_options['user_agent']])
        if parse_options.get('referer'):
            cmd.extend(['--referer', parse_options['referer']])
        if parse_options.get('add_header'):
            cmd.extend(['--add-header', parse_options['add_header']])

        if parse_options.get('username'):
            cmd.extend(['--username', parse_options['username']])
        if parse_options.get('password'):
            cmd.extend(['--password', parse_options['password']])
        if parse_options.get('twofactor'):
            cmd.extend(['--twofactor', parse_options['twofactor']])
        if parse_options.get('netrc'):
            cmd.append('--netrc')
        if parse_options.get('video_password'):
            cmd.extend(['--video-password', parse_options['video_password']])
        if parse_options.get('ap_mso'):
            cmd.extend(['--ap-mso', parse_options['ap_mso']])
        if parse_options.get('ap_username'):
            cmd.extend(['--ap-username', parse_options['ap_username']])
        if parse_options.get('ap_password'):
            cmd.extend(['--ap-password', parse_options['ap_password']])
        if parse_options.get('client_certificate'):
            cmd.extend(['--client-certificate', parse_options['client_certificate']])
        if parse_options.get('client_certificate_key'):
            cmd.extend(['--client-certificate-key', parse_options['client_certificate_key']])
        if parse_options.get('client_certificate_password'):
            cmd.extend(['--client-certificate-password', parse_options['client_certificate_password']])

        if parse_options.get('include_private_videos') is False:
            cmd.extend(['--compat-options', 'no-youtube-unavailable-videos'])

        user_extractor_args = parse_options.get('extractor_args', '') or ''
        if user_extractor_args:
            cmd.extend(['--extractor-args', user_extractor_args])
        normalized = user_extractor_args.lower().replace(' ', '')
        if 'youtubetab:' not in normalized:
            cmd.extend(['--extractor-args', 'youtubetab:skip=authcheck'])
        return cmd

    def get_batch_file_value(self):
        value = self.get_control_text('batch_file_var')
        if value:
            return value
        if hasattr(self, 'batch_file_entry'):
            try:
                return self.batch_file_entry.get().strip()
            except Exception:
                return ''
        return ''

    def get_bulk_urls(self):
        urls = []
        for row in getattr(self, 'bulk_rows', []):
            var = row.get('var') if isinstance(row, dict) else None
            if var is None:
                continue
            try:
                value = var.get().strip()
            except Exception:
                value = ''
            if value:
                urls.append(value)
        return urls

    def dedupe_preserve_order(self, values):
        seen = set()
        result = []
        for value in values:
            value = (value or '').strip()
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def normalize_media_url(self, value):
        """Normalize URL for equality checks (strip, drop trailing slash / common noise)."""
        text = (value or '').strip()
        if not text:
            return ''
        # Drop trailing slash except for scheme-only forms
        while text.endswith('/') and text.count('/') > 2:
            text = text[:-1]
        return text

    def media_urls_equal(self, a, b):
        return self.normalize_media_url(a) == self.normalize_media_url(b)

    def read_batch_file_urls(self, file_path):
        with open(file_path, encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    def create_temp_batch_file(self, urls):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tf:
            tf.write('\n'.join(urls))
            tf.write('\n')
            temp_path = tf.name
        if not hasattr(self, '_temp_batch_files'):
            self._temp_batch_files = []
            atexit.register(self._cleanup_temp_files)
        self._temp_batch_files.append(temp_path)
        return temp_path

    def collect_batch_targets(self, batch_file=None, bulk_urls=None):
        batch_file = self.get_batch_file_value() if batch_file is None else (batch_file or '').strip()
        bulk_urls = self.get_bulk_urls() if bulk_urls is None else list(bulk_urls)
        direct_urls = []
        batch_file_path = ''

        if batch_file:
            if '\n' in batch_file:
                direct_urls.extend(line.strip() for line in batch_file.splitlines() if line.strip())
            elif batch_file.startswith(('http://', 'https://')):
                direct_urls.append(batch_file)
            else:
                batch_file_path = batch_file

        direct_urls.extend(bulk_urls)
        return batch_file_path, self.dedupe_preserve_order(direct_urls)

    def has_download_target(self):
        return bool(self.url_entry.get().strip() or self.get_batch_file_value() or self.get_bulk_urls())

    def unload_tab(self, frame):
        """Destroy inactive tab contents while preserving their GUI state."""
        # EXEMPTION: Never unload the Playlist or Batch tab because they contain dynamic list data
        is_playlist = hasattr(self, 'playlist_tab_frame') and frame == self.playlist_tab_frame
        is_batch = hasattr(self, 'batch_tab_frame') and frame == self.batch_tab_frame
        if frame not in self._built_tabs or is_playlist or is_batch:
            return

        for name in self._tab_controls.get(frame, set()):
            widget = self._stateful_controls.pop(name, None)
            if widget is None:
                continue
            value = self.snapshot_control_value(widget)
            if value is not None:
                self._pending_gui_state[name] = value

        # Batch tab is exempt from unload above; do not snapshot bulk_rows here
        # (would race with empty bulk clears and resurrect stale pending URLs).

        for child in frame.winfo_children():
            child.destroy()

        self._built_tabs.discard(frame)

    def on_tab_changed(self, _event=None):
        if not hasattr(self, 'notebook'):
            return
        selected = self.notebook.select()
        if not selected:
            return
        frame = self.root.nametowidget(selected)
        previous_frame = self._active_tab_frame

        if previous_frame is not None and previous_frame != frame:
            # EXEMPTION: Never unload the Playlist or Batch tab
            is_playlist = (hasattr(self, 'playlist_tab_frame') and previous_frame == self.playlist_tab_frame)
            is_batch = (hasattr(self, 'batch_tab_frame') and previous_frame == self.batch_tab_frame)
            if not is_playlist and not is_batch:
                self.unload_tab(previous_frame)

        self.ensure_tab_built(frame)
        self._active_tab_frame = frame

        # Update scrollregion once after a slight delay if switching into it,
        # but avoid heavy update_idletasks on every switch.
        if hasattr(self, 'playlist_tab_frame') and frame == self.playlist_tab_frame:
            pass  # Treeview handles sizing automatically

    def trigger_autosave(self, *args):
        """Request an autosave with a short debouncing delay."""
        if hasattr(self, '_autosave_timer') and self._autosave_timer:
            self.root.after_cancel(self._autosave_timer)
        self._autosave_timer = self.root.after(500, lambda: self.save_config(silent=True))

    def ensure_all_tabs_built(self):
        """Build all tabs before full-state serialization."""
        if not hasattr(self, 'notebook'):
            return
        for tab_id in self.notebook.tabs():
            frame = self.root.nametowidget(tab_id)
            self.ensure_tab_built(frame)

    def register_stateful_controls(self, attribute_names):
        """Track GUI-only controls so they can be serialized independently and trigger autosave."""
        for name in attribute_names:
            value = getattr(self, name, None)
            if isinstance(value, (tk.BooleanVar, ttk.Entry, ttk.Combobox, scrolledtext.ScrolledText)):
                if self._stateful_controls.get(name) is value:
                    continue
                self._stateful_controls[name] = value

                # Setup autosave triggers
                if isinstance(value, tk.Variable):
                    value.trace_add('write', self.trigger_autosave)
                elif isinstance(value, (ttk.Entry, ttk.Combobox)):
                    value.bind('<KeyRelease>', self.trigger_autosave)
                    if isinstance(value, ttk.Combobox):
                        value.bind('<<ComboboxSelected>>', self.trigger_autosave)
                elif isinstance(value, scrolledtext.ScrolledText):
                    value.bind('<KeyRelease>', self.trigger_autosave)

    def _set_entry_value(self, widget, value):
        if isinstance(widget, ttk.Combobox):
            widget.set(value)
            return
        widget.delete(0, tk.END)
        if value:
            widget.insert(0, value)

    def _set_text_value(self, widget, value):
        prior_state = str(widget.cget('state'))
        if prior_state == tk.DISABLED:
            widget.config(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        if value:
            widget.insert('1.0', value)
        if prior_state == tk.DISABLED:
            widget.config(state=tk.DISABLED)

    def apply_pending_gui_state(self):
        """Apply saved GUI-only state to controls that already exist."""
        if not self._pending_gui_state:
            return

        # Restore bulk_urls when Batch tab is built. Empty list means "clear rows".
        if hasattr(self, 'batch_tab_frame') and self.batch_tab_frame in self._built_tabs:
            if 'bulk_urls' in self._pending_gui_state:
                bulk_urls = self._pending_gui_state.pop('bulk_urls', None)
                bulk_playlists = self._pending_gui_state.pop('bulk_playlists', None) or []
                if bulk_urls:
                    self._restore_bulk_rows(bulk_urls, bulk_playlists)
                else:
                    self.clear_all_bulk_rows()

        for name, value in list(self._pending_gui_state.items()):
            widget = self._stateful_controls.get(name)
            if widget is None:
                continue
            if isinstance(widget, tk.BooleanVar):
                widget.set(bool(value))
            elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                self._set_entry_value(widget, value or '')
            elif isinstance(widget, scrolledtext.ScrolledText):
                self._set_text_value(widget, value or '')
            del self._pending_gui_state[name]

    def on_window_close(self):
        """Persist GUI-only state on close and then exit."""
        # Close is a one-way latch. Workers may still unwind after destroy(),
        # so they must see _closing before scheduling any Tk callback.
        self._closing = True
        self.download_after_playlist_parse = False
        self._download_cancel = True
        self._parse_cancel = True
        self._parse_generation += 1
        for attr in ('current_process', '_parse_process', '_parse_all_process'):
            process = getattr(self, attr, None)
            if process is not None:
                self._terminate_process(process)
                setattr(self, attr, None)
        self.save_config(silent=True)
        self.root.destroy()

    def on_url_changed(self, *args):
        """Reset playlist status when URL is manually changed by user."""
        # Invalidate the captured URL before touching the visible tree. This
        # prevents a slow response for the previous URL from winning later.
        was_parsing = getattr(self, '_parse_running', False)
        self._parse_generation += 1
        self._parse_cancel = True
        if was_parsing:
            process = self._parse_process
            self._parse_process = None
            if process is not None:
                self._terminate_process(process)
            self._parse_running = False
            self._runner_kind = None
            if not self._closing:
                self.root.after(0, self._set_parse_button_state, False)
        current_url = self.url_var.get().strip()
        if getattr(self, 'playlist_parsed_url', None) and current_url != self.playlist_parsed_url:
            self.clear_playlist_parse_state()
            self.status_var.set(self.tr('Ready'))

    def _terminate_process(self, process):
        """Terminate a GUI-owned process and its children, then reap it."""
        terminate_process(process)

    def clear_playlist_parse_state(self):
        """Drop parsed playlist tree/state so it cannot hijack a later batch/single download."""
        self.playlist_parsed_url = None
        self.playlist_parse_is_real_playlist = False
        self.playlist_entries_data = []
        self.playlist_requested_entries = None
        self.vis_to_orig = {}
        if hasattr(self, 'playlist_tree'):
            with contextlib.suppress(Exception):
                self.playlist_tree.delete(*self.playlist_tree.get_children())

    def _parse_request_is_current(self, generation):
        return (not self._closing
                and not self._parse_cancel
                and generation == self._parse_generation)

    def create_widgets(self):
        """Create all GUI widgets"""
        before_names = set(self.__dict__)
        # Top frame for URL input and quick actions
        top_frame = ttk.Frame(self.root, padding='10')
        top_frame.pack(fill=tk.X, side=tk.TOP)

        self.language_label = ttk.Label(top_frame, text='Language:')
        self.language_label.grid(row=0, column=2, sticky=tk.E, pady=5, padx=(20, 5))
        self.language_selector = ttk.Combobox(
            top_frame,
            width=16,
            textvariable=self.language_var,
            values=list(LANGUAGE_OPTIONS.values()),
            state='readonly')
        self.language_selector.grid(row=0, column=3, sticky=tk.W, pady=5)
        # The trace handles the change, but keeping bind for compatibility
        self.language_selector.bind('<<ComboboxSelected>>', self.on_language_changed)

        # URL input
        url_btn_frame = ttk.Frame(top_frame)
        url_btn_frame.grid(row=0, column=0, sticky=tk.W, pady=5)

        self.paste_url_btn = ttk.Button(url_btn_frame, text='Paste and Parse Link:', command=self.paste_url_from_clipboard)
        self.paste_url_btn.pack(side=tk.LEFT)
        self.register_translatable_widget(self.paste_url_btn, 'Paste and Parse Link:')

        self.playlist_btn = ttk.Button(url_btn_frame, text='Parse Playlist', command=self.parse_playlist, width=15)
        self.playlist_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.register_translatable_widget(self.playlist_btn, 'Parse Playlist')

        self.paste_parse_download_btn = ttk.Button(
            url_btn_frame, text='Paste Parse Download', command=self.paste_parse_download_from_clipboard, width=18)
        self.paste_parse_download_btn.pack(side=tk.LEFT, padx=(5, 0))
        self.register_translatable_widget(self.paste_parse_download_btn, 'Paste Parse Download')

        self.url_var = tk.StringVar()
        self.url_var.trace_add('write', self.on_url_changed)
        self.url_entry = ttk.Entry(top_frame, width=80, textvariable=self.url_var)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        top_frame.columnconfigure(1, weight=1)

        # Batch file option (removed UI entry as requested). Provide a minimal
        # dummy entry object so existing code calling .get/.delete/.insert won't crash.
        class _NullEntry:
            def delete(self, *a, **k):
                return None

            def insert(self, *a, **k):
                return None

            def get(self):
                return ''

            def focus_set(self):
                return None

        self.batch_file_entry = _NullEntry()

        # Quick action buttons
        button_frame = ttk.Frame(top_frame)
        # Move up since the intermediate batch row was removed
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        # 在 macOS 上，使用 tk.Label 模拟按钮是实现纯色背景最可靠的方法
        self.download_btn = tk.Label(button_frame, text='Download',
                                     bg='#28a745', fg='white',
                                     width=15, height=1,
                                     relief=tk.RAISED, cursor='hand2')
        self.download_btn.pack(side=tk.LEFT, padx=5, ipady=3)  # 增加内边距让它更高一点

        # 绑定点击事件：在松开鼠标时触发下载
        self.download_btn.bind('<ButtonRelease-1>', self._handle_label_release)
        self.download_btn.bind('<ButtonPress-1>', self._handle_label_press)

        self.register_translatable_widget(self.download_btn, 'Download')

        btn_open_folder = ttk.Button(button_frame, text='Open Output Folder', command=self.open_output_folder, width=15)
        btn_open_folder.pack(side=tk.LEFT, padx=5)
        self.register_translatable_widget(btn_open_folder, 'Open Output Folder')

        btn_list = ttk.Button(button_frame, text='List Formats', command=self.list_formats, width=15)
        btn_list.pack(side=tk.LEFT, padx=5)
        self.register_translatable_widget(btn_list, 'List Formats')

        btn_ext = ttk.Button(button_frame, text='Extract Info', command=self.extract_info, width=15)
        btn_ext.pack(side=tk.LEFT, padx=5)
        self.register_translatable_widget(btn_ext, 'Extract Info')

        btn_load = ttk.Button(button_frame, text='Load Config', command=self.load_config_dialog, width=15)
        btn_load.pack(side=tk.LEFT, padx=5)
        self.register_translatable_widget(btn_load, 'Load Config')

        btn_save = ttk.Button(button_frame, text='Save Config', command=self.save_config_dialog, width=15)
        btn_save.pack(side=tk.LEFT, padx=5)
        self.register_translatable_widget(btn_save, 'Save Config')

        # Separator
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # Notebook for tabbed options
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

        # Register tabs for lazy creation
        self.batch_tab_frame = self.add_lazy_tab('batch', 'Batch Download', self.create_batch_download_tab)

        # Insert Playlist tab so it appears before the General tab
        self.playlist_tab_frame = self.create_playlist_tab()
        if self.playlist_tab_frame is None:
            self.playlist_tab_frame = ttk.Frame(self.notebook, padding='10')
            self.create_playlist_tab(self.playlist_tab_frame)
        self.notebook.add(self.playlist_tab_frame, text='Playlist')
        self._built_tabs.add(self.playlist_tab_frame)
        self._notebook_tab_texts[self.playlist_tab_frame] = 'Playlist'

        # General tab comes after Playlist now
        self.add_lazy_tab('general', 'General', self.create_general_tab)
        self.add_lazy_tab('network', 'Network', self.create_network_tab)
        # ... rest of lazy tabs
        self.add_lazy_tab('geo', 'Geo-restriction', self.create_geo_restriction_tab)
        self.add_lazy_tab('video_selection', 'Video Selection', self.create_video_selection_tab)
        self.add_lazy_tab('download', 'Download', self.create_download_tab)
        self.add_lazy_tab('filesystem', 'Filesystem', self.create_filesystem_tab)
        self.add_lazy_tab('video_format', 'Video Format', self.create_video_format_tab)
        self.add_lazy_tab('subtitles', 'Subtitles', self.create_subtitle_tab)
        self.add_lazy_tab('authentication', 'Authentication', self.create_authentication_tab)
        self.add_lazy_tab('postprocessing', 'Post-processing', self.create_postprocessing_tab)
        self.add_lazy_tab('thumbnail', 'Thumbnail', self.create_thumbnail_tab)
        self.add_lazy_tab('verbosity', 'Verbosity/Simulation', self.create_verbosity_tab)
        self.add_lazy_tab('workarounds', 'Workarounds', self.create_workarounds_tab)
        self.add_lazy_tab('sponsorblock', 'SponsorBlock', self.create_sponsorblock_tab)
        self.add_lazy_tab('extractor', 'Extractor', self.create_extractor_tab)
        self.add_lazy_tab('advanced', 'Advanced', self.create_advanced_tab)
        self.ensure_tab_built(self.batch_tab_frame)
        self._active_tab_frame = self.batch_tab_frame

        # Output console at bottom
        console_frame = ttk.LabelFrame(self.root, text='Output Console', padding='5')
        console_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10), ipady=5)

        self.console = scrolledtext.ScrolledText(console_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        self.console.pack(fill=tk.BOTH, expand=True)

        # Status bar
        # Status bar with dual panes (Status | Progress)
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value='Ready')
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, padx=5, pady=2)

        self.progress_var = tk.StringVar(value='')
        # Using a distinct color and larger font for progress
        self.progress_label = ttk.Label(status_frame, textvariable=self.progress_var, anchor=tk.E, font=('TkDefaultFont', 11, 'bold'), foreground='#0056b3')
        self.progress_label.pack(side=tk.RIGHT, padx=10, pady=2)

        self.status_var.set(self.tr('Ready'))
        self.register_stateful_controls(set(self.__dict__) - before_names)

        # Apply initial localization based on detected/configured language
        self.apply_localization()

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

        btn_paste_top = ttk.Button(header_row, text=self.tr('Paste to Top'), command=self.paste_bulk_to_top)
        btn_paste_top.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_paste_top, 'Paste to Top')
        btn_paste_bottom = ttk.Button(header_row, text=self.tr('Paste to Bottom'), command=self.paste_bulk_to_bottom)
        btn_paste_bottom.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_paste_bottom, 'Paste to Bottom')
        btn_parse_all = ttk.Button(header_row, text=self.tr('Parse All'), command=self.parse_all_bulk_urls)
        btn_parse_all.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_parse_all, 'Parse All')

        # Keep clear pool in header row to the right
        btn_clear = ttk.Button(header_row, text=self.tr('Clear Pool'), command=self.clear_all_bulk_rows)
        btn_clear.pack(side=tk.RIGHT)
        self.register_translatable_widget(btn_clear, 'Clear Pool')

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

        # Bind mousewheel events for smooth scrolling on this canvas
        self._bind_batch_mousewheel()

        # Controls row removed: Bulk Paste and Parse Batch buttons were intentionally deleted
        # per user request. Keep dynamic rows and clear button intact.
        self.bulk_rows = []
        self.add_bulk_row()

        return frame

    def _bind_batch_mousewheel(self):
        self.bulk_canvas.bind('<Enter>', lambda e: self.bulk_canvas.bind_all('<MouseWheel>', self._on_batch_mousewheel))
        self.bulk_canvas.bind('<Leave>', lambda e: self.bulk_canvas.unbind_all('<MouseWheel>'))
        self.bulk_canvas.bind('<Enter>', lambda e: [
            self.bulk_canvas.bind_all('<Button-4>', self._on_batch_mousewheel),
            self.bulk_canvas.bind_all('<Button-5>', self._on_batch_mousewheel),
        ], add='+')
        self.bulk_canvas.bind('<Leave>', lambda e: [
            self.bulk_canvas.unbind_all('<Button-4>'),
            self.bulk_canvas.unbind_all('<Button-5>'),
        ], add='+')

    def _on_batch_mousewheel(self, event):
        if event.num == 4:
            self.bulk_canvas.yview_scroll(-2, 'units')
        elif event.num == 5:
            self.bulk_canvas.yview_scroll(2, 'units')
        else:
            if abs(event.delta) >= 120:
                scroll_units = -2 * int(event.delta / 120)
            else:
                scroll_units = -2 * event.delta
            self.bulk_canvas.yview_scroll(scroll_units, 'units')

    def _on_drag_start(self, event, row_frame):
        self._drag_data = {
            'row': row_frame,
            'y': event.y_root,
        }

    def _on_drag_motion(self, event, row_frame):
        if not hasattr(self, '_drag_data') or not self._drag_data:
            return
        delta_y = event.y_root - self._drag_data['y']
        if abs(delta_y) < 10:
            return
        children = self.bulk_scroll_frame.winfo_children()
        try:
            idx = children.index(row_frame)
        except ValueError:
            return
        if delta_y > 0 and idx < len(children) - 1:
            next_row = children[idx + 1]
            if event.y_root > next_row.winfo_rooty() + (next_row.winfo_height() / 2):
                self._swap_rows(idx, idx + 1)
                self._drag_data['y'] = event.y_root
        elif delta_y < 0 and idx > 0:
            prev_row = children[idx - 1]
            if event.y_root < prev_row.winfo_rooty() + (prev_row.winfo_height() / 2):
                self._swap_rows(idx - 1, idx)
                self._drag_data['y'] = event.y_root

    def _on_drag_stop(self, event, row_frame):
        self._drag_data = None
        self.trigger_autosave()

    def _swap_rows(self, idx1, idx2):
        self.bulk_rows[idx1], self.bulk_rows[idx2] = self.bulk_rows[idx2], self.bulk_rows[idx1]
        for r in self.bulk_rows:
            r['frame'].pack_forget()
        for r in self.bulk_rows:
            r['frame'].pack(fill=tk.X, pady=2)

    def add_bulk_row(self, initial_text='', initial_playlist='', auto_parse_playlist=False):
        row = ttk.Frame(self.bulk_scroll_frame)
        row.pack(fill=tk.X, pady=2)

        # Add drag handle
        lbl_drag = ttk.Label(row, text=' ☰ ', cursor='fleur')
        lbl_drag.pack(side=tk.LEFT, padx=(5, 2))
        lbl_drag.bind('<Button-1>', lambda e, r=row: self._on_drag_start(e, r))
        lbl_drag.bind('<B1-Motion>', lambda e, r=row: self._on_drag_motion(e, r))
        lbl_drag.bind('<ButtonRelease-1>', lambda e, r=row: self._on_drag_stop(e, r))

        var = tk.StringVar(value=initial_text)
        var.trace_add('write', self.trigger_autosave)
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        playlist_var = tk.StringVar(value=initial_playlist)
        playlist_var.trace_add('write', self.trigger_autosave)
        playlist_entry = ttk.Entry(row, textvariable=playlist_var, width=20)
        playlist_entry.pack(side=tk.LEFT, padx=(0, 5))

        entry.bind('<Return>', lambda e: self._on_bulk_url_return(var.get().strip(), playlist_var) if var.get().strip() else None)

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
        self.bulk_rows.append({'frame': row, 'var': var, 'playlist_var': playlist_var})

        if auto_parse_playlist and initial_text.strip():
            self._fetch_playlist_title_async(initial_text.strip(), playlist_var)

        # Immediate sync for this newly added row
        self.localize_widget_tree(row)

    def remove_bulk_row(self, frame):
        frame.destroy()
        self.bulk_rows = [r for r in self.bulk_rows if r['frame'] != frame]
        if not self.bulk_rows:
            self.add_bulk_row()
        self.trigger_autosave()

    def remove_batch_row(self, frame):
        """Compatibility alias for previous function name."""
        self.remove_bulk_row(frame)

    def _extract_urls_from_clipboard(self):
        """Extract HTTP URLs from clipboard text (case insensitive)."""
        try:
            raw = self.root.clipboard_get()
            import re
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', raw, re.IGNORECASE)
            return [u.strip() for u in urls if u.strip()]
        except Exception:
            return []

    def paste_bulk_to_top(self):
        """Paste URLs from clipboard to the top of bulk rows."""
        urls = self._extract_urls_from_clipboard()
        if not urls:
            self.log_message(self.tr('No HTTP URLs found in clipboard'))
            return
        # Insert at beginning
        for url in reversed(urls):
            self.add_bulk_row_at_index(0, url, auto_parse_playlist=True)
        self.log_message(self.translate_concat('Pasted ', f'{len(urls)}') + self.tr(' URL(s) to top'))
        self.trigger_autosave()

    def paste_bulk_to_bottom(self):
        """Paste URLs from clipboard to the bottom of bulk rows."""
        urls = self._extract_urls_from_clipboard()
        if not urls:
            self.log_message(self.tr('No HTTP URLs found in clipboard'))
            return
        for url in urls:
            self.add_bulk_row(url, auto_parse_playlist=True)
        self.log_message(self.translate_concat('Pasted ', f'{len(urls)}') + self.tr(' URL(s) to bottom'))
        self.trigger_autosave()

    def parse_all_bulk_urls(self):
        """Serially resolve bulk-row titles; full playlist tree parse only for a single URL.

        Multiple concurrent parse_playlist threads share one tree and race. For many bulk
        URLs we fetch titles one-by-one into each row. With exactly one URL we still open
        the full playlist selector.
        """
        if getattr(self, '_parse_all_running', False):
            self.log_message(self.tr('[DEBUG] Parse All already running — ignored.'))
            return

        targets = []
        for row in getattr(self, 'bulk_rows', []):
            url = (row.get('var').get() if row.get('var') is not None else '').strip()
            if url:
                targets.append((row, url))

        if not targets:
            self.log_message(self.tr('No valid batch URLs found.'))
            return

        if len(targets) == 1:
            self._parse_single_row_url(targets[0][1])
            return

        parse_options = self.collect_parse_options()
        self.status_var.set(self.tr('Checking URL...'))
        self.log_message(self.translate_concat('Parsing bulk URLs: ', f'{len(targets)}'))
        self._parse_all_running = True

        def worker():
            ok = 0
            try:
                for index, (row, url) in enumerate(targets, start=1):
                    if not getattr(self, '_parse_all_running', False):
                        break
                    title_var = row.get('playlist_var')
                    try:
                        cmd = [
                            *core_launcher(),
                            '--flat-playlist', '--dump-single-json', '--no-cache-dir',
                            '--ignore-no-formats-error',
                            '--remote-components', 'ejs:github',
                        ]
                        self.apply_parse_options_to_cmd(cmd, parse_options)
                        cmd.append(url)
                        env = self._subprocess_env()
                        popen_kwargs = {
                            'stdout': subprocess.PIPE,
                            'stderr': subprocess.PIPE,
                            'env': env,
                            **self._subprocess_text_kwargs(),
                        }
                        if os.name == 'nt':
                            popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                        else:
                            popen_kwargs['start_new_session'] = True
                        proc = subprocess.Popen(cmd, **popen_kwargs)
                        self._parse_all_process = proc
                        try:
                            stdout_data, _stderr_data = proc.communicate(timeout=45)
                        except subprocess.TimeoutExpired:
                            self._terminate_process(proc)
                            raise
                        finally:
                            if getattr(self, '_parse_all_process', None) is proc:
                                self._parse_all_process = None

                        if not getattr(self, '_parse_all_running', False):
                            break

                        title = ''
                        if stdout_data:
                            info = json.loads(stdout_data)
                            title = (info.get('title') or info.get('id') or '').strip()
                        if title and title_var is not None:
                            self.root.after(0, lambda t=title, v=title_var: v.set(t))
                            ok += 1
                        self.log_message(f'[{index}/{len(targets)}] {title or url}')
                    except Exception as e:
                        self.log_message(self.translate_concat(f'[{index}/{len(targets)}] ', str(e)))
                self.log_message(
                    self.translate_concat('Batch parsed: ', f'{ok}/{len(targets)}')
                    + self.tr(' URL(s) ready.'))
            finally:
                self._parse_all_running = False
                self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))

        threading.Thread(target=worker, daemon=True).start()

    def add_bulk_row_at_index(self, index, initial_text='', initial_playlist='', auto_parse_playlist=False):
        """Add a bulk row at specific index position."""
        row = ttk.Frame(self.bulk_scroll_frame)

        # Add drag handle
        lbl_drag = ttk.Label(row, text=' ☰ ', cursor='fleur')
        lbl_drag.pack(side=tk.LEFT, padx=(5, 2))
        lbl_drag.bind('<Button-1>', lambda e, r=row: self._on_drag_start(e, r))
        lbl_drag.bind('<B1-Motion>', lambda e, r=row: self._on_drag_motion(e, r))
        lbl_drag.bind('<ButtonRelease-1>', lambda e, r=row: self._on_drag_stop(e, r))

        var = tk.StringVar(value=initial_text)
        var.trace_add('write', self.trigger_autosave)
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        playlist_var = tk.StringVar(value=initial_playlist)
        playlist_var.trace_add('write', self.trigger_autosave)
        playlist_entry = ttk.Entry(row, textvariable=playlist_var, width=20)
        playlist_entry.pack(side=tk.LEFT, padx=(0, 5))

        entry.bind('<Return>', lambda e: self._on_bulk_url_return(var.get().strip(), playlist_var) if var.get().strip() else None)

        btn_parse = ttk.Button(row, text=self.tr('Parse'), width=8, command=lambda v=var: self._parse_single_row_url(v.get()))
        btn_parse.pack(side=tk.LEFT, padx=2)
        self.register_translatable_widget(btn_parse, 'Parse')

        btn_remove = ttk.Button(row, text='-', width=3, command=lambda r=row: self.remove_bulk_row(r))
        btn_remove.pack(side=tk.LEFT)

        # Insert into list at index
        self.bulk_rows.insert(index, {'frame': row, 'var': var, 'playlist_var': playlist_var})
        self.localize_widget_tree(row)

        if auto_parse_playlist and initial_text.strip():
            self._fetch_playlist_title_async(initial_text.strip(), playlist_var)

        # Re-pack all rows in order
        for r in self.bulk_rows:
            r['frame'].pack_forget()
        for r in self.bulk_rows:
            r['frame'].pack(fill=tk.X, pady=2)

    def clear_all_bulk_rows(self):
        for row in self.bulk_rows[1:]:
            row['frame'].destroy()
        if self.bulk_rows:
            self.bulk_rows = self.bulk_rows[:1]
            self.bulk_rows[0]['var'].set('')
            if 'playlist_var' in self.bulk_rows[0]:
                self.bulk_rows[0]['playlist_var'].set('')
        self.trigger_autosave()

    def _restore_bulk_rows(self, urls, playlists=None):
        """Restore bulk_rows from saved URLs."""
        if not urls:
            return
        if playlists is None:
            playlists = []

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        unique_playlists = []
        for i, url in enumerate(urls):
            norm_url = url.strip()
            if not norm_url:
                continue
            if norm_url in seen:
                continue
            seen.add(norm_url)
            unique_urls.append(url)
            pl = playlists[i] if i < len(playlists) else ''
            unique_playlists.append(pl)

        urls = unique_urls
        playlists = unique_playlists

        # Clear existing rows first
        for row in self.bulk_rows[1:]:
            row['frame'].destroy()
        if self.bulk_rows:
            self.bulk_rows[0]['var'].set(urls[0] if urls else '')
            if 'playlist_var' in self.bulk_rows[0]:
                self.bulk_rows[0]['playlist_var'].set(playlists[0] if playlists else '')
            self.bulk_rows = self.bulk_rows[:1]
            urls = urls[1:]
            playlists = playlists[1:] if playlists else []
        for i, url in enumerate(urls):
            pl = playlists[i] if i < len(playlists) else ''
            self.add_bulk_row(url, initial_playlist=pl)

    def _on_bulk_url_return(self, url, title_var):
        if url:
            self._fetch_playlist_title_async(url, title_var)

    def _fetch_playlist_title_async(self, url, title_var):
        cookies_from_browser = self.get_control_text('cookies_from_browser')
        cookies = self.get_control_text('cookies')

        def worker():
            try:
                cmd = [*core_launcher(), '--flat-playlist', '--dump-single-json', url]
                if cookies_from_browser:
                    cmd.extend(['--cookies-from-browser', cookies_from_browser])
                if cookies:
                    cmd.extend(['--cookies', cookies])

                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    timeout=15, env=self._subprocess_env(), **self._subprocess_text_kwargs())
                if result.stdout:
                    info = json.loads(result.stdout)
                    title = info.get('title')
                    if title:
                        self.root.after(0, lambda: title_var.set(title))
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _parse_single_row_url(self, url):
        url = (url or '').strip()
        if not url:
            return
        self._is_from_bulk_parse_flag = True
        self.url_var.set(url)
        self.parse_playlist()

    def parse_single_url(self, url):
        """Compatibility alias for previous function name."""
        self._parse_single_row_url(url)

    def parse_batch(self):
        """Parse all batch inputs and normalize them into the main batch input box."""
        file_path = self.get_batch_file_value()
        row_urls = self.get_bulk_urls()
        thread = threading.Thread(target=self._parse_batch_worker, args=(file_path, row_urls), daemon=True)
        thread.start()

    def _parse_batch_worker(self, file_path, row_urls):
        urls = []

        if file_path and os.path.isfile(file_path):
            try:
                urls.extend(self.read_batch_file_urls(file_path))
            except Exception as e:
                self.log_message(self.translate_concat('Error reading batch file: ', str(e)))
        elif file_path:
            urls.extend(line.strip() for line in file_path.splitlines() if line.strip())

        urls.extend(row_urls)

        normalized = self.dedupe_preserve_order(urls)

        if not normalized:
            self.log_message(self.tr('No valid batch URLs found.'))
            self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))
            return

        self.root.after(0, lambda: self._restore_bulk_rows(normalized))
        self.root.after(0, lambda: self.batch_file_var.set(''))
        self.log_message(self.translate_concat('Batch parsed: ', f'{len(normalized)}') + self.tr(' URL(s) ready.'))
        self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))

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

    # Lazy tab builders delegated to guiapi.tab_builders
    create_general_tab = tab_builders.create_general_tab
    create_network_tab = tab_builders.create_network_tab
    create_geo_restriction_tab = tab_builders.create_geo_restriction_tab
    create_video_selection_tab = tab_builders.create_video_selection_tab
    create_download_tab = tab_builders.create_download_tab
    create_filesystem_tab = tab_builders.create_filesystem_tab
    create_video_format_tab = tab_builders.create_video_format_tab
    _on_res_selected = tab_builders._on_res_selected
    _on_res_mouse_release = tab_builders._on_res_mouse_release
    create_subtitle_tab = tab_builders.create_subtitle_tab
    get_smart_subtitle_lang_code = tab_builders.get_smart_subtitle_lang_code
    build_smart_sub_langs = tab_builders.build_smart_sub_langs
    create_authentication_tab = tab_builders.create_authentication_tab
    create_postprocessing_tab = tab_builders.create_postprocessing_tab
    create_thumbnail_tab = tab_builders.create_thumbnail_tab
    create_verbosity_tab = tab_builders.create_verbosity_tab
    create_workarounds_tab = tab_builders.create_workarounds_tab
    create_sponsorblock_tab = tab_builders.create_sponsorblock_tab
    _set_sb_group = tab_builders._set_sb_group
    create_extractor_tab = tab_builders.create_extractor_tab
    create_advanced_tab = tab_builders.create_advanced_tab

    # File browser methods
    def browse_batch_file(self):
        filename = filedialog.askopenfilename(
            title=self.tr('Select Batch File'),
            filetypes=[(self.tr('Text Files'), '*.txt'), (self.tr('All Files'), '*.*')])
        if filename:
            if hasattr(self, 'batch_file_var'):
                self.batch_file_var.set(filename)
            # batch_file_entry may be a NullEntry stub; still attempt write for compatibility
            self.batch_file_entry.delete(0, tk.END)
            self.batch_file_entry.insert(0, filename)
            self.trigger_autosave()

    def paste_url_from_clipboard(self):
        if not self._paste_clipboard_to_url_entry():
            return

        # Trigger parsing automatically
        self.parse_playlist()

    def paste_parse_download_from_clipboard(self):
        if not self._paste_clipboard_to_url_entry():
            return

        self.download_after_playlist_parse = True
        self.parse_playlist()

    def _paste_clipboard_to_url_entry(self):
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
        return True

    def paste_playlist_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get().strip()
        except tk.TclError:
            clipboard_text = ''

        if not clipboard_text:
            self.log_message(self.tr('Clipboard is empty.'))
            return

        lines = [l.strip() for l in clipboard_text.splitlines() if l.strip()]
        if not lines:
            self.log_message(self.tr('Clipboard is empty.'))
            return

        # Prefer bulk rows (real batch UI); batch_file_entry is a NullEntry stub.
        if hasattr(self, 'bulk_rows') and self.bulk_rows is not None:
            # Ensure Batch tab exists so bulk_rows widgets are real
            if hasattr(self, 'batch_tab_frame'):
                self.ensure_tab_built(self.batch_tab_frame)
            self._restore_bulk_rows(lines)
        if hasattr(self, 'batch_file_var'):
            # Keep a single multi-line path only when one file path is pasted
            if len(lines) == 1 and not lines[0].startswith('http') and os.path.isfile(lines[0]):
                self.batch_file_var.set(lines[0])
            else:
                self.batch_file_var.set('')

        # If it's a single URL and the main URL entry is empty, duplicate it there for convenience
        if len(lines) == 1 and lines[0].startswith('http') and not self.url_entry.get().strip():
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, lines[0])

        self.log_message(self.tr('Pasted playlist from clipboard.'))
        self.trigger_autosave()

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

    def open_output_folder(self):
        if not hasattr(self, 'output_dir'):
            self.ensure_named_tab_built('filesystem')
        if not hasattr(self, 'output_dir'):
            messagebox.showwarning(self.tr('Warning'), self.tr('Please set an output directory first'))
            return
        output_dir = self.output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning(self.tr('Warning'), self.tr('Please set an output directory first'))
            return
        if not os.path.exists(output_dir):
            messagebox.showwarning(self.tr('Warning'), self.tr('Output directory does not exist'))
            return
        # Open folder using platform-specific command
        import platform
        system = platform.system()
        try:
            if system == 'Darwin':  # macOS
                subprocess.run(['open', output_dir])
            elif system == 'Windows':
                subprocess.run(['explorer', output_dir])
            else:  # Linux
                subprocess.run(['xdg-open', output_dir])
        except Exception as e:
            messagebox.showerror(self.tr('Error'), f"{self.tr('Failed to open folder')}:\n{e}")

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

    def build_command_args(self):
        """Build yt-dlp command arguments from GUI settings"""
        return build_command_args_from_app(self)

    def _cleanup_temp_files(self):
        if hasattr(self, '_temp_batch_files'):
            for f in self._temp_batch_files:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass
            self._temp_batch_files.clear()

    def generate_command(self):
        """Generate and display the yt-dlp command"""
        args = self.build_command_args()
        cmd = [*core_launcher(), *args]
        # This string is for copy/paste only; execution always uses the list.
        # Quote every argument because formats and URLs commonly contain shell
        # metacharacters such as '<', '>', '&', and '|'.
        cmd_str = subprocess.list2cmdline(cmd) if os.name == 'nt' else shlex.join(cmd)

        self.generated_cmd.config(state=tk.NORMAL)
        self.generated_cmd.delete('1.0', tk.END)
        self.generated_cmd.insert('1.0', cmd_str)
        self.generated_cmd.config(state=tk.DISABLED)

    def copy_command(self):
        """Copy generated command to clipboard"""
        self.generate_command()
        cmd_text = self.generated_cmd.get('1.0', tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd_text)
        self.log_message('Command copied to clipboard!')

    def run_ytdlp(self, tasks):
        """Run a list of yt-dlp tasks (args sets) sequentially"""
        # Keep subprocess I/O off the Tk thread. UI changes use root.after;
        # log_message remains queue-safe, while Tk callbacks stop on close.
        try:
            total = len(tasks)
            for i, (idx, args) in enumerate(tasks):
                if getattr(self, '_download_cancel', False):
                    self.log_message(self.tr('Stopping download...'))
                    break

                self.log_message(f'[{i + 1}/{total}] ' + self.tr('Download Task: Index ') + f'{idx}')
                if not self._closing:
                    self.root.after(
                        0,
                        lambda i=i, total=total: self.status_var.set(
                            f'{self.tr("Downloading")} {i + 1}/{total}'),
                    )

                if idx != 'Single' and str(idx).isdigit():
                    def highlight_row(v_idx):
                        if hasattr(self, 'playlist_tree'):
                            for child in self.playlist_tree.get_children():
                                vals = self.playlist_tree.item(child, 'values')
                                if vals and str(vals[1]) == str(v_idx):
                                    self.playlist_tree.selection_set(child)
                                    self.playlist_tree.see(child)
                                    break
                    if not self._closing:
                        self.root.after(0, highlight_row, idx)

                if getattr(self, '_download_cancel', False):
                    break

                full_cmd = [*core_launcher(), '--remote-components', 'ejs:github', *args]
                self.log_message(self.tr('[DEBUG] 执行命令: ') + ' '.join(sanitize_command(full_cmd)))
                env = self._subprocess_env()

                popen_kwargs = {
                    'stdout': subprocess.PIPE,
                    'stderr': subprocess.STDOUT,
                    'env': env,
                    **self._subprocess_text_kwargs(),
                }
                if os.name == 'nt':
                    popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                else:
                    popen_kwargs['start_new_session'] = True
                self.current_process = subprocess.Popen(full_cmd, **popen_kwargs)
                process = self.current_process
                task_output_lines = []

                if process.stdout:
                    for line in process.stdout:
                        if line:
                            translated_line = self.translate_yt_dlp_line(line.rstrip())
                            task_output_lines.append(translated_line)
                            self.log_message(translated_line)

                process.wait()

                if process.returncode != 0 and process.returncode not in (15, -15):
                    self.log_message(self.translate_concat('Task failed with code ', process.returncode))
                    if 'n challenge solving failed' in '\n'.join(task_output_lines):
                        self.log_message(self.tr('\n[!] Warning: Missing JavaScript runtime environment.'))
                        self.log_message(self.tr("[!] Please run 'brew install node' in the terminal to fix this download error."))
                    # We continue even if one fails

                if getattr(self, '_download_cancel', False) or self.current_process is None:
                    # User likely clicked Stop
                    break

            self.log_message(self.tr('All tasks processed.'))
            if not self._closing:
                self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))

        except Exception as e:
            self.log_message(self.translate_concat('ERROR in runner: ', str(e)))
            if not self._closing:
                self.root.after(0, lambda: self.status_var.set(self.tr('Error')))
        finally:
            self.current_process = None
            self._download_running = False
            self._download_cancel = False
            self._runner_kind = None
            if not self._closing:
                self.root.after(0, self._restore_download_button)
                self.root.after(0, lambda: self.root.title(self.tr(self.base_title)))

    def _restore_download_button(self):
        if hasattr(self, 'download_btn'):
            # 恢复为绿色
            def _restore():
                self.download_btn.config(text=self.tr('Download'), background='#28a745', bg='#28a745')
                self.download_btn.update()
            self.root.after(10, _restore)
            self._translatable_widgets[self.download_btn] = 'Download'

    def _handle_label_press(self, event):
        self.download_btn.config(relief=tk.SUNKEN)

    def _handle_label_release(self, event):
        self.download_btn.config(relief=tk.RAISED)
        self.on_download_btn_click()

    def on_download_btn_click(self):
        self.log_message(self.tr('[DEBUG] Download button clicked.'))
        if (getattr(self, '_download_running', False)
                or getattr(self, 'current_process', None)
                or getattr(self, '_parse_running', False)
                or getattr(self, '_parse_all_running', False)):
            self.stop_download()
        else:
            self.start_download()

    def _on_escape_key(self, _event=None):
        """Escape acts as the Stop button when a job is running."""
        if (getattr(self, '_download_running', False)
                or getattr(self, 'current_process', None)
                or getattr(self, '_parse_running', False)
                or getattr(self, '_parse_all_running', False)):
            self.stop_download()
            return 'break'
        return None

    def _get_playlist_entry_download_url(self, original_idx, fallback_url):
        entries = getattr(self, 'playlist_entries_data', None) or []
        if not entries or original_idx is None:
            return None

        # Prefer mapping absolute playlist positions via requested_entries when present.
        # entries may be densified (privates omitted) while original_idx is absolute.
        entry = None
        req_entries = getattr(self, 'playlist_requested_entries', None)
        if req_entries:
            try:
                dense_pos = list(req_entries).index(original_idx)
                if 0 <= dense_pos < len(entries):
                    entry = entries[dense_pos]
            except ValueError:
                entry = None
        if entry is None:
            if not (1 <= original_idx <= len(entries)):
                return None
            entry = entries[original_idx - 1]
        if not entry:
            return None

        entry_id = str(entry.get('id') or '').strip()
        ie_key = str(entry.get('ie_key') or entry.get('extractor_key') or '').lower()
        fallback_is_youtube = 'youtube.com/' in fallback_url or 'youtu.be/' in fallback_url
        is_youtube_entry = fallback_is_youtube or ie_key.startswith('youtube')

        if is_youtube_entry and entry_id:
            return f'https://www.youtube.com/watch?v={entry_id}'

        for key in ('webpage_url', 'url'):
            entry_url = str(entry.get(key) or '').strip()
            if entry_url.startswith(('http://', 'https://')):
                return entry_url

        return None

    def stop_download(self):
        if getattr(self, '_parse_all_running', False):
            self._parse_all_running = False
            process = getattr(self, '_parse_all_process', None)
            self._parse_all_process = None
            if process is not None:
                self._terminate_process(process)
            self.log_message(self.tr('Stopping bulk parse...'))
            if not self._closing:
                self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))
            return

        if getattr(self, '_parse_running', False):
            self._parse_cancel = True
            self._parse_generation += 1
            self.download_after_playlist_parse = False
            process = self._parse_process
            self._parse_process = None
            if process is not None:
                self._terminate_process(process)
            self._parse_running = False
            self._runner_kind = None
            self.log_message(self.tr('Stopping playlist parse...'))
            if not self._closing:
                self.root.after(0, self._restore_download_button)
                self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))
            return

        if not getattr(self, '_download_running', False) and not getattr(self, 'current_process', None):
            self.log_message(self.tr('No download currently running.'))
            return

        # Always set cancel so the runner will not start the next task / Popen
        # even if current_process is still None (race after Download click).
        self._download_cancel = True
        process = getattr(self, 'current_process', None)
        self.current_process = None  # Signal runner loop after current process exits
        self.log_message(self.tr('Stopping download...'))

        if process is not None:
            self._terminate_process(process)
            # No confirmation dialog — Stop / Esc should cancel immediately.

    def cleanup_partial_files(self):
        """Recursively remove .part/.ytdl fragment files under the output directory."""
        try:
            output_dir = self.get_control_text('output_dir')
        except Exception:
            output_dir = ''
        if not output_dir:
            widget = getattr(self, 'output_dir', None)
            if widget is not None:
                with contextlib.suppress(tk.TclError, Exception):
                    output_dir = str(widget.get() or '').strip()
        if not output_dir or not os.path.exists(output_dir):
            return

        def is_partial(filename):
            # yt-dlp partials: *.part, *.ytdl, or fragment names containing .f*.part
            return filename.endswith(('.part', '.ytdl')) or ('.f' in filename and filename.endswith('.part'))

        count = 0
        self.log_message(self.tr('Cleaning up partial files...'))
        try:
            for root_dir, _, files in os.walk(output_dir):
                for filename in files:
                    if not is_partial(filename):
                        continue
                    file_path = os.path.join(root_dir, filename)
                    try:
                        os.remove(file_path)
                        count += 1
                    except Exception as e:
                        rel = os.path.relpath(file_path, output_dir)
                        self.log_message(self.translate_concat('Failed to remove ', f'{rel}: {e}'))
            self.log_message(self.tr('Cleanup finished. Removed ') + f'{count}' + self.tr(' files.'))
        except Exception as e:
            self.log_message(self.tr('Error during cleanup: ') + str(e))

    def start_download(self):
        """Start download in a separate thread"""
        self.log_message(self.tr('[DEBUG] start_download called'))
        if (getattr(self, '_download_running', False)
                or getattr(self, 'current_process', None)
                or getattr(self, '_parse_running', False)
                or getattr(self, '_parse_all_running', False)):
            self.log_message(self.tr('A download is already running.'))
            return
        url = self.url_entry.get().strip()
        self.log_message(self.translate_concat('[DEBUG] url=', f'{url!r}'))
        try:
            base_args = self.build_command_args()
            self.log_message(self.translate_concat('[DEBUG] base_args count=', len(base_args) if base_args else 0))
        except Exception as e:
            import traceback
            self.log_message(self.translate_concat('[DEBUG] build_command_args CRASHED: ', str(e)))
            self.log_message(traceback.format_exc())
            self._restore_download_button()
            return

        if not base_args or not self.has_download_target():
            self.log_message(self.tr('[DEBUG] No URL or args — showing warning'))
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL or batch file to download.'))
            return

        output_dir = self.get_control_text('output_dir')
        if not output_dir:
            with contextlib.suppress(tk.TclError, Exception):
                output_dir = str(self.output_dir.get() or '').strip()
        self.log_message(self.translate_concat('[DEBUG] output_dir=', f'{output_dir!r}'))

        playlist_parsed_url = getattr(self, 'playlist_parsed_url', None)
        msg = self.tr('[DEBUG] URL match check: Input=') + f'"{url}"' + self.tr(', Parsed=') + f'"{playlist_parsed_url}"'
        self.log_message(msg)

        tasks = []
        # When the main URL is still the parsed playlist, always honor the file list
        # tree selection — even if the bulk pool holds many other URLs. Bulk/batch
        # only drives the job when there is no matching parse for the top URL field.
        # (Use the Batch tab download path / empty main URL matching bulk for multi-URL runs.)
        bulk_urls = self.get_bulk_urls()
        batch_file_value = self.get_batch_file_value()
        playlist_mode = bool(
            playlist_parsed_url
            and self.media_urls_equal(url, playlist_parsed_url)
            and hasattr(self, 'playlist_tree'),
        )
        if playlist_mode and (bulk_urls or batch_file_value):
            self.log_message(
                self.tr('[DEBUG] Using playlist tree selection (bulk pool ignored for this run).')
                + f' bulk_count={len(bulk_urls)}')
        # ONLY use playlist tasks if the URL matches what we parsed
        if playlist_mode:
            items = self.playlist_tree.get_children()
            # SIMPLICITY: Just follow the tree from TOP TO BOTTOM as shown in GUI.
            vis_to_orig_map = getattr(self, 'vis_to_orig', {})
            for item in items:
                vals = self.playlist_tree.item(item, 'values')
                if not vals or len(vals) < 2:
                    continue
                checked = vals[0] == '☑'
                try:
                    visual_idx = int(vals[1])
                except (TypeError, ValueError):
                    continue

                if checked:
                    gui_title = str(vals[2]) if len(vals) > 2 else f'Video {visual_idx}'
                    original_idx = vis_to_orig_map.get(visual_idx, visual_idx)
                    task_args = []
                    skip = False
                    for arg in base_args:
                        if skip:
                            skip = False
                            continue
                        # EXCLUDE batch file and redundant playlist items from individual tasks
                        if arg in ('--playlist-items', '--playlist-reverse', '--no-playlist-reverse',
                                   '--yes-playlist', '--no-playlist',
                                   '-o', '-P', '--paths', '-a', '--batch-file'):
                            if arg in ('--playlist-items', '-o', '-P', '--paths', '-a', '--batch-file'):
                                skip = True
                            continue
                        if arg == url:  # Don't add the main URL yet
                            continue
                        task_args.append(arg)

                    entry_download_url = self._get_playlist_entry_download_url(original_idx, url)
                    if entry_download_url:
                        task_args.append('--no-playlist')
                        task_args.append(entry_download_url)
                    else:
                        task_args.append(url)
                    filename_tpl = f'{visual_idx:03d}-{self.sanitize_path_component(gui_title, fallback=f"Video_{visual_idx}")}.%(ext)s'

                    # Handle playlist subfolder
                    final_output_dir = output_dir
                    if (self.playlist_subdir.get()
                            and getattr(self, 'playlist_parse_is_real_playlist', False)
                            and getattr(self, 'current_playlist_metadata_title', None)):
                        folder_name = self.sanitize_path_component(
                            self.current_playlist_metadata_title, fallback='Playlist')
                        if folder_name:
                            final_output_dir = os.path.join(output_dir, folder_name)
                            if not os.path.exists(final_output_dir):
                                os.makedirs(final_output_dir, exist_ok=True)

                    out_path = os.path.join(final_output_dir, filename_tpl) if final_output_dir else filename_tpl
                    if not entry_download_url:
                        task_args.extend(['--playlist-items', str(original_idx)])
                    task_args.extend(['-o', out_path])
                    tasks.append((visual_idx, task_args))

        # If no playlist tasks were built:
        # - In playlist mode with nothing checked: refuse (do not download whole list)
        # - Otherwise treat as single/batch via base_args
        if not tasks:
            if playlist_mode:
                self.log_message(self.tr('No playlist items selected.'))
                messagebox.showwarning(
                    self.tr('No Selection'),
                    self.tr('Please select at least one playlist item to download.'),
                )
                return
            tasks.append(('Single', base_args))

        # Change button to Stop only after tasks are ready
        def _to_stop():
            self.download_btn.config(text=self.tr('Stop'), background='#dc3545', bg='#dc3545')
            self.download_btn.update()
        self.root.after(10, _to_stop)
        self._translatable_widgets[self.download_btn] = 'Stop'
        self._download_cancel = False
        self._runner_kind = 'download'
        self._download_running = True

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.run_ytdlp, args=(tasks,), daemon=True)
        thread.start()

    def parse_playlist(self):
        # Starting Parse again is an explicit cancel/restart gesture rather than
        # launching a second worker that could race on playlist_entries_data.
        if getattr(self, '_parse_running', False):
            self.stop_download()
            return

        if not getattr(self, '_is_from_bulk_parse_flag', False):
            self._is_from_bulk_parse = False
        else:
            self._is_from_bulk_parse = True
            self._is_from_bulk_parse_flag = False

        url = self.url_entry.get().strip()
        batch = self.get_batch_file_value()

        # If main URL is empty but batch has a URL, use it
        if not url and batch.startswith('http') and '\n' not in batch:
            url = batch
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
        elif not url:
            bulk_urls = self.get_bulk_urls()
            if bulk_urls:
                url = bulk_urls[0]
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, url)

        if not url:
            self.download_after_playlist_parse = False
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL.'))
            return

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)
        self.status_var.set(self.tr('Checking URL...'))
        parse_options = self.collect_parse_options()
        self._parse_generation += 1
        generation = self._parse_generation
        # The worker captures this generation. URL edits, Stop, and close all
        # increment it, making late results harmless without joining the thread.
        self._parse_cancel = False
        self._parse_running = True
        self._runner_kind = 'parse'
        self.root.after(0, self._set_parse_button_state, True, generation)
        thread = threading.Thread(
            target=self._parse_playlist_only,
            args=(url, parse_options, generation),
            daemon=True)
        thread.start()

    def _set_parse_button_state(self, parsing, generation=None):
        if self._closing or not hasattr(self, 'download_btn'):
            return
        if generation is not None and generation != self._parse_generation:
            return
        if parsing:
            self.download_btn.config(text=self.tr('Stop'), background='#dc3545', bg='#dc3545')
            self._translatable_widgets[self.download_btn] = 'Stop'
        else:
            self._restore_download_button()

    def _parse_playlist_only(self, url, parse_options=None, generation=None):
        parse_options = parse_options or {}
        generation = self._parse_generation if generation is None else generation
        try:
            if not self._parse_request_is_current(generation):
                return
            self.log_message(self.tr('Checking if URL is a playlist...'))
            # Keep preflight aligned with the downloader while making it cheap:
            # flat JSON avoids resolving every media format before the selector.
            cmd = [
                *core_launcher(),
                '-J', '--flat-playlist', '--no-cache-dir', '--ignore-no-formats-error',
                '--remote-components', 'ejs:github',
            ]

            lang_to_use, _metadata_lang_selected = self.get_metadata_language()

            self.log_message(self.translate_concat('[DEBUG] Parsing playlist metadata using interface-linked language: ', lang_to_use))
            # This is the crucial counterpart to build_command_args(): titles
            # displayed in the tree become selected-download filenames.
            cmd.extend(['--extractor-args', f'youtube:lang={lang_to_use}'])
            cmd.extend(['--add-header', f'Accept-Language:{lang_to_use},zh-CN;q=0.9,zh;q=0.8'])
            # Default geo-bypass for metadata unless user explicitly disabled it
            if not parse_options.get('no_geo_bypass') and not parse_options.get('geo_bypass'):
                cmd.append('--geo-bypass')

            # Align parse with download auth/network context (proxy, login, cookies, etc.)
            self.apply_parse_options_to_cmd(cmd, parse_options)
            cmd.append(url)

            # 设置环境变量，确保能找到 deno/node/ffmpeg
            env = self._subprocess_env()

            popen_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'env': env,
                **self._subprocess_text_kwargs(),
            }
            if os.name == 'nt':
                popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                popen_kwargs['start_new_session'] = True
            process = subprocess.Popen(cmd, **popen_kwargs)
            self._parse_process = process
            try:
                stdout, stderr = process.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                self._terminate_process(process)
                raise
            finally:
                if self._parse_process is process:
                    self._parse_process = None
            if not self._parse_request_is_current(generation):
                return
            if process.returncode == 0:
                info = json.loads(stdout)
                # Handle both playlists and single videos
                if info.get('_type') in ('playlist', 'multi_video') and 'entries' in info:
                    self.playlist_parsed_url = url
                    self.playlist_parse_is_real_playlist = True

                    entries = info['entries']
                    playlist_count = info.get('playlist_count')
                    requested_entries = info.get('requested_entries')

                    # Some extractors return only the first page. Fetch the rest
                    # in bounded ranges while keeping requested_entries aligned.
                    if playlist_count and len(entries) < playlist_count:
                        self.log_message(self.translate_concat(f'[DEBUG] Pagination detected. Total count: {playlist_count}, currently loaded: ', len(entries)))
                        if not requested_entries:
                            requested_entries = list(range(1, len(entries) + 1))

                        current_loaded = len(entries)
                        while current_loaded < playlist_count:
                            if not self._parse_request_is_current(generation):
                                return
                            start_idx = current_loaded + 1
                            end_idx = min(start_idx + 99, playlist_count)
                            range_str = f'{start_idx}-{end_idx}'

                            self.log_message(self.translate_concat('[DEBUG] Pagination: Fetching items ', f'{range_str}...'))

                            page_cmd = cmd.copy()
                            page_cmd.extend(['--playlist-items', range_str])

                            try:
                                page_popen_kwargs = {
                                    'stdout': subprocess.PIPE,
                                    'stderr': subprocess.PIPE,
                                    'env': env,
                                    **self._subprocess_text_kwargs(),
                                }
                                if os.name == 'nt':
                                    page_popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                                else:
                                    page_popen_kwargs['start_new_session'] = True
                                page_proc = subprocess.Popen(page_cmd, **page_popen_kwargs)
                                self._parse_process = page_proc
                                try:
                                    page_stdout, page_stderr = page_proc.communicate(timeout=120)
                                except subprocess.TimeoutExpired:
                                    self._terminate_process(page_proc)
                                    raise
                                finally:
                                    if self._parse_process is page_proc:
                                        self._parse_process = None
                                if not self._parse_request_is_current(generation):
                                    return
                                if page_proc.returncode == 0:
                                    page_info = json.loads(page_stdout)
                                    page_entries = page_info.get('entries') or []
                                    if not page_entries:
                                        # If no entries returned, break to avoid infinite loop
                                        break

                                    entries.extend(page_entries)
                                    page_req = page_info.get('requested_entries')
                                    if page_req:
                                        requested_entries.extend(page_req)
                                    else:
                                        requested_entries.extend(list(range(start_idx, start_idx + len(page_entries))))

                                    current_loaded += len(page_entries)
                                else:
                                    self.log_message(self.translate_concat(f'[DEBUG] Pagination failed for range {range_str}: ', page_stderr.strip()))
                                    break
                            except subprocess.TimeoutExpired:
                                self.log_message(self.tr('Playlist page parsing timed out.'))
                                break
                            except Exception as pe:
                                self.log_message(self.translate_concat(f'[DEBUG] Pagination exception for range {range_str}: ', str(pe)))
                                break

                    self.playlist_entries_data = entries
                    self.playlist_count = playlist_count or len(entries)
                    self.playlist_requested_entries = requested_entries
                    self.current_playlist_metadata_title = info.get('title', 'Playlist')
                    if not self._parse_request_is_current(generation):
                        return
                    self._parse_running = False
                    self._runner_kind = None
                    self.root.after(0, self._set_parse_button_state, False, generation)
                    self.root.after(0, self._show_playlist_tab, self.current_playlist_metadata_title, generation)
                    return
                elif info.get('_type') == 'video' or (info.get('_type') == 'url' and info.get('ie_key') == 'Youtube'):
                    # Single video detected - treat it as a playlist with one entry
                    self.playlist_parsed_url = url
                    self.playlist_parse_is_real_playlist = False
                    video_info = {
                        '_type': 'video',
                        'id': info.get('id', ''),
                        'title': info.get('title', 'Video'),
                        'url': info.get('url') or info.get('webpage_url', url),
                        'ie_key': info.get('extractor_key', 'Youtube'),
                    }
                    self.playlist_entries_data = [video_info]
                    self.playlist_count = 1
                    self.playlist_requested_entries = [1]
                    self.current_playlist_metadata_title = info.get('title', 'Single Video')
                    if not self._parse_request_is_current(generation):
                        return
                    self._parse_running = False
                    self._runner_kind = None
                    self.root.after(0, self._set_parse_button_state, False, generation)
                    self.root.after(0, self._show_playlist_tab, self.current_playlist_metadata_title, generation)
                    return
                else:
                    self.log_message(self.tr('Not a playlist or no entries found.'))
            else:
                self.log_message(f'[ERROR] Parsing failed: {stderr.strip()}')
                self.log_message(self.tr('Failed to parse playlist.'))
                if generation == self._parse_generation:
                    self.download_after_playlist_parse = False
        except subprocess.TimeoutExpired:
            self.log_message(self.tr('Playlist parsing timed out.'))
            if generation == self._parse_generation:
                self._parse_cancel = True
                self.download_after_playlist_parse = False
        except Exception as e:
            self.log_message(self.translate_concat('Error checking playlist: ', str(e)))
            if generation == self._parse_generation:
                self.download_after_playlist_parse = False
        finally:
            if not self._closing and generation == self._parse_generation:
                self._parse_running = False
                self._runner_kind = None
                self.root.after(0, self._set_parse_button_state, False, generation)
                self.root.after(0, lambda: self.status_var.set(self.tr('Ready')))

    def _show_playlist_tab(self, temp_title, generation=None):
        if generation is not None and not self._parse_request_is_current(generation):
            return
        self.log_message(self.tr('Playlist detected. Please select videos to download.'))
        self.status_var.set(self.tr('Playlist detected'))
        if hasattr(self, 'playlist_tree'):
            self.notebook.select(self.playlist_tab_frame)
            self.playlist_tree.delete(*self.playlist_tree.get_children())

            entries = self.playlist_entries_data
            total_entries = getattr(self, 'playlist_count', None) or len(entries)
            req_entries = getattr(self, 'playlist_requested_entries', None)

            filtered_entries = []
            for i, entry in enumerate(entries):
                if not entry:
                    continue
                title = entry.get('title') or entry.get('id') or f'Video {i + 1}'
                availability = entry.get('availability', '')
                raw_title = entry.get('title')
                is_private = (
                    raw_title in (
                        '[Private video]', '[私享视频]', '[私有视频]',
                        '[Deleted video]', '[已删除的视频]',
                    )
                    or availability == 'private'
                )
                if is_private and self.playlist_exclude_private_var.get():
                    continue

                # Get absolute original 1-based index from requested_entries if available
                if req_entries and i < len(req_entries):
                    original_idx = req_entries[i]
                else:
                    original_idx = i + 1

                # Always use reverse (newest-first) display numbers as the stable # column /
                # filename prefix. When the playlist grows at the front, older videos keep
                # the same reverse index (total - original + 1) so re-sync does not rename them.
                # Reverse-order checkbox only reverses row order in the tree, not the numbering.
                display_idx = total_entries - original_idx + 1
                filtered_entries.append((display_idx, original_idx, title))

            if getattr(self, 'playlist_reverse_var', None) and self.playlist_reverse_var.get():
                filtered_entries = list(reversed(filtered_entries))

            self.vis_to_orig = {}
            for display_idx, original_idx, title in filtered_entries:
                # Map the number shown in the # column back to the original playlist index
                self.vis_to_orig[display_idx] = original_idx
                status_char = '☐' if getattr(self, '_is_from_bulk_parse', False) else '☑'
                self.playlist_tree.insert('', tk.END, values=(status_char, display_idx, title))

            # Reset headers
            self.playlist_tree.heading('status', text=' ')
            self.playlist_tree.heading('index', text='#')
            self.playlist_tree.heading('title', text=self.tr('Title'))

            if getattr(self, 'download_after_playlist_parse', False):
                self.download_after_playlist_parse = False
                self.root.after(
                    100,
                    lambda g=generation: self.start_download()
                    if g is None or self._parse_request_is_current(g) else None)

    def _begin_inspect_job(self, task_name, args):
        """Run a non-download yt-dlp job (formats/info) with Stop support but no partial cleanup."""
        def _to_stop():
            if hasattr(self, 'download_btn'):
                self.download_btn.config(text=self.tr('Stop'), background='#dc3545', bg='#dc3545')
                self.download_btn.update()
        self.root.after(10, _to_stop)
        if hasattr(self, 'download_btn'):
            self._translatable_widgets[self.download_btn] = 'Stop'
        self._download_cancel = False
        self._runner_kind = 'inspect'
        self._download_running = True
        thread = threading.Thread(target=self.run_ytdlp, args=([(task_name, args)],), daemon=True)
        thread.start()

    def list_formats(self):
        """List available formats for the video"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL.'))
            return
        if (getattr(self, '_download_running', False)
                or getattr(self, 'current_process', None)
                or getattr(self, '_parse_running', False)
                or getattr(self, '_parse_all_running', False)):
            messagebox.showwarning(self.tr('Busy'), self.tr('A download is already running.'))
            return

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)
        self._begin_inspect_job('Formats', ['-F', url])

    def extract_info(self):
        """Extract video information"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning(self.tr('No URL'), self.tr('Please enter a URL.'))
            return
        if (getattr(self, '_download_running', False)
                or getattr(self, 'current_process', None)
                or getattr(self, '_parse_running', False)
                or getattr(self, '_parse_all_running', False)):
            messagebox.showwarning(self.tr('Busy'), self.tr('A download is already running.'))
            return

        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)
        self._begin_inspect_job('Info', ['--dump-json', url])

    def _start_log_watcher(self):
        """Poll the log queue and update the UI from the main thread"""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._log_message_internal(msg)
        except Exception:  # queue.Empty
            pass
        self.root.after(100, self._start_log_watcher)

    def _log_message_internal(self, message):
        """Internal method to update the console text widget and redirect progress to status bar"""
        clean_msg = message.strip()

        if clean_msg.startswith('[download] Destination:'):
            filename = clean_msg.split(':', 1)[1].strip()
            self.root.title(f'{self.tr(self.base_title)} - {os.path.basename(filename)}')
        elif 'has already been downloaded' in clean_msg and clean_msg.startswith('[download]'):
            filename = clean_msg.replace('[download]', '').split('has already been downloaded')[0].strip()
            self.root.title(f'{self.tr(self.base_title)} - {os.path.basename(filename)}')

        # Redirect [download] progress to the status bar instead of the console
        # Typically looks like: [download]  1.2% of 10.00MiB at ...
        if clean_msg.startswith('[download]') and '%' in clean_msg:
            # Strip '[download]' prefix for a cleaner look as requested
            display_msg = clean_msg.replace('[download]', '').strip()
            now = time.monotonic()
            force_update = '100%' in clean_msg
            if not force_update and now - self._last_progress_update < 0.35:
                return
            self._last_progress_update = now
            self.progress_var.set(display_msg)
            # Clear progress bar once finished or moved to next stage
            if force_update:
                self.root.after(3000, lambda: self.progress_var.set('') if '100%' in self.progress_var.get() else None)
            return

        self.console.config(state=tk.NORMAL)
        # Check if we were already at the bottom before adding content
        at_bottom = self.console.yview()[1] == 1.0
        self.console.insert(tk.END, message + '\n')
        if at_bottom:
            self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)

    def log_message(self, message):
        """Add message to the thread-safe queue and stdout for debugging."""
        msg_str = str(message)
        is_progress = msg_str.startswith('[download]') and '%' in msg_str
        if is_progress:
            now = time.monotonic()
            if '100%' not in msg_str and now - self._last_progress_enqueue < 0.15:
                return
            self._last_progress_enqueue = now
        # Avoid mirroring every high-frequency progress tick to terminal/log files.
        if not is_progress:
            print(msg_str)

        if hasattr(self, 'log_queue'):
            self.log_queue.put(msg_str)

    def load_config(self):
        """Load configuration from file"""
        self.config = load_config_file(self.config_file)

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
        """Get current configuration from GUI without force-building every lazy tab.

        Built widgets win over pending values; unbuilt tabs keep their last pending
        snapshot so autosave does not materialize the whole notebook.
        """
        # Start from pending (covers unbuilt tabs), then overlay live controls
        gui_state = {
            key: value for key, value in self._pending_gui_state.items()
            if key not in _SECRET_CONFIG_KEYS
        }

        for name, widget in self._stateful_controls.items():
            if name in {'language_selector', 'console', 'generated_cmd'}:
                continue
            if name in _SECRET_CONFIG_KEYS:
                continue
            if isinstance(widget, tk.BooleanVar):
                gui_state[name] = bool(widget.get())
            elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                gui_state[name] = widget.get()
            elif isinstance(widget, scrolledtext.ScrolledText):
                gui_state[name] = widget.get('1.0', tk.END).rstrip('\n')

        # Prefer live bulk_rows; only fall back to pending when Batch tab not built yet
        bulk_list = getattr(self, 'bulk_rows', None)
        if bulk_list is not None and (
            hasattr(self, 'batch_tab_frame') and self.batch_tab_frame in self._built_tabs
        ):
            bulk_urls = []
            bulk_playlists = []
            for row in bulk_list:
                url = row['var'].get().strip()
                if url:
                    bulk_urls.append(url)
                    bulk_playlists.append(
                        row.get('playlist_var').get().strip() if 'playlist_var' in row else '')
            gui_state['bulk_urls'] = bulk_urls
            gui_state['bulk_playlists'] = bulk_playlists
        elif 'bulk_urls' not in gui_state:
            gui_state['bulk_urls'] = []
            gui_state['bulk_playlists'] = []

        # Persist raw language preference (including 'auto'), not only the resolved session language.
        language_pref = self.config.get('language', self.current_language)
        if language_pref not in LANGUAGE_OPTIONS:
            language_pref = self.current_language

        return {
            'config_version': 1,
            'language': language_pref,
            'language_initialized': True,
            'gui_state': gui_state,
        }

    def apply_config(self):
        """Apply loaded configuration to GUI"""
        language = self.config.get('language', self.current_language)
        if language not in LANGUAGE_OPTIONS:
            language = 'en'
        # Resolve 'auto' to a real locale for the session while keeping the preference for the selector
        if language == 'auto':
            self.current_language = self.detect_system_language()
        else:
            self.current_language = language
        gui_state = dict(self.config.get('gui_state', {}))
        # Strip any secrets that may exist in older config files
        for secret_key in _SECRET_CONFIG_KEYS:
            gui_state.pop(secret_key, None)
        # Migrate removed dual-control keys into the surviving Network-tab fields
        if gui_state.get('limit_rate') and not gui_state.get('rate_limit'):
            gui_state['rate_limit'] = gui_state['limit_rate']
        gui_state.pop('limit_rate', None)
        if gui_state.get('sleep_requests') and not gui_state.get('sleep_interval_requests'):
            gui_state['sleep_interval_requests'] = gui_state['sleep_requests']
        gui_state.pop('sleep_requests', None)
        # Discard modes are not CLI-mappable; coerce to supported value
        if gui_state.get('extract_flat') in ('discard', 'discard_in_playlist'):
            gui_state['extract_flat'] = 'in_playlist'
        # Drop dead legacy vars if present
        gui_state.pop('exclude_private', None)
        gui_state.pop('reverse_order', None)
        for key, value in GUI_DEFAULT_STATE.items():
            if key not in gui_state:
                gui_state[key] = value
        self._pending_gui_state = gui_state
        if hasattr(self, 'language_var'):
            self.language_var.set(self.get_language_display(language))
        self.apply_localization()
        self.apply_pending_gui_state()
        self.status_var.set(self.tr('Ready'))


def main():
    """Main entry point for the GUI"""
    try:
        root = tk.Tk()
        # Set theme and window style for macOS
        style = ttk.Style(root)
        if sys.platform == 'darwin':
            style.theme_use('aqua')

        _app = YtDlpGUI(root)
        root.mainloop()
    except Exception:
        import traceback
        print(f'FATAL ERROR during GUI startup:\n{traceback.format_exc()}')


if __name__ == '__main__':
    main()
