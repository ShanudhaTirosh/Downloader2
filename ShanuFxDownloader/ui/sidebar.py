"""
Shanu Fx Private Downloader - Sidebar Navigation
Modern sidebar with icon + label nav items, active state, and logo.
Author: Shanudha Tirosh
"""

import tkinter as tk
from typing import Callable

import customtkinter as ctk

from core.config import COLORS, FONTS, SIDEBAR_WIDTH, APP_NAME, APP_VERSION

# ─── Nav Items Definition ──────────────────────────────────────────────────────

NAV_ITEMS = [
    ("home",       "⌂",  "Home"),
    ("downloader", "⬇",  "Downloader"),
    ("manager",    "⚡",  "DL Manager"),
    ("history",    "🕘",  "History"),
    ("torrent",    "⊕",  "Torrents"),
    ("settings",   "⚙",  "Settings"),
    ("about",      "◉",  "About"),
]


# ─── Nav Button ───────────────────────────────────────────────────────────────

class NavButton(ctk.CTkFrame):
    """Single sidebar navigation item with hover and active effects."""

    HEIGHT = 48

    def __init__(self, parent, icon: str, label: str, page_key: str,
                 navigate_cb: Callable, **kwargs):
        super().__init__(
            parent,
            height=self.HEIGHT,
            fg_color="transparent",
            corner_radius=12,
            cursor="hand2",
            **kwargs,
        )
        self.page_key    = page_key
        self.navigate_cb = navigate_cb
        self._active     = False

        self.grid_propagate(False)
        self.pack_propagate(False)

        # ── Icon ─────────────────────────────────────────────────────────────
        self._icon_lbl = ctk.CTkLabel(
            self, text=icon,
            font=("Segoe UI", 16),
            text_color=COLORS["text_secondary"],
            width=36, anchor="center",
        )
        self._icon_lbl.place(x=14, y=13)

        # ── Label ────────────────────────────────────────────────────────────
        self._label_lbl = ctk.CTkLabel(
            self, text=label,
            font=FONTS["body_md"],
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self._label_lbl.place(x=52, y=15)

        # ── Active indicator bar ──────────────────────────────────────────────
        self._bar = ctk.CTkFrame(
            self, width=3, height=26, corner_radius=2,
            fg_color=COLORS["accent"],
        )
        # Hidden by default

        # ── Bindings ─────────────────────────────────────────────────────────
        for w in (self, self._icon_lbl, self._label_lbl):
            w.bind("<Enter>",  self._on_enter)
            w.bind("<Leave>",  self._on_leave)
            w.bind("<Button-1>", self._on_click)

    def _on_enter(self, _e=None):
        if not self._active:
            self.configure(fg_color=COLORS["sidebar_hover"])

    def _on_leave(self, _e=None):
        if not self._active:
            self.configure(fg_color="transparent")

    def _on_click(self, _e=None):
        self.navigate_cb(self.page_key)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(fg_color=COLORS["sidebar_active"])
            self._icon_lbl.configure(text_color=COLORS["accent_light"])
            self._label_lbl.configure(
                text_color=COLORS["text_primary"],
                font=FONTS["heading_sm"],
            )
            self._bar.place(x=SIDEBAR_WIDTH - 6, y=11)
        else:
            self.configure(fg_color="transparent")
            self._icon_lbl.configure(text_color=COLORS["text_secondary"])
            self._label_lbl.configure(
                text_color=COLORS["text_secondary"],
                font=FONTS["body_md"],
            )
            self._bar.place_forget()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

class Sidebar(ctk.CTkFrame):
    """
    Left sidebar with logo, navigation, and bottom status strip.
    Width is fixed; height fills the window.
    """

    def __init__(self, parent, navigate_cb: Callable, **kwargs):
        super().__init__(
            parent,
            width=SIDEBAR_WIDTH,
            fg_color=COLORS["sidebar_bg"],
            corner_radius=0,
            **kwargs,
        )
        self.grid_propagate(False)
        self.pack_propagate(False)
        self._buttons: dict[str, NavButton] = {}
        self._navigate_cb = navigate_cb

        self._build()

    def _build(self):
        # ── Logo section ──────────────────────────────────────────────────────
        logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", padx=0, pady=0)
        logo_frame.pack_propagate(False)

        # Gradient accent line at top
        accent_bar = ctk.CTkFrame(self, height=2, fg_color=COLORS["accent"], corner_radius=0)
        accent_bar.pack(fill="x", side="top")

        # App icon placeholder (unicode symbol)
        ctk.CTkLabel(
            logo_frame, text="⬡",
            font=("Segoe UI", 28, "bold"),
            text_color=COLORS["accent"],
        ).place(x=16, y=16)

        ctk.CTkLabel(
            logo_frame, text="Shanu Fx",
            font=FONTS["heading_md"],
            text_color=COLORS["text_primary"],
        ).place(x=54, y=18)

        ctk.CTkLabel(
            logo_frame, text="Private Downloader",
            font=FONTS["caption"],
            text_color=COLORS["text_muted"],
        ).place(x=54, y=40)

        # ── Separator ────────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=(0, 8))

        # ── Navigation items ──────────────────────────────────────────────────
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.pack(fill="x", padx=10, pady=4)

        for page_key, icon, label in NAV_ITEMS:
            btn = NavButton(
                nav_container,
                icon=icon,
                label=label,
                page_key=page_key,
                navigate_cb=self._navigate_cb,
            )
            btn.pack(fill="x", pady=3)
            self._buttons[page_key] = btn

        # ── Separator ────────────────────────────────────────────────────────
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(
            fill="x", pady=(8, 0), padx=0, side="bottom"
        )

        # ── Bottom status strip ───────────────────────────────────────────────
        bottom = ctk.CTkFrame(self, fg_color="transparent", height=52)
        bottom.pack(fill="x", padx=12, pady=8, side="bottom")
        bottom.pack_propagate(False)

        # Version badge
        version_badge = ctk.CTkFrame(
            bottom, fg_color=COLORS["bg_elevated"],
            corner_radius=8, height=32,
        )
        version_badge.pack(fill="x")
        version_badge.pack_propagate(False)

        ctk.CTkLabel(
            version_badge,
            text=f"v{APP_VERSION}  •  by Shanudha Tirosh",
            font=FONTS["caption"],
            text_color=COLORS["text_muted"],
        ).pack(expand=True)

    def set_active(self, page_key: str):
        """Set the active state for the given page key."""
        for key, btn in self._buttons.items():
            btn.set_active(key == page_key)
