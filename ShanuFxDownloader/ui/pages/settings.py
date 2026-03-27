"""
Shanu Fx Private Downloader - Settings Page
All user-configurable preferences.
Author: Shanudha Tirosh
"""

import os
from typing import TYPE_CHECKING

import customtkinter as ctk

from core.config import COLORS, FONTS, config, VIDEO_QUALITIES, AUDIO_BITRATES

if TYPE_CHECKING:
    from ui.app import App

# ─── Settings Section ─────────────────────────────────────────────────────────

class SettingsSection(ctk.CTkFrame):
    """A labeled section card containing related settings."""

    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=16,
                         border_width=1, border_color=COLORS["border"], **kwargs)

        ctk.CTkLabel(self, text=title, font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=20, pady=(14, 4))
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=0)

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="x", padx=20, pady=(8, 16))

    @property
    def content(self):
        return self._content


class SettingRow(ctk.CTkFrame):
    """A single setting with label + control on the same row."""

    def __init__(self, parent, label: str, description: str = "", **kwargs):
        super().__init__(parent, fg_color="transparent", height=52, **kwargs)
        self.pack_propagate(False)

        text_col = ctk.CTkFrame(self, fg_color="transparent")
        text_col.place(x=0, y=4)

        ctk.CTkLabel(text_col, text=label, font=FONTS["body_md"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        if description:
            ctk.CTkLabel(text_col, text=description, font=FONTS["caption"],
                         text_color=COLORS["text_muted"]).pack(anchor="w")

    def add_control(self, widget):
        """Place control on the right side of the row."""
        widget.place(relx=1.0, rely=0.5, anchor="e", x=0)


# ─── Settings Page ────────────────────────────────────────────────────────────

class SettingsPage(ctk.CTkFrame):
    """Application settings page."""

    def __init__(self, parent, app: "App", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0, **kwargs)
        self._app = app
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(24, 4))
        ctk.CTkLabel(hdr, text="Settings", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(hdr, text="Configure your downloader preferences",
                     font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(anchor="w")

        # ── Section 1: Download Folder ────────────────────────────────────────
        s1 = SettingsSection(scroll, "Download Location")
        s1.pack(fill="x", padx=30, pady=(20, 0))

        dir_row = ctk.CTkFrame(s1.content, fg_color="transparent")
        dir_row.pack(fill="x", pady=4)

        self._dir_entry = ctk.CTkEntry(
            dir_row, width=380, height=38,
            font=FONTS["body_sm"],
            fg_color=COLORS["bg_elevated"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self._dir_entry.insert(0, config.get("download_dir", ""))
        self._dir_entry.pack(side="left")

        ctk.CTkButton(
            dir_row, text="Browse", width=90, height=38,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["body_sm"], command=self._browse_dir,
        ).pack(side="left", padx=(8, 0))

        # ── Section 2: Format Defaults ────────────────────────────────────────
        s2 = SettingsSection(scroll, "Format Preferences")
        s2.pack(fill="x", padx=30, pady=(14, 0))

        row1 = ctk.CTkFrame(s2.content, fg_color="transparent")
        row1.pack(fill="x", pady=6)
        row1.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(row1, text="Default Format", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=0, sticky="w")
        self._fmt_var = ctk.StringVar(value=config.get("default_format", "mp4").upper())
        ctk.CTkOptionMenu(
            row1, variable=self._fmt_var,
            values=["MP4", "MP3", "WEBM", "M4A"],
            fg_color=COLORS["bg_elevated"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_elevated"],
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
        ).grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(4, 0))

        ctk.CTkLabel(row1, text="Default Quality", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=1, sticky="w")
        self._qual_var = ctk.StringVar(value=config.get("default_quality", "best").title())
        ctk.CTkOptionMenu(
            row1, variable=self._qual_var,
            values=[q.title() for q in VIDEO_QUALITIES],
            fg_color=COLORS["bg_elevated"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_elevated"],
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
        ).grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(4, 0))

        ctk.CTkLabel(row1, text="Audio Bitrate", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=2, sticky="w")
        self._br_var = ctk.StringVar(value=config.get("default_bitrate", "192kbps"))
        ctk.CTkOptionMenu(
            row1, variable=self._br_var,
            values=AUDIO_BITRATES,
            fg_color=COLORS["bg_elevated"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_elevated"],
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
        ).grid(row=1, column=2, sticky="ew", pady=(4, 0))

        # ── Section 3: Download Manager ───────────────────────────────────────
        s3 = SettingsSection(scroll, "Download Manager")
        s3.pack(fill="x", padx=30, pady=(14, 0))

        threads_row = ctk.CTkFrame(s3.content, fg_color="transparent")
        threads_row.pack(fill="x", pady=6)

        ctk.CTkLabel(threads_row, text="Max Download Threads:",
                     font=FONTS["body_md"], text_color=COLORS["text_primary"]).pack(side="left")

        self._threads_var = ctk.IntVar(value=config.get("max_threads", 8))
        threads_label = ctk.CTkLabel(threads_row, text=str(self._threads_var.get()),
                                      font=FONTS["heading_sm"], text_color=COLORS["accent"],
                                      width=30)
        threads_label.pack(side="right")

        def on_slider(val):
            v = int(val)
            self._threads_var.set(v)
            threads_label.configure(text=str(v))

        ctk.CTkSlider(
            threads_row, from_=1, to=32, number_of_steps=31,
            variable=self._threads_var,
            fg_color=COLORS["bg_elevated"], progress_color=COLORS["accent"],
            button_color=COLORS["accent_light"],
            command=on_slider, width=200,
        ).pack(side="right", padx=(0, 8))

        # Speed limit
        speed_row = ctk.CTkFrame(s3.content, fg_color="transparent")
        speed_row.pack(fill="x", pady=4)

        ctk.CTkLabel(speed_row, text="Speed Limit (0 = unlimited):",
                     font=FONTS["body_md"], text_color=COLORS["text_primary"]).pack(side="left")

        self._speed_entry = ctk.CTkEntry(
            speed_row, width=100, height=32,
            font=FONTS["body_sm"], fg_color=COLORS["bg_elevated"],
            border_color=COLORS["border"], text_color=COLORS["text_primary"],
        )
        self._speed_entry.insert(0, str(config.get("speed_limit_kbps", 0)))
        self._speed_entry.pack(side="right")
        ctk.CTkLabel(speed_row, text="KB/s", font=FONTS["body_sm"],
                     text_color=COLORS["text_muted"]).pack(side="right", padx=(0, 4))

        # ── Section 4: Behavior ───────────────────────────────────────────────
        s4 = SettingsSection(scroll, "Behavior")
        s4.pack(fill="x", padx=30, pady=(14, 0))

        self._clipboard_var   = ctk.BooleanVar(value=config.get("clipboard_detection", True))
        self._notif_var       = ctk.BooleanVar(value=config.get("show_notifications", True))
        self._auto_start_var  = ctk.BooleanVar(value=config.get("auto_start_download", False))

        toggle_items = [
            (self._clipboard_var,  "Clipboard Detection",
             "Auto-detect URLs copied to clipboard"),
            (self._notif_var,      "Show Notifications",
             "Display toast notifications on download events"),
            (self._auto_start_var, "Auto-Start Downloads",
             "Start downloading immediately without confirmation"),
        ]

        for var, label, desc in toggle_items:
            row = ctk.CTkFrame(s4.content, fg_color="transparent")
            row.pack(fill="x", pady=4)

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left")
            ctk.CTkLabel(text_col, text=label, font=FONTS["body_md"],
                         text_color=COLORS["text_primary"]).pack(anchor="w")
            ctk.CTkLabel(text_col, text=desc, font=FONTS["caption"],
                         text_color=COLORS["text_muted"]).pack(anchor="w")

            ctk.CTkSwitch(
                row, variable=var, text="",
                progress_color=COLORS["accent"],
                button_color=COLORS["accent_light"],
            ).pack(side="right")

        # ── Save Button ───────────────────────────────────────────────────────
        save_row = ctk.CTkFrame(scroll, fg_color="transparent")
        save_row.pack(fill="x", padx=30, pady=(20, 30))

        ctk.CTkButton(
            save_row, text="✓  Save Settings", height=48, width=200,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["heading_sm"], command=self._save,
        ).pack(side="left")

        ctk.CTkButton(
            save_row, text="Reset Defaults", height=48, width=150,
            fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"],
            font=FONTS["body_md"], text_color=COLORS["text_secondary"],
            command=self._reset_defaults,
        ).pack(side="left", padx=(12, 0))

        # ── Status label ──────────────────────────────────────────────────────
        self._save_lbl = ctk.CTkLabel(
            save_row, text="", font=FONTS["body_sm"],
            text_color=COLORS["accent_green"],
        )
        self._save_lbl.pack(side="left", padx=(12, 0))

    def _browse_dir(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Choose Download Folder")
        if folder:
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, folder)

    def _save(self):
        config.set("download_dir",        self._dir_entry.get().strip())
        config.set("default_format",      self._fmt_var.get().lower())
        config.set("default_quality",     self._qual_var.get().lower())
        config.set("default_bitrate",     self._br_var.get())
        config.set("max_threads",         self._threads_var.get())
        config.set("clipboard_detection", self._clipboard_var.get())
        config.set("show_notifications",  self._notif_var.get())
        config.set("auto_start_download", self._auto_start_var.get())
        try:
            config.set("speed_limit_kbps", int(self._speed_entry.get()))
        except Exception:
            config.set("speed_limit_kbps", 0)

        self._save_lbl.configure(text="✓ Settings saved!")
        self.after(2500, lambda: self._save_lbl.configure(text=""))

        from utils.notifications import notifications
        notifications.success("All settings saved", "Settings")

    def _reset_defaults(self):
        from core.config import DEFAULT_CONFIG
        self._dir_entry.delete(0, "end")
        self._dir_entry.insert(0, DEFAULT_CONFIG["download_dir"])
        self._fmt_var.set(DEFAULT_CONFIG["default_format"].upper())
        self._qual_var.set(DEFAULT_CONFIG["default_quality"].title())
        self._br_var.set(DEFAULT_CONFIG["default_bitrate"])
        self._threads_var.set(DEFAULT_CONFIG["max_threads"])
        self._clipboard_var.set(DEFAULT_CONFIG["clipboard_detection"])
        self._notif_var.set(DEFAULT_CONFIG["show_notifications"])
        self._auto_start_var.set(DEFAULT_CONFIG["auto_start_download"])
        self._speed_entry.delete(0, "end")
        self._speed_entry.insert(0, "0")
