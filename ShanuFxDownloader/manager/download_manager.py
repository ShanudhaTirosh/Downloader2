"""
Shanu Fx Private Downloader - Queue & Download Manager
Manages a queue of HTTP download tasks, limits concurrency, and categorizes files.
Author: Shanudha Tirosh
"""

import os
import re
import uuid
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional

from core.config import config, DOWNLOAD_DIR
from manager.multi_thread import MultiThreadDownloader, DownloadTask, DownloadStatus

# ─── File Category Detection ───────────────────────────────────────────────────

CATEGORY_PATTERNS = {
    "videos":    r"\.(mp4|mkv|avi|mov|webm|flv|wmv|m4v)$",
    "music":     r"\.(mp3|aac|flac|wav|ogg|m4a|wma|opus)$",
    "documents": r"\.(pdf|docx|xlsx|pptx|txt|csv|odt|epub|mobi)$",
    "programs":  r"\.(exe|msi|dmg|deb|rpm|apk|zip|rar|7z|tar\.gz|tar\.xz)$",
}


def detect_category(filename: str) -> str:
    name_lower = filename.lower()
    for cat, pattern in CATEGORY_PATTERNS.items():
        if re.search(pattern, name_lower):
            return cat
    return "files"


def filename_from_url(url: str) -> str:
    """Extract a reasonable filename from a URL."""
    path = url.split("?")[0].rstrip("/")
    name = path.split("/")[-1]
    name = re.sub(r"[<>:\"/\\|?*]", "_", name)
    return name or "download"


# ─── Download Manager ──────────────────────────────────────────────────────────

class DownloadManager:
    """
    Central manager for all HTTP download tasks.
    - Queues tasks and limits concurrent downloads
    - Tracks all active/completed/failed downloads
    - Fires callbacks on state changes
    """

    MAX_CONCURRENT = 3  # default max parallel downloads

    def __init__(self):
        self._tasks: Dict[str, DownloadTask]   = {}
        self._downloaders: Dict[str, MultiThreadDownloader] = {}
        self._queue: List[str]                 = []      # task IDs waiting to start
        self._lock = threading.Lock()

        # Callbacks fired on any task change — UI subscribes here
        self._on_update: List[Callable[[DownloadTask], None]] = []
        self._on_new:    List[Callable[[DownloadTask], None]] = []

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def subscribe_update(self, cb: Callable[[DownloadTask], None]):
        self._on_update.append(cb)

    def subscribe_new(self, cb: Callable[[DownloadTask], None]):
        self._on_new.append(cb)

    def _fire_update(self, task: DownloadTask):
        for cb in self._on_update:
            try: cb(task)
            except Exception: pass

    def _fire_new(self, task: DownloadTask):
        for cb in self._on_new:
            try: cb(task)
            except Exception: pass

    # ── Task Management ───────────────────────────────────────────────────────

    def add(
        self,
        url:       str,
        filename:  Optional[str] = None,
        output_dir:Optional[str] = None,
        auto_start:bool = True,
    ) -> DownloadTask:
        """Add a new download task."""
        fname   = filename   or filename_from_url(url)
        out_dir = output_dir or str(config.get("download_dir", str(DOWNLOAD_DIR)))
        cat     = detect_category(fname)

        task = DownloadTask(
            url        = url,
            filename   = fname,
            output_dir = out_dir,
            category   = cat,
        )

        with self._lock:
            self._tasks[task.task_id] = task
            if auto_start:
                self._queue.append(task.task_id)

        self._fire_new(task)
        if auto_start:
            self._process_queue()
        return task

    def pause(self, task_id: str):
        dl = self._downloaders.get(task_id)
        if dl:
            dl.pause()

    def resume(self, task_id: str):
        task = self._tasks.get(task_id)
        if not task:
            return
        if task.status == DownloadStatus.PAUSED:
            dl = self._downloaders.get(task_id)
            if dl:
                dl.resume()
        elif task.status in (DownloadStatus.QUEUED, DownloadStatus.ERROR):
            with self._lock:
                if task_id not in self._queue:
                    self._queue.append(task_id)
            self._process_queue()

    def cancel(self, task_id: str):
        dl = self._downloaders.get(task_id)
        if dl:
            dl.cancel()
        with self._lock:
            if task_id in self._queue:
                self._queue.remove(task_id)
            task = self._tasks.get(task_id)
            if task:
                task.status = DownloadStatus.CANCELLED
                self._fire_update(task)

    def remove(self, task_id: str):
        self.cancel(task_id)
        with self._lock:
            self._tasks.pop(task_id, None)
            self._downloaders.pop(task_id, None)

    def retry(self, task_id: str):
        """Retry a failed or cancelled download."""
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status     = DownloadStatus.QUEUED
        task.done_bytes = 0
        task.percent    = 0.0
        task.error_msg  = ""
        with self._lock:
            if task_id not in self._queue:
                self._queue.insert(0, task_id)
        self._process_queue()

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_all(self) -> List[DownloadTask]:
        return list(self._tasks.values())

    def get_active(self) -> List[DownloadTask]:
        return [t for t in self._tasks.values()
                if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONNECTING)]

    def get_by_category(self, cat: str) -> List[DownloadTask]:
        return [t for t in self._tasks.values() if t.category == cat]

    def active_count(self) -> int:
        return len(self.get_active())

    # ── Queue Processing ──────────────────────────────────────────────────────

    def _process_queue(self):
        """Start queued tasks if under the concurrency limit."""
        max_c = config.get("max_threads", self.MAX_CONCURRENT)
        # Rough cap: allow up to max_threads/4 concurrent tasks, min 1
        concurrent = max(1, max_c // 4)

        threading.Thread(target=self._queue_worker, args=(concurrent,), daemon=True).start()

    def _queue_worker(self, concurrent: int):
        with self._lock:
            while self._queue and self.active_count() < concurrent:
                task_id = self._queue.pop(0)
                task    = self._tasks.get(task_id)
                if task and task.status == DownloadStatus.QUEUED:
                    self._start_task(task)

    def _start_task(self, task: DownloadTask):
        dl = MultiThreadDownloader(task)
        self._downloaders[task.task_id] = dl

        def on_progress(t: DownloadTask):
            self._fire_update(t)
            if t.status == DownloadStatus.DONE:
                # Start next in queue
                self._process_queue()

        def on_done(t: DownloadTask):
            self._fire_update(t)
            self._process_queue()

        def on_error(t: DownloadTask, err: str):
            self._fire_update(t)
            self._process_queue()

        dl.on_progress = on_progress
        dl.on_done     = on_done
        dl.on_error    = on_error
        dl.start()


# Singleton
download_manager = DownloadManager()
