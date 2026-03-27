"""
Shanu Fx Private Downloader - Torrent Page
Magnet link and .torrent file download UI.
Author: Shanudha Tirosh
"""

from typing import TYPE_CHECKING

import customtkinter as ctk

from core.config import COLORS, FONTS
from downloader.torrent import torrent_downloader, TorrentProgress
from utils.notifications import notifications

if TYPE_CHECKING:
    from ui.app import App


class TorrentPage(ctk.CTkFrame):
    """Torrent downloader UI page."""

    def __init__(self, parent, app: "App", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0, **kwargs)
        self._app  = app
        self._active = False
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        scroll.pack(fill="both", expand=True)

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(24, 4))
        ctk.CTkLabel(hdr, text="Torrent Downloader", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(hdr,
                     text="Download via magnet links or .torrent files",
                     font=FONTS["body_md"],
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        # libtorrent availability banner
        if not torrent_downloader.is_available():
            warn = ctk.CTkFrame(scroll, fg_color=COLORS["accent_orange"] + "22",
                                 corner_radius=12,
                                 border_width=1,
                                 border_color=COLORS["accent_orange"])
            warn.pack(fill="x", padx=30, pady=(16, 0))

            ctk.CTkLabel(warn,
                         text="⚠  libtorrent not installed  —  torrent support is disabled",
                         font=FONTS["heading_sm"],
                         text_color=COLORS["accent_orange"]
                         ).pack(anchor="w", padx=16, pady=(12, 4))

            ctk.CTkLabel(warn,
                         text=torrent_downloader.install_instructions(),
                         font=FONTS["mono"],
                         text_color=COLORS["text_secondary"],
                         justify="left",
                         ).pack(anchor="w", padx=16, pady=(0, 12))

        # Input card
        card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=16,
                             border_width=1, border_color=COLORS["border"])
        card.pack(fill="x", padx=30, pady=(16, 0))

        ctk.CTkLabel(card, text="Magnet Link or .torrent File",
                     font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 4))

        url_row = ctk.CTkFrame(card, fg_color="transparent")
        url_row.pack(fill="x", padx=16, pady=(0, 8))

        self._entry = ctk.CTkEntry(
            url_row,
            placeholder_text="magnet:?xt=urn:btih:… or path/to/file.torrent",
            height=44, font=FONTS["body_md"],
            fg_color=COLORS["bg_elevated"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            url_row, text="Browse", width=80, height=44,
            fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"],
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
            command=self._browse_torrent,
        ).pack(side="left", padx=(0, 8))

        self._start_btn = ctk.CTkButton(
            url_row, text="⬇  Start", height=44, width=110,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["heading_sm"],
            state="normal" if torrent_downloader.is_available() else "disabled",
            command=self._start_download,
        )
        self._start_btn.pack(side="left")

        # Progress
        prog_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=16,
                                  border_width=1, border_color=COLORS["border"])
        prog_card.pack(fill="x", padx=30, pady=(14, 0))

        ctk.CTkLabel(prog_card, text="Progress", font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 4))

        prog_inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_inner.pack(fill="x", padx=16, pady=(0, 14))

        self._status_lbl = ctk.CTkLabel(prog_inner, text="No active torrent",
                                         font=FONTS["body_md"],
                                         text_color=COLORS["text_secondary"])
        self._status_lbl.pack(anchor="w")

        self._pb = ctk.CTkProgressBar(prog_inner, height=8, corner_radius=4,
                                       fg_color=COLORS["bg_elevated"],
                                       progress_color=COLORS["accent"])
        self._pb.pack(fill="x", pady=6)
        self._pb.set(0)

        info_row = ctk.CTkFrame(prog_inner, fg_color="transparent")
        info_row.pack(fill="x")

        self._pct_lbl   = ctk.CTkLabel(info_row, text="0%", font=FONTS["heading_sm"],
                                        text_color=COLORS["accent"])
        self._pct_lbl.pack(side="left")

        self._speed_lbl = ctk.CTkLabel(info_row, text="", font=FONTS["body_sm"],
                                        text_color=COLORS["text_secondary"])
        self._speed_lbl.pack(side="left", padx=(12, 0))

        self._peers_lbl = ctk.CTkLabel(info_row, text="", font=FONTS["body_sm"],
                                        text_color=COLORS["text_muted"])
        self._peers_lbl.pack(side="right")

        self._eta_lbl = ctk.CTkLabel(info_row, text="", font=FONTS["body_sm"],
                                      text_color=COLORS["text_muted"])
        self._eta_lbl.pack(side="right", padx=(0, 12))

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _browse_torrent(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select .torrent file",
            filetypes=[("Torrent files", "*.torrent"), ("All files", "*.*")],
        )
        if path:
            self._entry.delete(0, "end")
            self._entry.insert(0, path)

    def _start_download(self):
        source = self._entry.get().strip()
        if not source:
            notifications.warning("Please enter a magnet link or .torrent path")
            return
        if self._active:
            notifications.info("Torrent already downloading")
            return

        self._active = True
        self._start_btn.configure(state="disabled", text="Downloading…")

        from core.config import config
        out_dir = config.get("download_dir", "~/Downloads/ShanuFx")

        def on_progress(p: TorrentProgress):
            self.after(0, lambda: self._update_progress(p))

        def on_done(path: str):
            self.after(0, lambda: self._on_done(path))

        def on_error(err: str):
            self.after(0, lambda: self._on_error(err))

        torrent_downloader.download(
            source=source,
            output_dir=out_dir,
            on_progress=on_progress,
            on_done=on_done,
            on_error=on_error,
        )

    def _update_progress(self, p: TorrentProgress):
        self._status_lbl.configure(text=f"{p.name}  ·  {p.status.title()}")
        self._pb.set(p.percent / 100)
        self._pct_lbl.configure(text=f"{p.percent:.1f}%")
        self._speed_lbl.configure(text=p.speed_str)
        self._peers_lbl.configure(text=f"Peers: {p.peers} / Seeds: {p.seeds}")
        self._eta_lbl.configure(text=f"ETA: {p.eta_str}")

    def _on_done(self, path: str):
        self._active = False
        self._start_btn.configure(state="normal", text="⬇  Start")
        self._pb.set(1.0)
        self._pct_lbl.configure(text="100%", text_color=COLORS["accent_green"])
        self._status_lbl.configure(text="✓ Torrent complete!")
        notifications.success("Torrent download finished", "Torrent Done")

    def _on_error(self, err: str):
        self._active = False
        self._start_btn.configure(state="normal", text="⬇  Start")
        self._status_lbl.configure(text=f"✕ Error: {err[:60]}")
        notifications.error(err[:80], "Torrent Error")
