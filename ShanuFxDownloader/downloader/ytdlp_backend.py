"""
Shanu Fx Private Downloader - yt-dlp Backend
Handles all social media downloading via yt-dlp Python API.
Author: Shanudha Tirosh
"""

import os
import re
import json
import threading
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Dict, List, Any
from dataclasses import dataclass, field

from core.config import config

# ─── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class VideoInfo:
    """Holds metadata about a video fetched from yt-dlp."""
    title:       str      = ""
    uploader:    str      = ""
    duration:    int      = 0       # seconds
    view_count:  int      = 0
    thumbnail:   str      = ""      # URL
    webpage_url: str      = ""
    extractor:   str      = ""
    description: str      = ""
    formats:     List[Dict] = field(default_factory=list)

    @property
    def duration_str(self) -> str:
        if self.duration <= 0:
            return "--:--"
        h, rem = divmod(self.duration, 3600)
        m, s   = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    @property
    def platform_name(self) -> str:
        name = self.extractor.lower()
        mapping = {
            "youtube": "YouTube", "tiktok": "TikTok",
            "instagram": "Instagram", "facebook": "Facebook",
            "twitter": "Twitter/X", "twitch": "Twitch",
            "vimeo": "Vimeo", "dailymotion": "Dailymotion",
        }
        for key, display in mapping.items():
            if key in name:
                return display
        return self.extractor.title()


@dataclass
class DownloadProgress:
    """Represents real-time download progress."""
    status:     str   = "idle"     # idle / downloading / processing / done / error
    percent:    float = 0.0
    speed:      str   = ""
    eta:        str   = ""
    filename:   str   = ""
    total_bytes:int   = 0
    dl_bytes:   int   = 0
    error:      str   = ""


# ─── YtDlpBackend ──────────────────────────────────────────────────────────────

class YtDlpBackend:
    """
    Wraps yt-dlp's Python API for media info extraction and downloading.
    All network operations run on background threads to keep UI responsive.
    """

    def __init__(self):
        self._active_downloads: Dict[str, threading.Thread] = {}

    # ── Info Extraction ───────────────────────────────────────────────────────

    def fetch_info(
        self,
        url: str,
        on_success: Callable[[VideoInfo], None],
        on_error:   Callable[[str], None],
    ):
        """Fetch video metadata asynchronously."""
        def worker():
            try:
                import yt_dlp
                ydl_opts = {
                    "quiet":          True,
                    "no_warnings":    True,
                    "skip_download":  True,
                    "extract_flat":   False,
                    "socket_timeout": 15,
                }
                ffmpeg = config.get("ffmpeg_path", "")
                if ffmpeg:
                    ydl_opts["ffmpeg_location"] = str(Path(ffmpeg).parent)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    raw = ydl.extract_info(url, download=False)

                if not raw:
                    on_error("No info returned — check the URL")
                    return

                # Parse formats into readable list
                formats = []
                for fmt in raw.get("formats", []):
                    ext  = fmt.get("ext", "?")
                    vcodec = fmt.get("vcodec", "none")
                    acodec = fmt.get("acodec", "none")
                    height = fmt.get("height")
                    abr    = fmt.get("abr")
                    tbr    = fmt.get("tbr")
                    fid    = fmt.get("format_id", "")

                    if vcodec != "none" and height:
                        label = f"{height}p  [{ext}]"
                        ftype = "video"
                    elif acodec != "none" and vcodec == "none":
                        bitrate = int(abr or tbr or 0)
                        label = f"Audio {bitrate}kbps  [{ext}]"
                        ftype = "audio"
                    else:
                        continue  # skip muxed/unknown

                    formats.append({
                        "id":     fid,
                        "label":  label,
                        "type":   ftype,
                        "height": height or 0,
                        "ext":    ext,
                    })

                # Sort: video by resolution desc, audio by bitrate desc
                formats.sort(key=lambda x: (-x.get("height", 0)))

                info = VideoInfo(
                    title       = raw.get("title", "Unknown Title"),
                    uploader    = raw.get("uploader", raw.get("channel", "Unknown")),
                    duration    = raw.get("duration", 0) or 0,
                    view_count  = raw.get("view_count", 0) or 0,
                    thumbnail   = raw.get("thumbnail", ""),
                    webpage_url = raw.get("webpage_url", url),
                    extractor   = raw.get("extractor", ""),
                    description = (raw.get("description") or "")[:300],
                    formats     = formats,
                )
                on_success(info)

            except Exception as e:
                on_error(str(e))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # ── Download ──────────────────────────────────────────────────────────────

    def download(
        self,
        url:         str,
        output_dir:  str,
        fmt_type:    str = "video",   # "video" | "audio"
        quality:     str = "best",    # "best" | "1080p" | etc.
        bitrate:     str = "192kbps", # for audio
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
        on_done:     Optional[Callable[[str], None]] = None,
        on_error:    Optional[Callable[[str], None]] = None,
        download_id: str = "",
    ):
        """Start a yt-dlp download in background."""
        def worker():
            try:
                import yt_dlp
                progress = DownloadProgress()

                # Build format selector
                fmt_selector = self._build_format_selector(fmt_type, quality, bitrate)

                # Build postprocessors
                postprocessors = []
                if fmt_type == "audio":
                    br = re.sub(r"[^0-9]", "", bitrate) or "192"
                    postprocessors.append({
                        "key":            "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": br,
                    })
                else:
                    postprocessors.append({"key": "FFmpegVideoConvertor", "preferedformat": "mp4"})

                def _hook(d: dict):
                    status = d.get("status", "")
                    if status == "downloading":
                        progress.status  = "downloading"
                        progress.percent = float(
                            re.sub(r"[^0-9.]", "", d.get("_percent_str", "0") or "0") or 0
                        )
                        progress.speed   = d.get("_speed_str", "")
                        progress.eta     = d.get("_eta_str", "")
                        progress.dl_bytes    = d.get("downloaded_bytes", 0)
                        progress.total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                        if on_progress:
                            on_progress(progress)

                    elif status == "finished":
                        progress.status  = "processing"
                        progress.percent = 100.0
                        progress.filename = d.get("filename", "")
                        if on_progress:
                            on_progress(progress)

                    elif status == "error":
                        progress.status = "error"
                        progress.error  = str(d.get("error", "Unknown error"))
                        if on_progress:
                            on_progress(progress)

                ydl_opts = {
                    "format":           fmt_selector,
                    "outtmpl":          os.path.join(output_dir, "%(title)s.%(ext)s"),
                    "quiet":            True,
                    "no_warnings":      True,
                    "progress_hooks":   [_hook],
                    "postprocessors":   postprocessors,
                    "merge_output_format": "mp4" if fmt_type == "video" else None,
                    "writethumbnail":   False,
                    "socket_timeout":   30,
                    "retries":          3,
                }

                # Remove None values
                ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}

                ffmpeg = config.get("ffmpeg_path", "")
                if ffmpeg:
                    ydl_opts["ffmpeg_location"] = str(Path(ffmpeg).parent)

                # Ensure output dir exists
                Path(output_dir).mkdir(parents=True, exist_ok=True)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                progress.status  = "done"
                progress.percent = 100.0
                if on_progress:
                    on_progress(progress)
                if on_done:
                    on_done(progress.filename)

            except Exception as e:
                if on_error:
                    on_error(str(e))

        t = threading.Thread(target=worker, daemon=True, name=f"ytdlp-{download_id}")
        if download_id:
            self._active_downloads[download_id] = t
        t.start()

    def _build_format_selector(self, fmt_type: str, quality: str, bitrate: str) -> str:
        """Build yt-dlp format selector string."""
        if fmt_type == "audio":
            return "bestaudio/best"

        quality_map = {
            "best":  "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "2160p": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
            "1440p": "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "720p":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "480p":  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
            "360p":  "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]",
            "240p":  "bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/best[height<=240]",
            "144p":  "bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/best[height<=144]",
        }
        return quality_map.get(quality, quality_map["best"])

    # ── Thumbnail Downloader ─────────────────────────────────────────────────

    def fetch_thumbnail(
        self,
        url:        str,
        on_success: Callable[[bytes], None],
        on_error:   Optional[Callable[[str], None]] = None,
    ):
        """Download thumbnail bytes asynchronously."""
        def worker():
            try:
                req = urllib.request.urlopen(url, timeout=10)
                data = req.read()
                on_success(data)
            except Exception as e:
                if on_error:
                    on_error(str(e))

        threading.Thread(target=worker, daemon=True).start()


# Singleton
ytdlp_backend = YtDlpBackend()
