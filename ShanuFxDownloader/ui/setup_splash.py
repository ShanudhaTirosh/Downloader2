"""
Shanu Fx Private Downloader - Setup Splash Screen
Shown on first run while system components are being installed.
Author: Shanudha Tirosh
"""

import threading
import tkinter as tk

import customtkinter as ctk

from core.config import COLORS, FONTS, APP_NAME, APP_VERSION
from core.setup import setup_manager


class SetupSplash(ctk.CTkToplevel):
    """
    Full-window splash screen displayed during first-run setup.
    Shows progress, status messages, and a log of install steps.
    Calls `on_complete` when setup finishes.
    """

    def __init__(self, parent, on_complete: callable):
        super().__init__(parent)
        self._on_complete = on_complete
        self._log_lines   = []

        # ── Window Setup ─────────────────────────────────────────────────────
        self.title(f"{APP_NAME} — Setup")
        self.geometry("520x440")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_primary"])
        self.grab_set()
        self.lift()
        self.focus_force()

        # Center
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"520x440+{(sw-520)//2}+{(sh-440)//2}")

        self._build()
        self._start_setup()

    def _build(self):
        # Logo + Title
        logo_row = ctk.CTkFrame(self, fg_color="transparent")
        logo_row.pack(pady=(40, 0))

        ctk.CTkLabel(logo_row, text="⬡", font=("Segoe UI", 52, "bold"),
                     text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(self, text=APP_NAME, font=FONTS["heading_lg"],
                     text_color=COLORS["text_primary"]).pack(pady=(8, 0))
        ctk.CTkLabel(self, text=f"v{APP_VERSION}  ·  First Run Setup",
                     font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack()

        # Status label
        self._status_lbl = ctk.CTkLabel(
            self, text="Preparing system components…",
            font=FONTS["body_md"], text_color=COLORS["accent_light"],
        )
        self._status_lbl.pack(pady=(28, 8))

        # Progress bar
        self._pb = ctk.CTkProgressBar(
            self, width=400, height=8, corner_radius=4,
            fg_color=COLORS["bg_elevated"], progress_color=COLORS["accent"],
        )
        self._pb.pack()
        self._pb.set(0)

        # Percentage
        self._pct_lbl = ctk.CTkLabel(self, text="0%", font=FONTS["heading_sm"],
                                      text_color=COLORS["accent"])
        self._pct_lbl.pack(pady=(6, 0))

        # Log box
        log_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_elevated"],
                                  corner_radius=10, width=440, height=120)
        log_frame.pack(pady=(20, 0))
        log_frame.pack_propagate(False)

        self._log_text = ctk.CTkTextbox(
            log_frame, width=430, height=115,
            font=FONTS["mono"], fg_color="transparent",
            text_color=COLORS["text_secondary"],
            wrap="word",
        )
        self._log_text.pack(fill="both", expand=True, padx=4, pady=4)
        self._log_text.configure(state="disabled")

        # Footer note
        ctk.CTkLabel(
            self,
            text="This only happens once. FFmpeg and yt-dlp will be installed automatically.",
            font=FONTS["caption"], text_color=COLORS["text_muted"],
        ).pack(pady=(12, 0))

    def _start_setup(self):
        setup_manager.on_progress(
            lambda v: self.after(0, lambda: self._update_progress(v))
        )
        setup_manager.on_status(
            lambda s: self.after(0, lambda: self._update_status(s))
        )
        setup_manager.on_complete(
            lambda: self.after(0, self._finish)
        )
        setup_manager.on_error(
            lambda e: self.after(0, lambda: self._show_error(e))
        )
        setup_manager.run_setup()

    def _update_progress(self, value: float):
        self._pb.set(value)
        self._pct_lbl.configure(text=f"{int(value * 100)}%")

    def _update_status(self, msg: str):
        self._status_lbl.configure(text=msg)
        self._log_lines.append(msg)
        self._log_text.configure(state="normal")
        self._log_text.insert("end", f"{msg}\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _finish(self):
        self._update_status("✓ Setup complete!")
        self._pb.set(1.0)
        self._pct_lbl.configure(text="100%", text_color=COLORS["accent_green"])
        self.after(1200, lambda: [self.destroy(), self._on_complete()])

    def _show_error(self, err: str):
        self._status_lbl.configure(text=f"⚠ {err}", text_color=COLORS["accent_orange"])
        self._update_status(f"Warning: {err}")
        self._update_status("Continuing with available components…")
        # Don't block launch on setup errors
        self.after(2500, lambda: [self.destroy(), self._on_complete()])
