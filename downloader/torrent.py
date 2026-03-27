"""
Shanu Fx Private Downloader - Torrent Downloader
Uses libtorrent python bindings for magnet/torrent file support.
Falls back gracefully if libtorrent is not installed.
Author: Shanudha Tirosh
"""

import os
import time
import threading
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass

from core.config import config

# ─── Torrent Status ───────────────────────────────────────────────────────────

@dataclass
class TorrentProgress:
    name:           str   = ""
    status:         str   = "idle"      # idle/checking/downloading/seeding/done/error
    percent:        float = 0.0
    download_rate:  float = 0.0         # bytes/sec
    upload_rate:    float = 0.0
    peers:          int   = 0
    seeds:          int   = 0
    total_bytes:    int   = 0
    done_bytes:     int   = 0
    eta_seconds:    float = 0.0
    error:          str   = ""

    @property
    def speed_str(self) -> str:
        s = self.download_rate
        if s < 1024:      return f"{s:.0f} B/s"
        if s < 1024**2:   return f"{s/1024:.1f} KB/s"
        return f"{s/1024**2:.2f} MB/s"

    @property
    def eta_str(self) -> str:
        s = int(self.eta_seconds)
        if s <= 0:   return "—"
        if s < 60:   return f"{s}s"
        if s < 3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"


# ─── Torrent Downloader ───────────────────────────────────────────────────────

class TorrentDownloader:
    """
    Wraps libtorrent for magnet links and .torrent file downloads.
    Gracefully degrades if libtorrent is unavailable.
    """

    AVAILABLE = False  # Set to True if libtorrent imports OK

    def __init__(self):
        try:
            import libtorrent as lt  # noqa
            TorrentDownloader.AVAILABLE = True
        except ImportError:
            TorrentDownloader.AVAILABLE = False

    def is_available(self) -> bool:
        return self.AVAILABLE

    def download(
        self,
        source:       str,              # magnet link or path to .torrent file
        output_dir:   Optional[str] = None,
        on_progress:  Optional[Callable[[TorrentProgress], None]] = None,
        on_done:      Optional[Callable[[str], None]] = None,
        on_error:     Optional[Callable[[str], None]] = None,
    ):
        """Start a torrent download asynchronously."""
        if not self.AVAILABLE:
            if on_error:
                on_error(
                    "libtorrent is not installed.\n"
                    "Install it with: pip install lbry-libtorrent\n"
                    "Or: pip install python-libtorrent"
                )
            return

        out_dir = output_dir or config.get("download_dir", str(Path.home() / "Downloads" / "ShanuFx"))
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        thread = threading.Thread(
            target=self._worker,
            args=(source, out_dir, on_progress, on_done, on_error),
            daemon=True,
        )
        thread.start()

    def _worker(self, source, out_dir, on_progress, on_done, on_error):
        try:
            import libtorrent as lt

            ses = lt.session()
            ses.listen_on(6881, 6891)

            if source.startswith("magnet:"):
                params = lt.parse_magnet_uri(source)
                params.save_path = out_dir
                handle = ses.add_torrent(params)
            else:
                info = lt.torrent_info(source)
                handle = ses.add_torrent({
                    "ti":        info,
                    "save_path": out_dir,
                })

            progress = TorrentProgress()

            while not handle.is_seed():
                s = handle.status()
                total = s.total_wanted
                done  = s.total_wanted_done

                progress.name          = handle.name() or "Torrent"
                progress.percent       = s.progress * 100
                progress.download_rate = s.download_rate
                progress.upload_rate   = s.upload_rate
                progress.peers         = s.num_peers
                progress.seeds         = s.num_seeds
                progress.total_bytes   = total
                progress.done_bytes    = done
                progress.eta_seconds   = (
                    (total - done) / max(s.download_rate, 1)
                    if s.download_rate > 0 else 0
                )

                state_str = [
                    "queued", "checking", "downloading metadata",
                    "downloading", "finished", "seeding", "allocating",
                    "checking fastresume",
                ]
                progress.status = state_str[s.state] if s.state < len(state_str) else "downloading"

                if on_progress:
                    on_progress(progress)

                time.sleep(1.0)

            progress.status  = "done"
            progress.percent = 100.0
            if on_progress:
                on_progress(progress)
            if on_done:
                on_done(out_dir)

        except Exception as e:
            if on_error:
                on_error(str(e))

    @staticmethod
    def is_torrent_source(s: str) -> bool:
        """Return True if string looks like a magnet link or .torrent file path."""
        return s.startswith("magnet:?") or s.lower().endswith(".torrent")

    @staticmethod
    def install_instructions() -> str:
        return (
            "To enable torrent downloads, install libtorrent:\n\n"
            "  Option 1 (easiest):\n"
            "    pip install lbry-libtorrent\n\n"
            "  Option 2 (Windows binary):\n"
            "    pip install python-libtorrent\n\n"
            "  Option 3 (compile from source):\n"
            "    https://libtorrent.org/python_binding.html"
        )


# Singleton
torrent_downloader = TorrentDownloader()
