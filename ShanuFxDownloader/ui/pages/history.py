"""
Shanu Fx Private Downloader - History Page
Searchable, filterable download history with open/delete actions.
Author: Shanudha Tirosh
"""

import os
import subprocess
import platform
from typing import TYPE_CHECKING, List

import customtkinter as ctk

from core.config import COLORS, FONTS
from downloader.history import history_manager, HistoryEntry
from ui.widgets.shared import SearchEntry, EmptyState, Divider, StatusBadge

if TYPE_CHECKING:
    from ui.app import App


# ─── History Row ──────────────────────────────────────────────────────────────

class HistoryRow(ctk.CTkFrame):
    """A single row in the history list."""

    def __init__(self, parent, entry: HistoryEntry, on_delete: callable, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )
        self._entry     = entry
        self._on_delete = on_delete
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=8)

        # ── Left: type icon + metadata ────────────────────────────────────────
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        row1 = ctk.CTkFrame(left, fg_color="transparent")
        row1.pack(fill="x")

        # Type icon
        ctk.CTkLabel(row1, text=self._entry.type_icon,
                     font=("Segoe UI", 16),
                     text_color=COLORS["accent"]).pack(side="left")

        # Title (truncated)
        title = self._entry.title[:60] + ("…" if len(self._entry.title) > 60 else "")
        ctk.CTkLabel(row1, text=title, font=FONTS["body_md"],
                     text_color=COLORS["text_primary"]).pack(side="left", padx=(8, 0))

        # Status badge
        StatusBadge(row1, status=self._entry.status).pack(side="left", padx=(10, 0))

        row2 = ctk.CTkFrame(left, fg_color="transparent")
        row2.pack(fill="x", pady=(2, 0))

        meta_parts = [
            self._entry.platform,
            self._entry.duration if self._entry.duration else None,
            self._entry.size_str,
            self._entry.timestamp,
        ]
        meta_text = "  ·  ".join(p for p in meta_parts if p)
        ctk.CTkLabel(row2, text=meta_text, font=FONTS["caption"],
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(28, 0))

        # ── Right: action buttons ─────────────────────────────────────────────
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        btn_kw = dict(height=28, font=FONTS["caption"],
                      fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"])

        ctk.CTkButton(
            right, text="📂 Open", width=72, **btn_kw,
            text_color=COLORS["accent_light"],
            command=self._open_file,
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            right, text="✕", width=36, **btn_kw,
            text_color=COLORS["accent_red"],
            command=lambda: self._on_delete(self._entry.id),
        ).pack(side="left")

    def _open_file(self):
        filepath = self._entry.filepath
        if not filepath or not os.path.exists(filepath):
            # Open containing folder
            folder = os.path.expanduser("~/Downloads/ShanuFx")
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            return

        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", filepath])
        else:
            subprocess.Popen(["xdg-open", filepath])


# ─── History Page ─────────────────────────────────────────────────────────────

class HistoryPage(ctk.CTkFrame):
    """Full history browser with search, filter tabs, and per-entry actions."""

    FILTERS = ["All", "Videos", "Audio", "Files"]

    def __init__(self, parent, app: "App", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0, **kwargs)
        self._app          = app
        self._active_filter = "All"
        self._search_query  = ""
        self._row_widgets: dict = {}
        self._build()
        self._render_list()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(24, 4))

        ctk.CTkLabel(hdr, text="Download History", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(side="left", anchor="w")

        # Clear all button
        ctk.CTkButton(
            hdr, text="🗑  Clear All", height=36, width=120,
            fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"],
            font=FONTS["body_sm"], text_color=COLORS["accent_red"],
            command=self._clear_all,
        ).pack(side="right")

        # Stats bar
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.pack(fill="x", padx=30, pady=(0, 8))

        self._count_lbl = ctk.CTkLabel(
            stats, text=f"{history_manager.count} downloads",
            font=FONTS["body_md"], text_color=COLORS["text_secondary"],
        )
        self._count_lbl.pack(side="left")

        # Total size
        total_size = history_manager.total_size
        size_str   = self._fmt_bytes(total_size)
        self._size_lbl = ctk.CTkLabel(
            stats, text=f"  ·  {size_str} total",
            font=FONTS["body_md"], text_color=COLORS["text_muted"],
        )
        self._size_lbl.pack(side="left")

        # Controls row: search + filter tabs
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=30, pady=(0, 8))

        # Search
        self._search = SearchEntry(
            ctrl,
            placeholder="Search history…",
            on_change=self._on_search,
            width=280,
        )
        self._search.pack(side="left")

        # Filter tabs
        tab_frame = ctk.CTkFrame(ctrl, fg_color="transparent")
        tab_frame.pack(side="left", padx=(16, 0))

        self._filter_btns = {}
        for f in self.FILTERS:
            btn = ctk.CTkButton(
                tab_frame, text=f, width=80, height=32,
                fg_color=COLORS["accent"] if f == "All" else COLORS["bg_elevated"],
                hover_color=COLORS["bg_hover"],
                font=FONTS["body_sm"],
                text_color=COLORS["text_primary"] if f == "All" else COLORS["text_secondary"],
                command=lambda filt=f: self._set_filter(filt),
            )
            btn.pack(side="left", padx=(0, 6))
            self._filter_btns[f] = btn

        Divider(self).pack(fill="x", padx=30, pady=(4, 0))

        # List container
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self._scroll.pack(fill="both", expand=True, padx=30, pady=(8, 16))

    # ── Render ────────────────────────────────────────────────────────────────

    def _render_list(self):
        """Re-render history rows based on current filter + search."""
        for w in self._scroll.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        entries = self._filtered_entries()

        if not entries:
            EmptyState(
                self._scroll,
                icon="📭",
                title="No download history yet",
                subtitle="Downloaded files will appear here.",
            ).pack(pady=40)
            return

        for entry in entries:
            row = HistoryRow(self._scroll, entry, on_delete=self._delete_entry)
            row.pack(fill="x", pady=3)
            self._row_widgets[entry.id] = row

        self._count_lbl.configure(text=f"{len(entries)} downloads")

    def _filtered_entries(self) -> List[HistoryEntry]:
        entries = history_manager.get_all()

        # Filter by type tab
        type_map = {"Videos": "video", "Audio": "audio", "Files": "file"}
        if self._active_filter in type_map:
            t = type_map[self._active_filter]
            entries = [e for e in entries if e.fmt_type == t]

        # Filter by search
        if self._search_query:
            q = self._search_query.lower()
            entries = [e for e in entries
                       if q in e.title.lower() or q in e.platform.lower()
                       or q in e.filename.lower()]
        return entries

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _set_filter(self, f: str):
        self._active_filter = f
        for name, btn in self._filter_btns.items():
            active = name == f
            btn.configure(
                fg_color=COLORS["accent"] if active else COLORS["bg_elevated"],
                text_color=COLORS["text_primary"] if active else COLORS["text_secondary"],
            )
        self._render_list()

    def _on_search(self, query: str):
        self._search_query = query
        self._render_list()

    def _delete_entry(self, entry_id: str):
        history_manager.remove(entry_id)
        self._render_list()
        self._size_lbl.configure(text=f"  ·  {self._fmt_bytes(history_manager.total_size)} total")

    def _clear_all(self):
        history_manager.clear()
        self._render_list()
        self._count_lbl.configure(text="0 downloads")
        self._size_lbl.configure(text="  ·  0 B total")

    @staticmethod
    def _fmt_bytes(b: int) -> str:
        if b <= 0:       return "0 B"
        if b < 1024:     return f"{b} B"
        if b < 1024**2:  return f"{b/1024:.1f} KB"
        if b < 1024**3:  return f"{b/1024**2:.1f} MB"
        return f"{b/1024**3:.2f} GB"
