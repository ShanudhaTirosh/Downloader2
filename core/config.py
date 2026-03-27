"""
Shanu Fx Private Downloader - Configuration Module
Author: Shanudha Tirosh
"""

import os
import json
from pathlib import Path

# ─── App Metadata ──────────────────────────────────────────────────────────────
APP_NAME = "Shanu Fx Private Downloader"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Shanudha Tirosh"
APP_GITHUB = "https://github.com/ShanudhaTirosh"
APP_DESCRIPTION = "A powerful all-in-one media downloader & download manager"

# ─── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path.home() / ".shanufx"
DOWNLOAD_DIR = Path.home() / "Downloads" / "ShanuFx"
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"
FFMPEG_DIR = DATA_DIR / "ffmpeg"
YTDLP_PATH = DATA_DIR / "yt-dlp.exe" if os.name == "nt" else DATA_DIR / "yt-dlp"

# ─── Color Palette (Dark Glassmorphism) ────────────────────────────────────────
COLORS = {
    # Backgrounds
    "bg_primary":    "#0B0B18",
    "bg_secondary":  "#111127",
    "bg_card":       "#161630",
    "bg_elevated":   "#1C1C3A",
    "bg_hover":      "#22224A",

    # Sidebar
    "sidebar_bg":    "#080815",
    "sidebar_hover": "#13133A",
    "sidebar_active":"#1E1E50",

    # Accent Colors
    "accent":        "#7C3AED",   # Primary purple
    "accent_hover":  "#6D28D9",
    "accent_light":  "#A78BFA",
    "accent_2":      "#EC4899",   # Pink accent
    "accent_green":  "#10B981",   # Success
    "accent_orange": "#F59E0B",   # Warning
    "accent_red":    "#EF4444",   # Error/Danger
    "accent_blue":   "#3B82F6",   # Info blue

    # Text
    "text_primary":  "#F1F1FF",
    "text_secondary":"#9090B8",
    "text_muted":    "#5A5A80",
    "text_accent":   "#A78BFA",

    # Borders
    "border":        "#252548",
    "border_light":  "#303060",
    "border_accent": "#7C3AED",

    # Gradients (start/end)
    "grad_start":    "#7C3AED",
    "grad_end":      "#EC4899",
    "grad_blue_start":"#2563EB",
    "grad_blue_end": "#7C3AED",

    # Progress
    "progress_bg":   "#1E1E3A",
    "progress_fill": "#7C3AED",

    # Status
    "status_active": "#10B981",
    "status_paused": "#F59E0B",
    "status_error":  "#EF4444",
    "status_queued": "#6B7280",
}

# ─── Typography ────────────────────────────────────────────────────────────────
FONTS = {
    "heading_xl": ("Segoe UI", 28, "bold"),
    "heading_lg": ("Segoe UI", 22, "bold"),
    "heading_md": ("Segoe UI", 16, "bold"),
    "heading_sm": ("Segoe UI", 13, "bold"),
    "body_lg":    ("Segoe UI", 13),
    "body_md":    ("Segoe UI", 12),
    "body_sm":    ("Segoe UI", 11),
    "caption":    ("Segoe UI", 10),
    "mono":       ("Consolas", 11),
}

# ─── Window Dimensions ─────────────────────────────────────────────────────────
WINDOW_WIDTH  = 1280
WINDOW_HEIGHT = 780
SIDEBAR_WIDTH = 220
TOPBAR_HEIGHT = 60

# ─── Download Settings ─────────────────────────────────────────────────────────
DEFAULT_THREADS   = 8
MAX_THREADS       = 32
CHUNK_SIZE        = 1024 * 1024  # 1 MB chunks
RETRY_ATTEMPTS    = 3
RETRY_DELAY       = 2  # seconds
CLIPBOARD_INTERVAL= 1.0  # seconds

# ─── Supported Formats ─────────────────────────────────────────────────────────
VIDEO_FORMATS = ["mp4", "webm", "mkv", "avi", "mov"]
AUDIO_FORMATS = ["mp3", "aac", "flac", "wav", "ogg", "m4a"]
IMAGE_FORMATS = ["jpg", "jpeg", "png", "gif", "webp"]
DOC_FORMATS   = ["pdf", "docx", "xlsx", "txt", "zip", "rar", "7z", "exe", "msi"]

VIDEO_QUALITIES = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
AUDIO_BITRATES  = ["320kbps", "256kbps", "192kbps", "128kbps", "96kbps"]

# ─── Config Manager ────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "download_dir":        str(DOWNLOAD_DIR),
    "default_format":      "mp4",
    "default_quality":     "best",
    "default_bitrate":     "192kbps",
    "max_threads":         DEFAULT_THREADS,
    "clipboard_detection": True,
    "auto_start_download": False,
    "show_notifications":  True,
    "theme":               "dark",
    "ffmpeg_path":         "",
    "ytdlp_path":          "",
    "first_run":           True,
    "speed_limit_kbps":    0,  # 0 = unlimited
}


class Config:
    """Manages persistent application configuration."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                # Merge with defaults so new keys are always present
                merged = {**DEFAULT_CONFIG, **loaded}
                return merged
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    def save(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self.set(key, value)


# Singleton config instance
config = Config()
