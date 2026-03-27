"""
Shanu Fx Private Downloader - Home Page
Dashboard with stats, quick actions, and recent activity.
Author: Shanudha Tirosh
"""

import time
import threading
import tkinter as tk
from typing import TYPE_CHECKING

import customtkinter as ctk

from core.config import COLORS, FONTS
from downloader.history import history_manager
from manager.download_manager import download_manager
from manager.multi_thread import DownloadStatus

if TYPE_CHECKING:
    from ui.app import App


# ─── Stat Card ────────────────────────────────────────────────────────────────

class StatCard(ctk.CTkFrame):
    """Glassmorphism-style stat card with icon, value, and label."""

    def __init__(self, parent, icon: str, label: str, value: str,
                 accent: str = COLORS["accent"], **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )

        # Colored top bar
        top_bar = ctk.CTkFrame(self, height=3, fg_color=accent, corner_radius=0)
        top_bar.pack(fill="x", side="top")
        top_bar.configure(corner_radius=16)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=14)

        # Icon
        icon_frame = ctk.CTkFrame(inner, fg_color=accent + "22", width=42, height=42,
                                   corner_radius=10)
        icon_frame.pack(anchor="w")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text=icon, font=("Segoe UI", 18),
                     text_color=accent).place(relx=0.5, rely=0.5, anchor="center")

        # Value
        self._val_lbl = ctk.CTkLabel(
            inner, text=value,
            font=FONTS["heading_lg"], text_color=COLORS["text_primary"],
        )
        self._val_lbl.pack(anchor="w", pady=(8, 0))

        # Label
        ctk.CTkLabel(
            inner, text=label,
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

    def update_value(self, new_value: str):
        self._val_lbl.configure(text=new_value)


# ─── Quick Action Button ───────────────────────────────────────────────────────

class QuickAction(ctk.CTkFrame):
    """Clickable quick-action card."""

    def __init__(self, parent, icon: str, label: str, subtitle: str,
                 command: callable, accent: str = COLORS["accent"], **kwargs):
        super().__init__(
            parent, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
            cursor="hand2", **kwargs,
        )
        self._accent = accent
        self._normal_bg = COLORS["bg_card"]
        self._hover_bg  = COLORS["bg_elevated"]

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        # Icon circle
        circle = ctk.CTkFrame(inner, width=44, height=44, corner_radius=22,
                               fg_color=accent + "33")
        circle.pack(anchor="w")
        circle.pack_propagate(False)
        ctk.CTkLabel(circle, text=icon, font=("Segoe UI", 18),
                     text_color=accent).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=label, font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", pady=(8, 2))
        ctk.CTkLabel(inner, text=subtitle, font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        for w in (self, inner):
            w.bind("<Enter>",  lambda e: self.configure(fg_color=self._hover_bg))
            w.bind("<Leave>",  lambda e: self.configure(fg_color=self._normal_bg))
            w.bind("<Button-1>", lambda e: command())


# ─── Recent Download Row ──────────────────────────────────────────────────────

class RecentRow(ctk.CTkFrame):
    def __init__(self, parent, entry, **kwargs):
        super().__init__(parent, fg_color="transparent", height=52, **kwargs)
        self.pack_propagate(False)

        # Status dot
        dot_color = (COLORS["accent_green"] if entry.status == "done"
                     else COLORS["accent_red"])
        ctk.CTkFrame(self, width=8, height=8, corner_radius=4,
                     fg_color=dot_color).place(x=0, y=22)

        # Type icon + title
        ctk.CTkLabel(self, text=entry.type_icon, font=FONTS["body_lg"],
                     text_color=COLORS["text_secondary"]).place(x=16, y=14)

        title_text = entry.title[:40] + ("…" if len(entry.title) > 40 else "")
        ctk.CTkLabel(self, text=title_text, font=FONTS["body_md"],
                     text_color=COLORS["text_primary"]).place(x=42, y=10)

        ctk.CTkLabel(self, text=f"{entry.platform} • {entry.timestamp}",
                     font=FONTS["caption"],
                     text_color=COLORS["text_muted"]).place(x=42, y=32)

        # Size
        ctk.CTkLabel(self, text=entry.size_str, font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).place(relx=1.0, x=-10, y=18,
                                                                 anchor="ne")


# ─── Home Page ────────────────────────────────────────────────────────────────

class HomePage(ctk.CTkFrame):
    """Main dashboard page."""

    def __init__(self, parent, app: "App", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0, **kwargs)
        self._app = app
        self._stat_cards: dict = {}
        self._build()
        self._start_refresh()

    def _build(self):
        # ── Scrollable inner ──────────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", scrollbar_button_color=COLORS["border"],
        )
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 4))

        ctk.CTkLabel(header, text="Dashboard", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(header, text="Welcome back, Shanudha  ·  All systems ready",
                     font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(anchor="w")

        # ── Stat cards row ────────────────────────────────────────────────────
        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", padx=30, pady=(20, 0))

        stats_data = [
            ("⬇",  "Total Downloads",  "0",   COLORS["accent"]),
            ("🎬", "Videos",           "0",   COLORS["accent_2"]),
            ("🎵", "Audio Files",      "0",   COLORS["accent_green"]),
            ("⚡",  "Active DLs",      "0",   COLORS["accent_orange"]),
        ]

        for i, (icon, label, val, accent) in enumerate(stats_data):
            card = StatCard(stats_frame, icon=icon, label=label, value=val, accent=accent)
            card.grid(row=0, column=i, padx=(0, 14) if i < 3 else (0, 0), sticky="ew")
            stats_frame.grid_columnconfigure(i, weight=1)
            self._stat_cards[label] = card

        # ── Quick Actions ─────────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="Quick Actions", font=FONTS["heading_md"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=30, pady=(28, 10))

        qa_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        qa_frame.pack(fill="x", padx=30)

        actions = [
            ("⬇", "New Download",    "Paste URL & download",
             lambda: self._app.navigate("downloader"), COLORS["accent"]),
            ("⚡", "Download Manager","Manage active downloads",
             lambda: self._app.navigate("manager"), COLORS["accent_2"]),
            ("📁", "Open Downloads",  "Browse saved files",
             self._open_downloads_folder, COLORS["accent_green"]),
            ("📋", "Paste & Go",      "From clipboard instantly",
             self._paste_and_go, COLORS["accent_orange"]),
        ]

        for i, (icon, label, sub, cmd, accent) in enumerate(actions):
            qa = QuickAction(qa_frame, icon=icon, label=label, subtitle=sub,
                             command=cmd, accent=accent)
            qa.grid(row=0, column=i, padx=(0, 14) if i < 3 else (0, 0), sticky="ew")
            qa_frame.grid_columnconfigure(i, weight=1)

        # ── Recent Downloads ──────────────────────────────────────────────────
        ctk.CTkLabel(scroll, text="Recent Downloads", font=FONTS["heading_md"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=30, pady=(28, 10))

        self._recent_frame = ctk.CTkFrame(
            scroll, fg_color=COLORS["bg_card"], corner_radius=16,
            border_width=1, border_color=COLORS["border"],
        )
        self._recent_frame.pack(fill="x", padx=30, pady=(0, 30))

        self._recent_container = ctk.CTkFrame(self._recent_frame, fg_color="transparent")
        self._recent_container.pack(fill="x", padx=20, pady=12)

        self._empty_label = ctk.CTkLabel(
            self._recent_container,
            text="No downloads yet. Go to Downloader to start!",
            font=FONTS["body_md"], text_color=COLORS["text_muted"],
        )
        self._empty_label.pack(pady=20)

        self._refresh_recent()

    def _refresh_recent(self):
        """Update recent downloads list."""
        for w in self._recent_container.winfo_children():
            w.destroy()

        entries = history_manager.get_all()[:8]
        if not entries:
            self._empty_label = ctk.CTkLabel(
                self._recent_container,
                text="No downloads yet. Start from the Downloader!",
                font=FONTS["body_md"], text_color=COLORS["text_muted"],
            )
            self._empty_label.pack(pady=20)
        else:
            for i, entry in enumerate(entries):
                row = RecentRow(self._recent_container, entry)
                row.pack(fill="x", pady=2)
                if i < len(entries) - 1:
                    ctk.CTkFrame(self._recent_container, height=1,
                                 fg_color=COLORS["border"]).pack(fill="x")

    def _refresh_stats(self):
        """Update stat cards with live data."""
        total   = history_manager.count
        videos  = len(history_manager.filter_by_type("video"))
        audio   = len(history_manager.filter_by_type("audio"))
        active  = download_manager.active_count()

        self._stat_cards["Total Downloads"].update_value(str(total))
        self._stat_cards["Videos"].update_value(str(videos))
        self._stat_cards["Audio Files"].update_value(str(audio))
        self._stat_cards["Active DLs"].update_value(str(active))

    def _start_refresh(self):
        """Periodically refresh stats."""
        def loop():
            try:
                self._refresh_stats()
                self._refresh_recent()
            except Exception:
                pass
            self.after(5000, loop)

        self.after(1000, loop)

    def _open_downloads_folder(self):
        import subprocess, platform, os
        from core.config import config, DOWNLOAD_DIR
        folder = config.get("download_dir", str(DOWNLOAD_DIR))
        os.makedirs(folder, exist_ok=True)
        if platform.system() == "Windows":
            os.startfile(folder)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def _paste_and_go(self):
        try:
            import tkinter as tk
            root = tk.Tk(); root.withdraw()
            url = root.clipboard_get(); root.destroy()
            if url.startswith("http"):
                self._app.go_to_downloader(url)
        except Exception:
            pass
