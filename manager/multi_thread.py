"""
Shanu Fx Private Downloader - Multi-Threaded Download Engine
IDM-style HTTP downloader with chunking, resume support, and speed tracking.
Author: Shanudha Tirosh
"""

import os
import time
import uuid
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from core.config import config, RETRY_ATTEMPTS, RETRY_DELAY


class DownloadStatus(Enum):
    QUEUED     = "queued"
    CONNECTING = "connecting"
    DOWNLOADING= "downloading"
    PAUSED     = "paused"
    PROCESSING = "processing"
    DONE       = "done"
    ERROR      = "error"
    CANCELLED  = "cancelled"


@dataclass
class DownloadTask:
    """Represents a single file download task."""
    url:        str
    filename:   str
    output_dir: str
    task_id:    str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status:     DownloadStatus = DownloadStatus.QUEUED

    # Progress
    total_bytes:    int   = 0
    done_bytes:     int   = 0
    speed_bps:      float = 0.0
    eta_seconds:    float = 0.0
    percent:        float = 0.0

    # Metadata
    category:   str   = "files"    # "videos" | "music" | "documents" | "programs" | "files"
    error_msg:  str   = ""
    filepath:   str   = ""         # Final file path after completion
    created_at: float = field(default_factory=time.time)
    chunks_total: int = 0
    chunks_done:  int = 0
    supports_resume: bool = False

    @property
    def speed_str(self) -> str:
        s = self.speed_bps
        if s <= 0:          return "—"
        if s < 1024:        return f"{s:.0f} B/s"
        if s < 1024**2:     return f"{s/1024:.1f} KB/s"
        return f"{s/1024**2:.2f} MB/s"

    @property
    def eta_str(self) -> str:
        if self.eta_seconds <= 0:   return "—"
        s = int(self.eta_seconds)
        if s < 60:   return f"{s}s"
        if s < 3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"

    @property
    def size_str(self) -> str:
        b = self.total_bytes
        if b <= 0:       return "Unknown"
        if b < 1024:     return f"{b} B"
        if b < 1024**2:  return f"{b/1024:.1f} KB"
        if b < 1024**3:  return f"{b/1024**2:.1f} MB"
        return f"{b/1024**3:.2f} GB"

    @property
    def done_size_str(self) -> str:
        b = self.done_bytes
        if b <= 0:       return "0 B"
        if b < 1024:     return f"{b} B"
        if b < 1024**2:  return f"{b/1024:.1f} KB"
        if b < 1024**3:  return f"{b/1024**2:.1f} MB"
        return f"{b/1024**3:.2f} GB"


# ─── Chunk Worker ──────────────────────────────────────────────────────────────

class ChunkWorker:
    """Downloads a specific byte range of a file."""

    def __init__(
        self,
        url:        str,
        filepath:   str,
        start:      int,
        end:        int,
        chunk_idx:  int,
        on_bytes:   Callable[[int], None],
        stop_event: threading.Event,
    ):
        self.url        = url
        self.filepath   = filepath   # Temp chunk file path
        self.start      = start
        self.end        = end
        self.chunk_idx  = chunk_idx
        self.on_bytes   = on_bytes
        self.stop_event = stop_event
        self.error      = None

    def run(self):
        """Download the chunk with retry logic."""
        for attempt in range(RETRY_ATTEMPTS):
            if self.stop_event.is_set():
                return
            try:
                headers = {
                    "Range":      f"bytes={self.start}-{self.end}",
                    "User-Agent": "Mozilla/5.0 ShanuFxDownloader/1.0",
                }
                req = urllib.request.Request(self.url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    with open(self.filepath, "wb") as f:
                        while not self.stop_event.is_set():
                            chunk = resp.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                            self.on_bytes(len(chunk))
                return  # success
            except Exception as e:
                self.error = str(e)
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY)


# ─── Multi-Thread Downloader ───────────────────────────────────────────────────

class MultiThreadDownloader:
    """
    Downloads a file using multiple threads for speed.
    Falls back to single-thread if server doesn't support Range requests.
    """

    SPEED_WINDOW = 2.0  # seconds for speed averaging

    def __init__(self, task: DownloadTask):
        self.task         = task
        self._stop        = threading.Event()
        self._pause       = threading.Event()
        self._pause.set()  # Not paused initially
        self._lock        = threading.Lock()
        self._speed_samples: List[tuple] = []  # (timestamp, bytes)

        # Callbacks
        self.on_progress: Optional[Callable[[DownloadTask], None]] = None
        self.on_done:     Optional[Callable[[DownloadTask], None]] = None
        self.on_error:    Optional[Callable[[DownloadTask, str], None]] = None

    def start(self):
        threading.Thread(target=self._run, daemon=True, name=f"dl-{self.task.task_id}").start()

    def pause(self):
        self._pause.clear()
        self.task.status = DownloadStatus.PAUSED
        self._notify_progress()

    def resume(self):
        self._pause.set()
        self.task.status = DownloadStatus.DOWNLOADING
        self._notify_progress()

    def cancel(self):
        self._stop.set()
        self._pause.set()
        self.task.status = DownloadStatus.CANCELLED

    def _add_bytes(self, n: int):
        """Thread-safe byte counter update."""
        now = time.time()
        with self._lock:
            self.task.done_bytes += n
            self._speed_samples.append((now, n))
            # Keep only last SPEED_WINDOW seconds
            cutoff = now - self.SPEED_WINDOW
            self._speed_samples = [(t, b) for t, b in self._speed_samples if t >= cutoff]
            total_b = sum(b for _, b in self._speed_samples)
            dt = now - self._speed_samples[0][0] if len(self._speed_samples) > 1 else 1
            self.task.speed_bps = total_b / max(dt, 0.001)
            if self.task.total_bytes > 0:
                self.task.percent = (self.task.done_bytes / self.task.total_bytes) * 100
                rem = self.task.total_bytes - self.task.done_bytes
                self.task.eta_seconds = rem / max(self.task.speed_bps, 1)

    def _notify_progress(self):
        if self.on_progress:
            self.on_progress(self.task)

    def _run(self):
        """Main download logic."""
        try:
            task = self.task
            task.status = DownloadStatus.CONNECTING
            self._notify_progress()

            out_dir = Path(task.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            filepath = out_dir / task.filename
            task.filepath = str(filepath)

            # ── Head request to get size & check resume support ───────────
            head_req = urllib.request.Request(
                task.url,
                method="HEAD",
                headers={"User-Agent": "Mozilla/5.0 ShanuFxDownloader/1.0"},
            )
            try:
                head = urllib.request.urlopen(head_req, timeout=10)
                total = int(head.headers.get("Content-Length", 0))
                accepts_ranges = head.headers.get("Accept-Ranges", "").lower() == "bytes"
            except Exception:
                total = 0
                accepts_ranges = False

            task.total_bytes = total
            task.supports_resume = accepts_ranges
            task.status = DownloadStatus.DOWNLOADING

            num_threads = config.get("max_threads", 8)
            if total <= 0 or not accepts_ranges or num_threads <= 1:
                # ── Single-thread fallback ─────────────────────────────────
                self._single_thread_download(filepath)
            else:
                # ── Multi-thread chunked download ──────────────────────────
                self._multi_thread_download(filepath, total, num_threads)

            if self._stop.is_set():
                task.status = DownloadStatus.CANCELLED
                return

            task.status  = DownloadStatus.DONE
            task.percent = 100.0
            self._notify_progress()
            if self.on_done:
                self.on_done(task)

        except Exception as e:
            self.task.status    = DownloadStatus.ERROR
            self.task.error_msg = str(e)
            self._notify_progress()
            if self.on_error:
                self.on_error(self.task, str(e))

    def _single_thread_download(self, filepath: Path):
        """Stream download without Range support."""
        req = urllib.request.Request(
            self.task.url,
            headers={"User-Agent": "Mozilla/5.0 ShanuFxDownloader/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(filepath, "wb") as f:
                while not self._stop.is_set():
                    self._pause.wait()
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    self._add_bytes(len(chunk))
                    self._notify_progress()

    def _multi_thread_download(self, filepath: Path, total: int, num_threads: int):
        """Chunked multi-thread download, then merge."""
        chunk_size = total // num_threads
        tmp_dir    = filepath.parent / f".tmp_{filepath.stem}"
        tmp_dir.mkdir(exist_ok=True)

        workers = []
        threads = []
        for i in range(num_threads):
            start = i * chunk_size
            end   = (total - 1) if i == num_threads - 1 else (start + chunk_size - 1)
            tmp_file = tmp_dir / f"chunk_{i:03d}"
            w = ChunkWorker(
                url       = self.task.url,
                filepath  = str(tmp_file),
                start     = start,
                end       = end,
                chunk_idx = i,
                on_bytes  = self._add_bytes,
                stop_event= self._stop,
            )
            workers.append(w)
            t = threading.Thread(target=w.run, daemon=True)
            threads.append(t)

        # Start with progress reporting
        for t in threads:
            t.start()
        self.task.chunks_total = num_threads

        # Poll until done, respecting pause
        while any(t.is_alive() for t in threads):
            if self._stop.is_set():
                for t in threads:
                    t.join(timeout=1)
                return
            self._pause.wait()
            self.task.chunks_done = sum(1 for w in workers if not threads[workers.index(w)].is_alive())
            self._notify_progress()
            time.sleep(0.15)

        # Check for chunk errors
        errors = [w.error for w in workers if w.error]
        if errors:
            raise RuntimeError(f"Chunk errors: {errors[0]}")

        # Merge chunks
        self.task.status = DownloadStatus.PROCESSING
        self._notify_progress()
        with open(filepath, "wb") as out:
            for i in range(num_threads):
                chunk_file = tmp_dir / f"chunk_{i:03d}"
                with open(chunk_file, "rb") as f:
                    out.write(f.read())
                chunk_file.unlink()

        # Cleanup temp dir
        try:
            tmp_dir.rmdir()
        except Exception:
            pass
