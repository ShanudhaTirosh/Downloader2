"""
Shanu Fx Private Downloader - System Setup Module
Handles auto-installation of FFmpeg, yt-dlp, and other dependencies.
Author: Shanudha Tirosh
"""

import os
import sys
import shutil
import zipfile
import platform
import subprocess
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from core.config import config, DATA_DIR, FFMPEG_DIR, YTDLP_PATH

# ─── Download URLs ─────────────────────────────────────────────────────────────
YTDLP_URL_WIN   = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
YTDLP_URL_LINUX = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
YTDLP_URL_MAC   = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos"

FFMPEG_URL_WIN = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


class SetupManager:
    """
    Manages first-run setup: downloads FFmpeg and yt-dlp binaries,
    and verifies the environment is ready for use.
    """

    def __init__(self):
        self._is_windows = platform.system() == "Windows"
        self._is_linux   = platform.system() == "Linux"
        self._is_mac     = platform.system() == "Darwin"
        self._on_progress: Optional[Callable] = None
        self._on_status:   Optional[Callable] = None
        self._on_complete: Optional[Callable] = None
        self._on_error:    Optional[Callable] = None

    # ── Callback Registration ─────────────────────────────────────────────────

    def on_progress(self, cb: Callable): self._on_progress = cb
    def on_status(self, cb: Callable):   self._on_status   = cb
    def on_complete(self, cb: Callable): self._on_complete = cb
    def on_error(self, cb: Callable):    self._on_error    = cb

    def _progress(self, value: float): 
        if self._on_progress: self._on_progress(value)

    def _status(self, msg: str):
        if self._on_status: self._on_status(msg)

    def _complete(self):
        if self._on_complete: self._on_complete()

    def _error(self, msg: str):
        if self._on_error: self._on_error(msg)

    # ── Check Methods ─────────────────────────────────────────────────────────

    def ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available on PATH or in data dir."""
        if shutil.which("ffmpeg"):
            return True
        ffmpeg_local = FFMPEG_DIR / ("ffmpeg.exe" if self._is_windows else "ffmpeg")
        return ffmpeg_local.exists()

    def ytdlp_available(self) -> bool:
        """Check if yt-dlp is installed (pip package or binary)."""
        try:
            import yt_dlp  # noqa
            return True
        except ImportError:
            pass
        if YTDLP_PATH.exists():
            return True
        if shutil.which("yt-dlp"):
            return True
        return False

    def get_ffmpeg_path(self) -> str:
        """Return the path to the ffmpeg executable."""
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg
        local = FFMPEG_DIR / ("ffmpeg.exe" if self._is_windows else "ffmpeg")
        if local.exists():
            return str(local)
        return "ffmpeg"

    def get_ytdlp_path(self) -> str:
        """Return the path to the yt-dlp executable/module."""
        if YTDLP_PATH.exists():
            return str(YTDLP_PATH)
        sys_ytdlp = shutil.which("yt-dlp")
        if sys_ytdlp:
            return sys_ytdlp
        return "yt-dlp"

    def needs_setup(self) -> bool:
        """Return True if any required component is missing."""
        return not (self.ffmpeg_available() and self.ytdlp_available())

    # ── Installation Methods ──────────────────────────────────────────────────

    def run_setup(self):
        """Run setup in a background thread."""
        thread = threading.Thread(target=self._setup_worker, daemon=True)
        thread.start()

    def _setup_worker(self):
        """Main setup worker — installs all missing components."""
        try:
            self._status("Checking system components...")
            self._progress(0.0)

            # ── Step 1: Install yt-dlp ──────────────────────────────────────
            if not self.ytdlp_available():
                self._status("Installing yt-dlp...")
                self._install_ytdlp()
            else:
                self._status("✓ yt-dlp is ready")
            self._progress(0.4)

            # ── Step 2: Install FFmpeg ──────────────────────────────────────
            if not self.ffmpeg_available():
                self._status("Downloading FFmpeg binaries...")
                self._install_ffmpeg()
            else:
                self._status("✓ FFmpeg is ready")
            self._progress(0.9)

            # ── Step 3: Save paths to config ───────────────────────────────
            config.set("ffmpeg_path", self.get_ffmpeg_path())
            config.set("ytdlp_path",  self.get_ytdlp_path())
            config.set("first_run",   False)

            self._progress(1.0)
            self._status("✓ All components ready — launching app...")
            self._complete()

        except Exception as e:
            self._error(f"Setup failed: {e}")

    def _install_ytdlp(self):
        """Try pip install first, fallback to binary download."""
        try:
            # Try pip install
            self._status("Installing yt-dlp via pip...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "--upgrade", "yt-dlp"],
                check=True,
                capture_output=True,
            )
            self._status("✓ yt-dlp installed via pip")
            return
        except Exception:
            pass

        # Fallback: download binary
        self._status("Downloading yt-dlp binary...")
        url = (YTDLP_URL_WIN if self._is_windows
               else YTDLP_URL_MAC if self._is_mac
               else YTDLP_URL_LINUX)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._download_file(url, YTDLP_PATH)

        # Make executable on Unix
        if not self._is_windows:
            os.chmod(YTDLP_PATH, 0o755)
        self._status("✓ yt-dlp binary downloaded")

    def _install_ffmpeg(self):
        """Download and extract FFmpeg."""
        FFMPEG_DIR.mkdir(parents=True, exist_ok=True)

        if self._is_windows:
            zip_path = DATA_DIR / "ffmpeg.zip"
            self._status("Downloading FFmpeg (this may take a moment)...")
            self._download_file(FFMPEG_URL_WIN, zip_path)

            self._status("Extracting FFmpeg...")
            with zipfile.ZipFile(zip_path, "r") as z:
                for member in z.namelist():
                    # Extract only the bin/*.exe files
                    if "bin/ffmpeg.exe" in member or "bin/ffprobe.exe" in member:
                        filename = Path(member).name
                        with z.open(member) as src:
                            with open(FFMPEG_DIR / filename, "wb") as dst:
                                shutil.copyfileobj(src, dst)
            zip_path.unlink(missing_ok=True)
            self._status("✓ FFmpeg extracted")

        else:
            # On Linux/Mac, guide user to install via package manager
            self._status("⚠ Please install FFmpeg via your package manager")
            self._status("  Linux: sudo apt install ffmpeg")
            self._status("  Mac:   brew install ffmpeg")

    def _download_file(self, url: str, dest: Path, chunk_size: int = 65536):
        """Download a file with progress tracking."""
        try:
            req = urllib.request.urlopen(url, timeout=30)
            total = int(req.headers.get("Content-Length", 0))
            downloaded = 0

            with open(dest, "wb") as f:
                while True:
                    chunk = req.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = (downloaded / total) * 0.4 + 0.4  # map to 40-80%
                        self._progress(min(pct, 0.85))
        except Exception as e:
            raise RuntimeError(f"Failed to download {url}: {e}")


# Singleton setup manager
setup_manager = SetupManager()
