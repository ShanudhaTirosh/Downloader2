"""
Shanu Fx Private Downloader - Download Manager Page
IDM-style download manager with live progress, speed graph, and queue.
Author: Shanudha Tirosh
"""

import time
import threading
import tkinter as tk
from collections import deque
from typing import TYPE_CHECKING, Dict, Optional

import customtkinter as ctk

from core.config import COLORS, FONTS
from manager.download_manager import download_manager, filename_from_url
from manager.multi_thread import DownloadTask, DownloadStatus
from utils.notifications import notifications

if TYPE_CHECKING:
    from ui.app import App

# ─── Speed Graph ─────────────────────────────────────────────────────────────

class SpeedGraph(ctk.CTkFrame):
    """
    Simple real-time speed graph drawn on a Canvas.
    Displays the last N seconds of combined download speed.
    """

    HISTORY = 60   # data points to keep
    HEIGHT   = 90
    WIDTH    = 400

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_elevated"],
                         corner_radius=10, **kwargs)
        self._speeds: deque = deque([0.0] * self.HISTORY, maxlen=self.HISTORY)
        self._max    = 1.0   # dynamic y-axis max

        self._canvas = tk.Canvas(
            self, width=self.WIDTH, height=self.HEIGHT,
            bg=COLORS["bg_elevated"], highlightthickness=0,
        )
        self._canvas.pack(fill="both", expand=True, padx=2, pady=2)

        self._speed_lbl = ctk.CTkLabel(
            self, text="0 KB/s", font=FONTS["heading_sm"],
            text_color=COLORS["accent_light"],
        )
        self._speed_lbl.place(x=8, y=4)

        self._peak_lbl = ctk.CTkLabel(
            self, text="Peak: 0 KB/s", font=FONTS["caption"],
            text_color=COLORS["text_muted"],
        )
        self._peak_lbl.place(x=8, y=26)

        self._draw()

    def push(self, speed_bps: float):
        self._speeds.append(speed_bps)
        self._max = max(max(self._speeds), 1.0)
        self._draw()
        self._speed_lbl.configure(text=self._fmt(speed_bps))
        peak = max(self._speeds)
        self._peak_lbl.configure(text=f"Peak: {self._fmt(peak)}")

    @staticmethod
    def _fmt(bps: float) -> str:
        if bps < 1024:      return f"{bps:.0f} B/s"
        if bps < 1024**2:   return f"{bps/1024:.1f} KB/s"
        return f"{bps/1024**2:.2f} MB/s"

    def _draw(self):
        c = self._canvas
        w = self.WIDTH
        h = self.HEIGHT
        c.delete("all")

        # Background grid lines
        for i in range(1, 4):
            y = int(h * i / 4)
            c.create_line(0, y, w, y, fill=COLORS["border"], width=1)

        pts = list(self._speeds)
        n   = len(pts)
        if n < 2:
            return

        step = w / (n - 1)
        coords = []
        for i, spd in enumerate(pts):
            x = int(i * step)
            y = int(h - (spd / self._max) * (h - 4))
            coords.extend([x, y])

        # Fill area under the curve
        fill_coords = [0, h] + coords + [w, h]
        c.create_polygon(fill_coords, fill=COLORS["accent"] + "44", outline="")
        # Line
        c.create_line(coords, fill=COLORS["accent"], width=2, smooth=True)


# ─── Task Row Widget ──────────────────────────────────────────────────────────

class TaskRow(ctk.CTkFrame):
    """Displays a single download task with progress bar and controls."""

    STATUS_COLORS = {
        DownloadStatus.QUEUED:      COLORS["status_queued"],
        DownloadStatus.CONNECTING:  COLORS["accent_blue"],
        DownloadStatus.DOWNLOADING: COLORS["accent"],
        DownloadStatus.PAUSED:      COLORS["status_paused"],
        DownloadStatus.PROCESSING:  COLORS["accent_orange"],
        DownloadStatus.DONE:        COLORS["status_active"],
        DownloadStatus.ERROR:       COLORS["status_error"],
        DownloadStatus.CANCELLED:   COLORS["text_muted"],
    }

    def __init__(self, parent, task: DownloadTask, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                         border_width=1, border_color=COLORS["border"], **kwargs)
        self.task_id = task.task_id
        self._build(task)

    def _build(self, task: DownloadTask):
        self.grid_columnconfigure(0, weight=1)

        row1 = ctk.CTkFrame(self, fg_color="transparent")
        row1.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 2))

        # Status dot
        color = self.STATUS_COLORS.get(task.status, COLORS["text_muted"])
        self._dot = ctk.CTkFrame(row1, width=10, height=10, corner_radius=5, fg_color=color)
        self._dot.pack(side="left", padx=(0, 8))

        # Filename
        fname = task.filename[:55] + ("…" if len(task.filename) > 55 else "")
        self._name_lbl = ctk.CTkLabel(row1, text=fname, font=FONTS["body_md"],
                                       text_color=COLORS["text_primary"])
        self._name_lbl.pack(side="left")

        # Size
        self._size_lbl = ctk.CTkLabel(row1, text=task.size_str, font=FONTS["body_sm"],
                                       text_color=COLORS["text_secondary"])
        self._size_lbl.pack(side="right")

        # Progress bar
        self._pb = ctk.CTkProgressBar(self, height=6, corner_radius=3,
                                       fg_color=COLORS["progress_bg"],
                                       progress_color=color)
        self._pb.grid(row=1, column=0, sticky="ew", padx=14, pady=2)
        self._pb.set(task.percent / 100)

        # Row 2: stats + buttons
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.grid(row=2, column=0, sticky="ew", padx=14, pady=(2, 10))

        # Status text
        self._status_lbl = ctk.CTkLabel(row2, text=self._status_text(task),
                                         font=FONTS["caption"], text_color=COLORS["text_secondary"])
        self._status_lbl.pack(side="left")

        # Speed & ETA
        self._speed_lbl = ctk.CTkLabel(row2, text="", font=FONTS["caption"],
                                        text_color=COLORS["accent_light"])
        self._speed_lbl.pack(side="left", padx=(12, 0))

        # Control buttons
        btn_kw = dict(height=26, font=FONTS["caption"],
                      fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"],
                      text_color=COLORS["text_secondary"])

        self._pause_btn = ctk.CTkButton(
            row2, text="⏸ Pause", width=72, **btn_kw,
            command=lambda: download_manager.pause(self.task_id),
        )
        self._pause_btn.pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            row2, text="✕ Cancel", width=72, **btn_kw,
            text_color=COLORS["accent_red"],
            command=lambda: download_manager.cancel(self.task_id),
        ).pack(side="right", padx=(4, 0))

        ctk.CTkButton(
            row2, text="↻ Retry", width=72, **btn_kw,
            command=lambda: download_manager.retry(self.task_id),
        ).pack(side="right", padx=(4, 0))

        # Category badge
        cat_colors = {
            "videos": COLORS["accent"], "music": COLORS["accent_2"],
            "documents": COLORS["accent_blue"], "programs": COLORS["accent_orange"],
        }
        cat_color = cat_colors.get(task.category, COLORS["text_muted"])
        ctk.CTkLabel(row2, text=f"  {task.category.title()}  ",
                     font=FONTS["caption"], text_color=cat_color,
                     fg_color=cat_color + "22", corner_radius=4).pack(side="right", padx=(4, 0))

    def update_task(self, task: DownloadTask):
        """Update all dynamic fields."""
        try:
            color = self.STATUS_COLORS.get(task.status, COLORS["text_muted"])
            self._dot.configure(fg_color=color)
            self._pb.configure(progress_color=color)
            self._pb.set(min(task.percent / 100, 1.0))
            self._size_lbl.configure(text=f"{task.done_size_str} / {task.size_str}")
            self._status_lbl.configure(text=self._status_text(task))

            if task.status == DownloadStatus.DOWNLOADING:
                self._speed_lbl.configure(
                    text=f"{task.speed_str}  •  ETA {task.eta_str}"
                )
            else:
                self._speed_lbl.configure(text="")

            # Update pause/resume button
            if task.status == DownloadStatus.PAUSED:
                self._pause_btn.configure(text="▶ Resume",
                    command=lambda: download_manager.resume(self.task_id))
            else:
                self._pause_btn.configure(text="⏸ Pause",
                    command=lambda: download_manager.pause(self.task_id))
        except Exception:
            pass

    @staticmethod
    def _status_text(task: DownloadTask) -> str:
        status_map = {
            DownloadStatus.QUEUED:      "Queued",
            DownloadStatus.CONNECTING:  "Connecting…",
            DownloadStatus.DOWNLOADING: f"{task.percent:.1f}%",
            DownloadStatus.PAUSED:      f"Paused  {task.percent:.1f}%",
            DownloadStatus.PROCESSING:  "Processing…",
            DownloadStatus.DONE:        "✓ Complete",
            DownloadStatus.ERROR:       f"✕ {task.error_msg[:40]}",
            DownloadStatus.CANCELLED:   "Cancelled",
        }
        return status_map.get(task.status, str(task.status.value))


# ─── Manager Page ─────────────────────────────────────────────────────────────

class ManagerPage(ctk.CTkFrame):
    """Download Manager page — IDM-style UI."""

    def __init__(self, parent, app: "App", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0, **kwargs)
        self._app = app
        self._task_rows: Dict[str, TaskRow] = {}
        self._combined_speeds: deque = deque([0.0] * 60, maxlen=60)
        self._build()
        self._subscribe()
        self._start_speed_ticker()

    def _build(self):
        # Header row
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(24, 0))

        ctk.CTkLabel(hdr, text="Download Manager", font=FONTS["heading_xl"],
                     text_color=COLORS["text_primary"]).pack(side="left", anchor="w")

        # Add URL button
        ctk.CTkButton(
            hdr, text="+ Add URL", height=38, width=120,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["heading_sm"], command=self._add_url_dialog,
        ).pack(side="right")

        ctk.CTkButton(
            hdr, text="Clear Done", height=38, width=110,
            fg_color=COLORS["bg_elevated"], hover_color=COLORS["bg_hover"],
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
            command=self._clear_done,
        ).pack(side="right", padx=(0, 8))

        # Stats + speed graph row
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=30, pady=(12, 0))

        # Mini stat pills
        self._active_pill = self._make_pill(stats_row, "Active: 0", COLORS["accent"])
        self._queued_pill = self._make_pill(stats_row, "Queued: 0", COLORS["text_muted"])
        self._done_pill   = self._make_pill(stats_row, "Done: 0",   COLORS["accent_green"])
        self._error_pill  = self._make_pill(stats_row, "Failed: 0", COLORS["accent_red"])

        # Speed graph
        self._graph = SpeedGraph(stats_row)
        self._graph.pack(side="right")

        # Filter tabs
        tab_row = ctk.CTkFrame(self, fg_color="transparent")
        tab_row.pack(fill="x", padx=30, pady=(10, 0))

        self._filter_var = ctk.StringVar(value="All")
        for tab in ["All", "Downloading", "Queued", "Done", "Failed"]:
            is_active = tab == "All"
            btn = ctk.CTkButton(
                tab_row, text=tab, width=100, height=32,
                fg_color=COLORS["accent"] if is_active else COLORS["bg_elevated"],
                hover_color=COLORS["bg_hover"],
                font=FONTS["body_sm"],
                text_color=COLORS["text_primary"] if is_active else COLORS["text_secondary"],
                command=lambda t=tab: self._set_filter(t),
            )
            btn.pack(side="left", padx=(0, 6))

        # Task list
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=30, pady=(8, 0))

        self._list_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        self._list_scroll.pack(fill="both", expand=True, padx=30, pady=(8, 16))

        self._empty_lbl = ctk.CTkLabel(
            self._list_scroll,
            text="No downloads yet.\nClick '+ Add URL' or paste a URL in the Downloader.",
            font=FONTS["body_md"], text_color=COLORS["text_muted"],
        )
        self._empty_lbl.pack(pady=60)

    # ── Pills ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_pill(parent, text: str, color: str) -> ctk.CTkLabel:
        lbl = ctk.CTkLabel(
            parent, text=f"  {text}  ", font=FONTS["body_sm"],
            text_color=color, fg_color=color + "22", corner_radius=8,
        )
        lbl.pack(side="left", padx=(0, 8))
        return lbl

    # ── Filter ────────────────────────────────────────────────────────────────

    def _set_filter(self, f: str):
        self._filter_var.set(f)
        self._rebuild_list()

    def _clear_done(self):
        for t in download_manager.get_all():
            if t.status in (DownloadStatus.DONE, DownloadStatus.CANCELLED):
                download_manager.remove(t.task_id)
                if t.task_id in self._task_rows:
                    try: self._task_rows[t.task_id].destroy()
                    except Exception: pass
                    del self._task_rows[t.task_id]

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def _subscribe(self):
        download_manager.subscribe_update(
            lambda t: self.after(0, lambda: self._on_task_update(t))
        )
        download_manager.subscribe_new(
            lambda t: self.after(0, lambda: self._on_task_new(t))
        )

    def _on_task_new(self, task: DownloadTask):
        self._empty_lbl.pack_forget()
        row = TaskRow(self._list_scroll, task)
        row.pack(fill="x", pady=4)
        self._task_rows[task.task_id] = row
        self._update_pills()

    def _on_task_update(self, task: DownloadTask):
        row = self._task_rows.get(task.task_id)
        if row:
            row.update_task(task)
        self._update_pills()

    def _rebuild_list(self):
        """Rebuild task list according to current filter."""
        f = self._filter_var.get()
        filter_map = {
            "Downloading": [DownloadStatus.DOWNLOADING, DownloadStatus.CONNECTING],
            "Queued":      [DownloadStatus.QUEUED],
            "Done":        [DownloadStatus.DONE],
            "Failed":      [DownloadStatus.ERROR, DownloadStatus.CANCELLED],
        }

        for row in self._task_rows.values():
            try: row.pack_forget()
            except Exception: pass

        tasks = download_manager.get_all()
        if f != "All":
            allowed = filter_map.get(f, [])
            tasks = [t for t in tasks if t.status in allowed]

        if not tasks:
            self._empty_lbl.pack(pady=60)
        else:
            self._empty_lbl.pack_forget()
            for t in tasks:
                row = self._task_rows.get(t.task_id)
                if row:
                    row.pack(fill="x", pady=4)

    def _update_pills(self):
        tasks = download_manager.get_all()
        active  = sum(1 for t in tasks if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONNECTING))
        queued  = sum(1 for t in tasks if t.status == DownloadStatus.QUEUED)
        done    = sum(1 for t in tasks if t.status == DownloadStatus.DONE)
        failed  = sum(1 for t in tasks if t.status in (DownloadStatus.ERROR, DownloadStatus.CANCELLED))

        self._active_pill.configure(text=f"  Active: {active}  ")
        self._queued_pill.configure(text=f"  Queued: {queued}  ")
        self._done_pill.configure(text=f"  Done: {done}  ")
        self._error_pill.configure(text=f"  Failed: {failed}  ")

    # ── Speed Ticker ─────────────────────────────────────────────────────────

    def _start_speed_ticker(self):
        def tick():
            tasks = download_manager.get_active()
            combined = sum(t.speed_bps for t in tasks)
            try:
                self._graph.push(combined)
            except Exception:
                pass
            self.after(1000, tick)

        self.after(1000, tick)

    # ── Add URL Dialog ────────────────────────────────────────────────────────

    def _add_url_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Download")
        dialog.geometry("500x200")
        dialog.resizable(False, False)
        dialog.configure(fg_color=COLORS["bg_elevated"])
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()

        ctk.CTkLabel(dialog, text="Enter download URL",
                     font=FONTS["heading_md"], text_color=COLORS["text_primary"]
                     ).pack(anchor="w", padx=20, pady=(16, 8))

        entry = ctk.CTkEntry(dialog, placeholder_text="https://…",
                              height=42, font=FONTS["body_md"],
                              fg_color=COLORS["bg_card"],
                              border_color=COLORS["border"],
                              text_color=COLORS["text_primary"])
        entry.pack(fill="x", padx=20)

        # Try paste from clipboard
        try:
            import tkinter as tk
            r = tk.Tk(); r.withdraw()
            cb = r.clipboard_get(); r.destroy()
            if cb.startswith("http"):
                entry.insert(0, cb.strip())
        except Exception:
            pass

        def start():
            url = entry.get().strip()
            if url:
                fname = filename_from_url(url)
                download_manager.add(url=url, filename=fname)
                notifications.info(f"Added: {fname[:40]}", "Download Queued")
                dialog.destroy()

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=12)

        ctk.CTkButton(btn_row, text="Start Download", height=40,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      font=FONTS["heading_sm"], command=start).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Cancel", height=40, width=90,
                      fg_color=COLORS["bg_card"], hover_color=COLORS["bg_hover"],
                      font=FONTS["body_md"], text_color=COLORS["text_secondary"],
                      command=dialog.destroy).pack(side="left")

        entry.bind("<Return>", lambda e: start())
