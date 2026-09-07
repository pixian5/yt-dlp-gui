"""Tab: authentication"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any

import tkinter as tk
from tkinter import ttk

if TYPE_CHECKING:
    pass


class AuthenticationTabMixin:
    """Mixin for authentication tab. Requires YtDlpGUI base class."""

    # Type hints for mixin attributes (provided by YtDlpGUI)
    if TYPE_CHECKING:
        notebook: Any
        tr: Any
        register_translatable_widget: Any
        trigger_autosave: Any
        register_stateful_controls: Any
        browse_client_cert: Any
        browse_client_key: Any
        username: Any
        password: Any
        twofactor: Any
        netrc: Any
        video_password: Any
        ap_mso: Any
        ap_username: Any
        ap_password: Any
        client_certificate: Any
        client_certificate_key: Any
        client_certificate_password: Any
        _stateful_controls: Any

    def create_authentication_tab(self, frame=None):
        """Create Authentication Options tab"""
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

        ttk.Label(scrollable_frame, text='Username:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.username = ttk.Entry(scrollable_frame, width=30)
        self.username.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.password = ttk.Entry(scrollable_frame, width=30, show='*')
        self.password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Two-factor code:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.twofactor = ttk.Entry(scrollable_frame, width=20)
        self.twofactor.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        self.netrc = tk.BooleanVar()
        ttk.Checkbutton(scrollable_frame, text='Use .netrc authentication (--netrc)',
                        variable=self.netrc).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Video password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.video_password = ttk.Entry(scrollable_frame, width=30, show='*')
        self.video_password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Adobe Pass MSO:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.ap_mso = ttk.Entry(scrollable_frame, width=30)
        self.ap_mso.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Adobe Pass username:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.ap_username = ttk.Entry(scrollable_frame, width=30)
        self.ap_username.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Adobe Pass password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.ap_password = ttk.Entry(scrollable_frame, width=30, show='*')
        self.ap_password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text='Client certificate:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        cert_frame = ttk.Frame(scrollable_frame)
        cert_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        self.client_certificate = ttk.Entry(cert_frame, width=40)
        self.client_certificate.pack(side=tk.LEFT)
        ttk.Button(cert_frame, text='Browse...', command=self.browse_client_cert).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        ttk.Label(scrollable_frame, text='Client certificate key:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        key_frame = ttk.Frame(scrollable_frame)
        key_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        self.client_certificate_key = ttk.Entry(key_frame, width=40)
        self.client_certificate_key.pack(side=tk.LEFT)
        ttk.Button(key_frame, text='Browse...', command=self.browse_client_key).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        ttk.Label(scrollable_frame, text='Client certificate password:').grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.client_certificate_password = ttk.Entry(scrollable_frame, width=30, show='*')
        self.client_certificate_password.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1
