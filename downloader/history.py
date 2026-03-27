"""
Shanu Fx Private Downloader - Download History
Persistent download history stored in JSON.
Author: Shanudha Tirosh
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from core.config import HISTORY_FILE

# ─── History Entry ─────────────────────────────────────────────────────────────

class HistoryEntry:
    def __init__(
        self,
        title:      str,
        url:        str,
        filename:   str,
        filepath:   str,
        fmt_type:   str,  # "video" | "audio" | "file"
        size_bytes: int   = 0,
        duration:   str   = "",
        platform:   str   = "",
        status:     str   = "done",  # "done" | "failed"
        entry_id:   Optional[str] = None,
        timestamp:  Optional[str] = None,
    ):
        self.id        = entry_id or str(uuid.uuid4())[:8]
        self.title     = title
        self.url       = url
        self.filename  = filename
        self.filepath  = filepath
        self.fmt_type  = fmt_type
        self.size_bytes= size_bytes
        self.duration  = duration
        self.platform  = platform
        self.status    = status
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M")

    @property
    def size_str(self) -> str:
        b = self.size_bytes
        if b <= 0:       return "Unknown"
        if b < 1024:     return f"{b} B"
        if b < 1024**2:  return f"{b/1024:.1f} KB"
        if b < 1024**3:  return f"{b/1024**2:.1f} MB"
        return f"{b/1024**3:.2f} GB"

    @property
    def type_icon(self) -> str:
        return {"video": "🎬", "audio": "🎵", "file": "📄"}.get(self.fmt_type, "📄")

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "title":      self.title,
            "url":        self.url,
            "filename":   self.filename,
            "filepath":   self.filepath,
            "fmt_type":   self.fmt_type,
            "size_bytes": self.size_bytes,
            "duration":   self.duration,
            "platform":   self.platform,
            "status":     self.status,
            "timestamp":  self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HistoryEntry":
        return cls(
            title      = d.get("title", ""),
            url        = d.get("url", ""),
            filename   = d.get("filename", ""),
            filepath   = d.get("filepath", ""),
            fmt_type   = d.get("fmt_type", "file"),
            size_bytes = d.get("size_bytes", 0),
            duration   = d.get("duration", ""),
            platform   = d.get("platform", ""),
            status     = d.get("status", "done"),
            entry_id   = d.get("id"),
            timestamp  = d.get("timestamp"),
        )


# ─── History Manager ───────────────────────────────────────────────────────────

class HistoryManager:
    """Manages download history with JSON-backed persistence."""

    MAX_ENTRIES = 500

    def __init__(self):
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r") as f:
                    data = json.load(f)
                self._entries = [HistoryEntry.from_dict(d) for d in data]
            except Exception:
                self._entries = []

    def _save(self):
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(HISTORY_FILE, "w") as f:
                json.dump([e.to_dict() for e in self._entries], f, indent=2)
        except Exception:
            pass

    def add(self, entry: HistoryEntry):
        """Add entry and trim if over limit."""
        self._entries.insert(0, entry)
        if len(self._entries) > self.MAX_ENTRIES:
            self._entries = self._entries[:self.MAX_ENTRIES]
        self._save()

    def remove(self, entry_id: str):
        self._entries = [e for e in self._entries if e.id != entry_id]
        self._save()

    def clear(self):
        self._entries.clear()
        self._save()

    def get_all(self) -> List[HistoryEntry]:
        return list(self._entries)

    def filter_by_type(self, fmt_type: str) -> List[HistoryEntry]:
        return [e for e in self._entries if e.fmt_type == fmt_type]

    def search(self, query: str) -> List[HistoryEntry]:
        q = query.lower()
        return [e for e in self._entries if q in e.title.lower() or q in e.filename.lower()]

    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def total_size(self) -> int:
        return sum(e.size_bytes for e in self._entries)


# Singleton
history_manager = HistoryManager()
