"""
Shanu Fx Private Downloader - Clipboard Monitor
Watches clipboard for URLs and fires a callback when one is detected.
Author: Shanudha Tirosh
"""

import re
import threading
import time
from typing import Callable, Optional

from core.config import config, CLIPBOARD_INTERVAL

# Regex to detect URLs
URL_PATTERN = re.compile(
    r"https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}"
    r"\b([-a-zA-Z0-9@:%_+.~#?&/=]*)",
    re.IGNORECASE,
)

# Social media patterns for auto-detection
SOCIAL_PATTERNS = [
    r"youtube\.com/watch", r"youtu\.be/",
    r"tiktok\.com/", r"vm\.tiktok\.com/",
    r"instagram\.com/(p|reel|tv)/",
    r"facebook\.com/(watch|video)",
    r"twitter\.com/.+/status",
    r"x\.com/.+/status",
    r"twitch\.tv/",
    r"vimeo\.com/\d+",
    r"dailymotion\.com/video",
]
SOCIAL_REGEX = re.compile("|".join(SOCIAL_PATTERNS), re.IGNORECASE)


class ClipboardMonitor:
    """
    Background thread that monitors the clipboard for URLs.
    When a URL is detected (optionally filtered to social media),
    it fires the registered callback.
    """

    def __init__(self):
        self._running      = False
        self._last_text    = ""
        self._thread:    Optional[threading.Thread] = None
        self._on_url:    Optional[Callable[[str], None]] = None
        self._social_only  = False

    def set_callback(self, cb: Callable[[str], None]):
        self._on_url = cb

    def set_social_only(self, value: bool):
        """If True, only fire for recognized social media URLs."""
        self._social_only = value

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True, name="clipboard-monitor")
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                if config.get("clipboard_detection", True):
                    text = self._read_clipboard()
                    if text and text != self._last_text:
                        self._last_text = text
                        if self._is_url(text):
                            if not self._social_only or self._is_social(text):
                                if self._on_url:
                                    self._on_url(text.strip())
            except Exception:
                pass
            time.sleep(CLIPBOARD_INTERVAL)

    @staticmethod
    def _read_clipboard() -> str:
        """Read clipboard text, trying multiple methods."""
        # Method 1: tkinter (always available)
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
            return text.strip()
        except Exception:
            pass

        # Method 2: pyperclip (optional dependency)
        try:
            import pyperclip
            return pyperclip.paste() or ""
        except Exception:
            pass

        return ""

    @staticmethod
    def _is_url(text: str) -> bool:
        return bool(URL_PATTERN.match(text.strip()))

    @staticmethod
    def _is_social(url: str) -> bool:
        return bool(SOCIAL_REGEX.search(url))


# Singleton
clipboard_monitor = ClipboardMonitor()
