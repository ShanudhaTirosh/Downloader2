"""
Shanu Fx Private Downloader - Downloader Page
Social media download UI with thumbnail preview, format picker, and progress.
Author: Shanudha Tirosh
"""

import io
import os
import threading
import tkinter as tk
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw

from core.config import COLORS, FONTS, VIDEO_QUALITIES, AUDIO_BITRATES, config
from downloader.ytdlp_backend import ytdlp_backend, VideoInfo, DownloadProgress
from downloader.history import history_manager, HistoryEntry
from utils.notifications import notifications

if TYPE_CHECKING:
    from ui.app import App

# ─── Platform Badge ───────────────────────────────────────────────────────────

PLATFORM_COLORS = {
    "YouTube":   "#FF0000", "TikTok":    "#010101",
    "Instagram": "#E1306C", "Facebook":  "#1877F2",
    "Twitter/X": "#1DA1F2", "Twitch":    "#9146FF",
    "Vimeo":     "#1AB7EA", "Dailymotion":"#0066DC",
}


def platform_badge_color(platform: str) -> str:
    for key, color in PLATFORM_COLORS.items():
        if key.lower() in platform.lower():
            return color
    return COLORS["accent"]


# ─── Thumbnail Widget ─────────────────────────────────────────────────────────

class ThumbnailWidget(ctk.CTkFrame):
    """Shows a video thumbnail with a play icon overlay."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_elevated"],
                         corner_radius=12, width=240, height=135, **kwargs)
        self.pack_propagate(False)
        self._img_ref = None

        self._placeholder = ctk.CTkLabel(
            self, text="🎬\nThumbnail Preview",
            font=FONTS["body_md"], text_color=COLORS["text_muted"],
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self._canvas = tk.Canvas(
            self, width=240, height=135,
            bg=COLORS["bg_elevated"], highlightthickness=0,
        )

    def load_image_bytes(self, data: bytes):
        """Display image from raw bytes."""
        try:
            img = Image.open(io.BytesIO(data))
            img = img.resize((240, 135), Image.LANCZOS)
            self._img_ref = ImageTk.PhotoImage(img)

            self._placeholder.place_forget()
            self._canvas.place(x=0, y=0)
            self._canvas.create_image(0, 0, anchor="nw", image=self._img_ref)
            # Play button overlay
            self._canvas.create_oval(100, 47, 140, 87, fill="#00000088", outline="")
            self._canvas.create_polygon(116, 55, 116, 79, 136, 67, fill="white")
        except Exception:
            pass

    def reset(self):
        self._canvas.place_forget()
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")
        self._img_ref = None


# ─── Progress Section ─────────────────────────────────────────────────────────

class DownloadProgressWidget(ctk.CTkFrame):
    """Shows download progress bar, speed, ETA, and status."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                         border_width=1, border_color=COLORS["border"], **kwargs)

        self._status_lbl = ctk.CTkLabel(
            self, text="Ready to download", font=FONTS["body_md"],
            text_color=COLORS["text_secondary"],
        )
        self._status_lbl.pack(anchor="w", padx=16, pady=(12, 4))

        self._pb = ctk.CTkProgressBar(
            self, height=8, corner_radius=4,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["accent"],
        )
        self._pb.pack(fill="x", padx=16, pady=4)
        self._pb.set(0)

        info_row = ctk.CTkFrame(self, fg_color="transparent")
        info_row.pack(fill="x", padx=16, pady=(4, 12))

        self._pct_lbl   = ctk.CTkLabel(info_row, text="0%", font=FONTS["heading_sm"],
                                        text_color=COLORS["accent"])
        self._pct_lbl.pack(side="left")

        self._speed_lbl = ctk.CTkLabel(info_row, text="", font=FONTS["body_sm"],
                                        text_color=COLORS["text_secondary"])
        self._speed_lbl.pack(side="left", padx=(12, 0))

        self._eta_lbl   = ctk.CTkLabel(info_row, text="", font=FONTS["body_sm"],
                                        text_color=COLORS["text_muted"])
        self._eta_lbl.pack(side="right")

    def update(self, progress: DownloadProgress):
        pct    = progress.percent
        status = progress.status
        speed  = progress.speed or ""
        eta    = progress.eta or ""

        color_map = {
            "downloading": COLORS["accent"],
            "processing":  COLORS["accent_orange"],
            "done":        COLORS["accent_green"],
            "error":       COLORS["accent_red"],
        }
        bar_color = color_map.get(status, COLORS["accent"])

        self._pb.configure(progress_color=bar_color)
        self._pb.set(pct / 100.0)
        self._pct_lbl.configure(text=f"{pct:.1f}%", text_color=bar_color)
        self._speed_lbl.configure(text=speed)
        self._eta_lbl.configure(text=f"ETA: {eta}" if eta else "")

        status_text_map = {
            "idle":        "Ready to download",
            "downloading": f"Downloading… {pct:.1f}%",
            "processing":  "⚙ Processing with FFmpeg…",
            "done":        "✓ Download complete!",
            "error":       f"✕ Error: {progress.error}",
        }
        self._status_lbl.configure(
            text=status_text_map.get(status, status),
            text_color=bar_color if status in ("done", "error", "processing") else COLORS["text_secondary"],
        )

    def reset(self):
        self._pb.set(0)
        self._pb.configure(progress_color=COLORS["accent"])
        self._pct_lbl.configure(text="0%", text_color=COLORS["accent"])
        self._speed_lbl.configure(text="")
        self._eta_lbl.configure(text="")
        self._status_lbl.configure(text="Ready to download",
                                    text_color=COLORS["text_secondary"])


# ─── Downloader Page ──────────────────────────────────────────────────────────

class DownloaderPage(ctk.CTkFrame):
    """
    Social media downloader page.
    Left: URL input + options. Right: Info panel.
    """

    def __init__(self, parent, app: "App", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0, **kwargs)
        self._app         = app
        self._info:       Optional[VideoInfo] = None
        self._is_fetching = False
        self._is_downloading = False
        self._build()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 8))

        ctk.CTkLabel(header, text="Media Downloader", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(header, text="YouTube · TikTok · Instagram · Facebook · Twitter · and 1000+ sites",
                     font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(anchor="w")

        # Main area: left column + right column
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=30, pady=8)
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        self._build_left(main)
        self._build_right(main)

    def _build_left(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                       scrollbar_button_color=COLORS["border"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        # ── URL Input Card ────────────────────────────────────────────────────
        url_card = ctk.CTkFrame(left, fg_color=COLORS["bg_card"], corner_radius=16,
                                 border_width=1, border_color=COLORS["border"])
        url_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(url_card, text="Enter URL", font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 4))

        url_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_row.pack(fill="x", padx=16, pady=(0, 14))

        self._url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="Paste URL here… (YouTube, TikTok, Instagram, etc.)",
            height=44, font=FONTS["body_md"],
            fg_color=COLORS["bg_elevated"],
            border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self._url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Paste button
        ctk.CTkButton(
            url_row, text="Paste", width=70, height=44,
            fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"],
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
            command=self._paste_url,
        ).pack(side="left", padx=(0, 8))

        # Fetch button
        self._fetch_btn = ctk.CTkButton(
            url_row, text="Fetch Info", width=100, height=44,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["heading_sm"], text_color="white",
            command=self._fetch_info,
        )
        self._fetch_btn.pack(side="left")

        # ── Download Options Card ─────────────────────────────────────────────
        opts_card = ctk.CTkFrame(left, fg_color=COLORS["bg_card"], corner_radius=16,
                                  border_width=1, border_color=COLORS["border"])
        opts_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(opts_card, text="Download Options", font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 4))

        opts_inner = ctk.CTkFrame(opts_card, fg_color="transparent")
        opts_inner.pack(fill="x", padx=16, pady=(0, 14))
        opts_inner.grid_columnconfigure((0, 1, 2), weight=1)

        # Format type
        ctk.CTkLabel(opts_inner, text="Format", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=0, sticky="w")
        self._fmt_var = ctk.StringVar(value=config.get("default_format", "mp4").upper())
        fmt_menu = ctk.CTkOptionMenu(
            opts_inner, variable=self._fmt_var,
            values=["MP4 (Video)", "MP3 (Audio)", "WEBM (Video)", "M4A (Audio)"],
            fg_color=COLORS["bg_elevated"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_elevated"],
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
            command=self._on_format_change,
        )
        fmt_menu.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(4, 0))

        # Quality
        ctk.CTkLabel(opts_inner, text="Quality", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=1, sticky="w")
        self._quality_var = ctk.StringVar(value=config.get("default_quality", "best").title())
        self._quality_menu = ctk.CTkOptionMenu(
            opts_inner, variable=self._quality_var,
            values=[q.title() for q in VIDEO_QUALITIES],
            fg_color=COLORS["bg_elevated"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_elevated"],
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
        )
        self._quality_menu.grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(4, 0))

        # Bitrate (audio)
        ctk.CTkLabel(opts_inner, text="Bitrate", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).grid(row=0, column=2, sticky="w")
        self._bitrate_var = ctk.StringVar(value=config.get("default_bitrate", "192kbps"))
        self._bitrate_menu = ctk.CTkOptionMenu(
            opts_inner, variable=self._bitrate_var,
            values=AUDIO_BITRATES,
            fg_color=COLORS["bg_elevated"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_elevated"],
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
        )
        self._bitrate_menu.grid(row=1, column=2, sticky="ew", pady=(4, 0))

        # ── Output directory ──────────────────────────────────────────────────
        dir_row = ctk.CTkFrame(opts_card, fg_color="transparent")
        dir_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(dir_row, text="Save To:", font=FONTS["body_sm"],
                     text_color=COLORS["text_secondary"]).pack(side="left")

        self._dir_lbl = ctk.CTkLabel(dir_row, text=config.get("download_dir", "~/Downloads/ShanuFx"),
                                      font=FONTS["body_sm"], text_color=COLORS["text_muted"])
        self._dir_lbl.pack(side="left", padx=(8, 0))

        ctk.CTkButton(dir_row, text="Browse", width=70, height=28,
                      fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"],
                      font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
                      command=self._browse_dir).pack(side="right")

        # ── Download button ───────────────────────────────────────────────────
        self._dl_btn = ctk.CTkButton(
            left, text="⬇  Start Download", height=52,
            font=FONTS["heading_md"], fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._start_download,
            state="disabled",
        )
        self._dl_btn.pack(fill="x", pady=(0, 16))

        # ── Progress widget ───────────────────────────────────────────────────
        self._progress_widget = DownloadProgressWidget(left)
        self._progress_widget.pack(fill="x", pady=(0, 16))

    def _build_right(self, parent):
        right = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                        scrollbar_button_color=COLORS["border"])
        right.grid(row=0, column=1, sticky="nsew")

        # ── Info card ─────────────────────────────────────────────────────────
        self._info_card = ctk.CTkFrame(right, fg_color=COLORS["bg_card"], corner_radius=16,
                                        border_width=1, border_color=COLORS["border"])
        self._info_card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(self._info_card, text="Video Info", font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 8))

        # Thumbnail
        self._thumb = ThumbnailWidget(self._info_card)
        self._thumb.pack(padx=16, pady=(0, 12))

        # Info fields
        info_grid = ctk.CTkFrame(self._info_card, fg_color="transparent")
        info_grid.pack(fill="x", padx=16, pady=(0, 14))

        self._field_labels = {}
        fields = [
            ("title",    "Title"),
            ("uploader", "Channel"),
            ("platform", "Platform"),
            ("duration", "Duration"),
        ]
        for i, (key, label) in enumerate(fields):
            ctk.CTkLabel(info_grid, text=f"{label}:", font=FONTS["body_sm"],
                         text_color=COLORS["text_secondary"]).grid(row=i, column=0, sticky="w", pady=3)
            val_lbl = ctk.CTkLabel(info_grid, text="—", font=FONTS["body_sm"],
                                    text_color=COLORS["text_primary"], wraplength=180)
            val_lbl.grid(row=i, column=1, sticky="w", padx=(8, 0), pady=3)
            self._field_labels[key] = val_lbl

        # ── Formats card ─────────────────────────────────────────────────────
        self._fmts_card = ctk.CTkFrame(right, fg_color=COLORS["bg_card"], corner_radius=16,
                                        border_width=1, border_color=COLORS["border"])
        self._fmts_card.pack(fill="x")

        ctk.CTkLabel(self._fmts_card, text="Available Formats", font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=16, pady=(14, 4))

        self._fmts_container = ctk.CTkFrame(self._fmts_card, fg_color="transparent")
        self._fmts_container.pack(fill="x", padx=16, pady=(0, 14))

        self._fmts_empty = ctk.CTkLabel(self._fmts_container, text="Fetch a URL to see formats",
                                         font=FONTS["body_sm"], text_color=COLORS["text_muted"])
        self._fmts_empty.pack(pady=12)

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _on_format_change(self, choice: str):
        is_audio = "audio" in choice.lower() or "mp3" in choice.lower() or "m4a" in choice.lower()
        self._bitrate_menu.configure(state="normal" if is_audio else "disabled")
        self._quality_menu.configure(state="disabled" if is_audio else "normal")

    def _paste_url(self):
        try:
            import tkinter as tk
            r = tk.Tk(); r.withdraw()
            url = r.clipboard_get(); r.destroy()
            if url:
                self._url_entry.delete(0, "end")
                self._url_entry.insert(0, url.strip())
        except Exception:
            pass

    def set_url(self, url: str):
        """Prefill URL from clipboard monitor or external call."""
        self._url_entry.delete(0, "end")
        self._url_entry.insert(0, url)
        self._fetch_info()

    def _browse_dir(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Choose Download Folder")
        if folder:
            config.set("download_dir", folder)
            self._dir_lbl.configure(text=folder)

    def _fetch_info(self):
        url = self._url_entry.get().strip()
        if not url:
            notifications.warning("Please enter a URL first")
            return
        if self._is_fetching:
            return

        self._is_fetching = True
        self._fetch_btn.configure(text="Fetching…", state="disabled")
        self._thumb.reset()
        self._dl_btn.configure(state="disabled")

        for key, lbl in self._field_labels.items():
            lbl.configure(text="Loading…")

        def on_success(info: VideoInfo):
            self.after(0, lambda: self._display_info(info))

        def on_error(err: str):
            self.after(0, lambda: self._on_fetch_error(err))

        ytdlp_backend.fetch_info(url, on_success=on_success, on_error=on_error)

    def _display_info(self, info: VideoInfo):
        self._info = info
        self._is_fetching = False
        self._fetch_btn.configure(text="Fetch Info", state="normal")
        self._dl_btn.configure(state="normal")

        # Update fields
        self._field_labels["title"].configure(
            text=info.title[:50] + ("…" if len(info.title) > 50 else ""))
        self._field_labels["uploader"].configure(text=info.uploader)
        self._field_labels["platform"].configure(text=info.platform_name)
        self._field_labels["duration"].configure(text=info.duration_str)

        # Fetch thumbnail
        if info.thumbnail:
            ytdlp_backend.fetch_thumbnail(
                info.thumbnail,
                on_success=lambda data: self.after(0, lambda: self._thumb.load_image_bytes(data)),
            )

        # Display formats
        for w in self._fmts_container.winfo_children():
            w.destroy()

        for fmt in info.formats[:8]:
            row = ctk.CTkFrame(self._fmts_container, fg_color=COLORS["bg_elevated"],
                                corner_radius=8, height=32)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            color = COLORS["accent_2"] if fmt["type"] == "audio" else COLORS["accent"]
            ctk.CTkLabel(row, text=fmt["label"], font=FONTS["body_sm"],
                         text_color=color).place(x=10, y=7)

        notifications.success(f"Info fetched: {info.title[:40]}", "Media Ready")

    def _on_fetch_error(self, err: str):
        self._is_fetching = False
        self._fetch_btn.configure(text="Fetch Info", state="normal")
        for lbl in self._field_labels.values():
            lbl.configure(text="—")
        notifications.error(f"Fetch failed: {err[:80]}", "Error")

    def _start_download(self):
        url = self._url_entry.get().strip()
        if not url:
            notifications.warning("Please enter a URL")
            return
        if self._is_downloading:
            notifications.info("Download already in progress")
            return

        fmt_choice = self._fmt_var.get().lower()
        is_audio   = "mp3" in fmt_choice or "audio" in fmt_choice or "m4a" in fmt_choice
        fmt_type   = "audio" if is_audio else "video"
        quality    = self._quality_var.get().lower()
        bitrate    = self._bitrate_var.get()
        output_dir = config.get("download_dir", "~/Downloads/ShanuFx")

        self._is_downloading = True
        self._dl_btn.configure(text="Downloading…", state="disabled",
                                fg_color=COLORS["bg_elevated"])
        self._progress_widget.reset()

        start_time = __import__("time").time()

        def on_progress(p: DownloadProgress):
            self.after(0, lambda: self._progress_widget.update(p))

        def on_done(filepath: str):
            elapsed = __import__("time").time() - start_time
            self.after(0, lambda: self._on_download_done(filepath, fmt_type, elapsed))

        def on_error(err: str):
            self.after(0, lambda: self._on_download_error(err))

        ytdlp_backend.download(
            url=url,
            output_dir=output_dir,
            fmt_type=fmt_type,
            quality=quality,
            bitrate=bitrate,
            on_progress=on_progress,
            on_done=on_done,
            on_error=on_error,
            download_id=url[:20],
        )

    def _on_download_done(self, filepath: str, fmt_type: str, elapsed: float):
        self._is_downloading = False
        self._dl_btn.configure(text="⬇  Start Download", state="normal",
                                fg_color=COLORS["accent"])

        # Save to history
        info = self._info
        import os
        size = 0
        try: size = os.path.getsize(filepath)
        except Exception: pass

        entry = HistoryEntry(
            title      = info.title if info else "Download",
            url        = self._url_entry.get().strip(),
            filename   = os.path.basename(filepath),
            filepath   = filepath,
            fmt_type   = fmt_type,
            size_bytes = size,
            duration   = info.duration_str if info else "",
            platform   = info.platform_name if info else "",
            status     = "done",
        )
        history_manager.add(entry)
        notifications.success(f"Downloaded in {elapsed:.1f}s", "Download Complete")

    def _on_download_error(self, err: str):
        self._is_downloading = False
        self._dl_btn.configure(text="⬇  Start Download", state="normal",
                                fg_color=COLORS["accent"])
        notifications.error(err[:100], "Download Failed")
