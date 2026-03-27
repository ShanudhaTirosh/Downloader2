"""
Shanu Fx Private Downloader - Notifications
In-app toast notification system.
Author: Shanudha Tirosh
"""

import threading
import time
from typing import Callable, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.config import config


class NotifType(Enum):
    SUCCESS = "success"
    INFO    = "info"
    WARNING = "warning"
    ERROR   = "error"


@dataclass
class Notification:
    message:   str
    title:     str        = ""
    notif_type: NotifType = NotifType.INFO
    duration:  float      = 4.0   # seconds before auto-dismiss
    timestamp: float      = field(default_factory=time.time)
    dismissed: bool       = False

    @property
    def icon(self) -> str:
        return {
            NotifType.SUCCESS: "✓",
            NotifType.INFO:    "ℹ",
            NotifType.WARNING: "⚠",
            NotifType.ERROR:   "✕",
        }.get(self.notif_type, "ℹ")

    @property
    def color(self) -> str:
        from core.config import COLORS
        return {
            NotifType.SUCCESS: COLORS["accent_green"],
            NotifType.INFO:    COLORS["accent_blue"],
            NotifType.WARNING: COLORS["accent_orange"],
            NotifType.ERROR:   COLORS["accent_red"],
        }.get(self.notif_type, COLORS["accent_blue"])


class NotificationManager:
    """Manages in-app notifications with callbacks for the UI."""

    def __init__(self):
        self._listeners: List[Callable[[Notification], None]] = []
        self._history:   List[Notification] = []

    def subscribe(self, cb: Callable[[Notification], None]):
        """Subscribe to new notifications."""
        self._listeners.append(cb)

    def _fire(self, notif: Notification):
        self._history.insert(0, notif)
        if len(self._history) > 50:
            self._history = self._history[:50]
        if config.get("show_notifications", True):
            for cb in self._listeners:
                try: cb(notif)
                except Exception: pass

    def success(self, message: str, title: str = "Success"):
        self._fire(Notification(message, title, NotifType.SUCCESS))

    def info(self, message: str, title: str = "Info"):
        self._fire(Notification(message, title, NotifType.INFO))

    def warning(self, message: str, title: str = "Warning"):
        self._fire(Notification(message, title, NotifType.WARNING))

    def error(self, message: str, title: str = "Error"):
        self._fire(Notification(message, title, NotifType.ERROR))

    def get_recent(self, n: int = 10) -> List[Notification]:
        return self._history[:n]


# Singleton
notifications = NotificationManager()
