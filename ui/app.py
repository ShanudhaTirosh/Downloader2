"""
Shanu Fx Private Downloader - Main App Window
Root customtkinter window with sidebar + page routing.
Author: Shanudha Tirosh
"""

import os
import sys
import platform
import threading
import tkinter as tk
from typing import Dict, Optional

import customtkinter as ctk
from PIL import Image, ImageTk

from core.config import (
    config, COLORS, FONTS,
    WINDOW_WIDTH, WINDOW_HEIGHT, SIDEBAR_WIDTH,
    APP_NAME, APP_VERSION,
)
from utils.clipboard  import clipboard_monitor
from utils.notifications import notifications, Notification, NotifType

# Configure CTk appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─── Windows Acrylic Blur ──────────────────────────────────────────────────────

def enable_acrylic_blur(hwnd):
    """Apply Windows 10/11 acrylic blur behind the window."""
    try:
        from ctypes import windll, byref, sizeof, c_int
        windll.dwmapi.DwmEnableBlurBehindWindow(hwnd, byref(c_int(1)))
    except Exception:
        pass


def set_window_rounded(root: tk.Tk):
    """Apply rounded corners on Windows 11."""
    if platform.system() == "Windows":
        try:
            import ctypes
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int),
            )
        except Exception:
            pass


# ─── Toast Notification Widget ────────────────────────────────────────────────

class ToastNotification(ctk.CTkFrame):
    """Animated toast that slides in from the bottom-right."""

    def __init__(self, parent, notif: Notification, **kwargs):
        super().__init__(
            parent,
            width=320, height=72,
            fg_color=COLORS["bg_elevated"],
            corner_radius=14,
            border_width=1,
            border_color=notif.color,
            **kwargs,
        )

        # Icon
        icon_lbl = ctk.CTkLabel(
            self, text=notif.icon, font=("Segoe UI", 18, "bold"),
            text_color=notif.color, width=36,
        )
        icon_lbl.place(x=12, y=16)

        # Title
        title_lbl = ctk.CTkLabel(
            self, text=notif.title or notif.notif_type.value.title(),
            font=FONTS["heading_sm"], text_color=COLORS["text_primary"],
        )
        title_lbl.place(x=52, y=10)

        # Message
        msg_lbl = ctk.CTkLabel(
            self, text=notif.message[:55] + ("…" if len(notif.message) > 55 else ""),
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
        )
        msg_lbl.place(x=52, y=34)

        # Progress bar (auto-dismiss timer)
        self._pb = ctk.CTkProgressBar(self, width=280, height=3, fg_color=COLORS["bg_card"],
                                       progress_color=notif.color, corner_radius=0)
        self._pb.place(x=20, y=66)
        self._pb.set(1.0)

        # Start countdown
        self._duration = notif.duration
        self._start_dismiss()

    def _start_dismiss(self):
        steps  = 60
        delay  = self._duration / steps
        current = [1.0]

        def step():
            current[0] -= 1.0 / steps
            if current[0] <= 0:
                self.destroy()
                return
            try:
                self._pb.set(max(current[0], 0))
                self.after(int(delay * 1000), step)
            except Exception:
                pass

        self.after(int(delay * 1000), step)


# ─── Clipboard Popup ──────────────────────────────────────────────────────────

class ClipboardPopup(ctk.CTkToplevel):
    """Popup asking user to download a detected URL."""

    def __init__(self, parent, url: str, on_yes: callable):
        super().__init__(parent)
        self.title("New URL Detected")
        self.geometry("400x160")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_elevated"])
        self.grab_set()
        self.lift()
        self.focus_force()

        ctk.CTkLabel(
            self, text="🔗  URL Detected in Clipboard",
            font=FONTS["heading_sm"], text_color=COLORS["text_primary"],
        ).pack(pady=(16, 4), padx=20, anchor="w")

        short_url = url if len(url) < 50 else url[:47] + "…"
        ctk.CTkLabel(
            self, text=short_url,
            font=FONTS["body_sm"], text_color=COLORS["text_secondary"],
        ).pack(padx=20, anchor="w")

        ctk.CTkLabel(
            self, text="Start download?",
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
        ).pack(pady=(12, 8))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=4)

        ctk.CTkButton(
            btn_frame, text="Yes, Download", width=140, height=36,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            font=FONTS["body_md"],
            command=lambda: [on_yes(url), self.destroy()],
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="No Thanks", width=120, height=36,
            fg_color=COLORS["bg_card"], hover_color=COLORS["bg_hover"],
            font=FONTS["body_md"], text_color=COLORS["text_secondary"],
            command=self.destroy,
        ).pack(side="left", padx=8)

        # Auto-close after 8 seconds
        self.after(8000, lambda: self.destroy() if self.winfo_exists() else None)


# ─── Main Application Window ──────────────────────────────────────────────────

class App(ctk.CTk):
    """
    Root window for Shanu Fx Private Downloader.
    Manages sidebar navigation, page container, and global notifications.
    """

    def __init__(self):
        super().__init__()

        # ── Window Setup ─────────────────────────────────────────────────────
        self.title(f"{APP_NAME}  v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_primary"])

        # Center on screen
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x = (sw - WINDOW_WIDTH) // 2
        y = (sh - WINDOW_HEIGHT) // 2
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")

        # ── App icon (titlebar + taskbar) ────────────────────────────────────
        self._set_app_icon()

        # Windows enhancements
        if platform.system() == "Windows":
            try:
                self.after(100, lambda: set_window_rounded(self))
            except Exception:
                pass

        # ── Build UI ─────────────────────────────────────────────────────────
        self._pages:       Dict[str, ctk.CTkFrame] = {}
        self._current_page = ""
        self._toasts:      list = []
        self._pending_url:  str = ""

        self._build_layout()
        self._register_pages()

        # ── Start Services ────────────────────────────────────────────────────
        notifications.subscribe(self._on_notification)
        self._start_clipboard_monitor()

        # Navigate to home
        self.navigate("home")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        """Create the two-column layout: sidebar | content."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────────────
        from ui.sidebar import Sidebar
        self._sidebar = Sidebar(self, navigate_cb=self.navigate)
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Content area ─────────────────────────────────────────────────────
        self._content = ctk.CTkFrame(
            self, fg_color=COLORS["bg_primary"], corner_radius=0,
        )
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

    def _register_pages(self):
        """Lazily import and instantiate all pages."""
        from ui.pages.home        import HomePage
        from ui.pages.downloader  import DownloaderPage
        from ui.pages.manager     import ManagerPage
        from ui.pages.history     import HistoryPage
        from ui.pages.torrent     import TorrentPage
        from ui.pages.settings    import SettingsPage
        from ui.pages.about       import AboutPage

        page_map = {
            "home":       HomePage,
            "downloader": DownloaderPage,
            "manager":    ManagerPage,
            "history":    HistoryPage,
            "torrent":    TorrentPage,
            "settings":   SettingsPage,
            "about":      AboutPage,
        }
        for key, PageClass in page_map.items():
            page = PageClass(self._content, app=self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[key] = page

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate(self, page_key: str):
        """Switch the visible page and update sidebar active state."""
        if page_key not in self._pages:
            return
        if self._current_page == page_key:
            return

        # Hide old page
        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].grid_remove()

        # Show new page
        self._pages[page_key].grid()
        self._current_page = page_key
        self._sidebar.set_active(page_key)

    # ── Notifications ─────────────────────────────────────────────────────────

    def _on_notification(self, notif: Notification):
        """Display a toast notification."""
        self.after(0, lambda: self._show_toast(notif))

    def _show_toast(self, notif: Notification):
        try:
            toast = ToastNotification(self, notif)
            # Stack toasts from bottom-right
            offset_y = 20 + len(self._toasts) * 80
            toast.place(relx=1.0, rely=1.0, x=-340, y=-offset_y, anchor="sw")
            self._toasts.append(toast)

            def remove_toast():
                try:
                    if toast in self._toasts:
                        self._toasts.remove(toast)
                    # Restack remaining
                    for i, t in enumerate(self._toasts):
                        offset = 20 + i * 80
                        try: t.place_configure(y=-offset)
                        except Exception: pass
                except Exception:
                    pass

            toast.bind("<Destroy>", lambda e: self.after(100, remove_toast))
        except Exception:
            pass

    # ── Clipboard Monitor ─────────────────────────────────────────────────────

    def _start_clipboard_monitor(self):
        def on_url(url: str):
            self.after(0, lambda: self._on_clipboard_url(url))

        clipboard_monitor.set_callback(on_url)
        clipboard_monitor.start()

    def _on_clipboard_url(self, url: str):
        """Show popup when a URL is detected in clipboard."""
        if not config.get("clipboard_detection", True):
            return
        # Avoid duplicate popups
        if url == self._pending_url:
            return
        self._pending_url = url

        def on_yes(u: str):
            self._pending_url = ""
            # Navigate to downloader and prefill URL
            self.navigate("downloader")
            page = self._pages.get("downloader")
            if page and hasattr(page, "set_url"):
                page.set_url(u)

        ClipboardPopup(self, url, on_yes=on_yes)

    def go_to_downloader(self, url: str = ""):
        """Public method to navigate to downloader with optional URL."""
        self.navigate("downloader")
        page = self._pages.get("downloader")
        if page and url and hasattr(page, "set_url"):
            page.set_url(url)

    def go_to_manager(self):
        self.navigate("manager")

    def _set_app_icon(self):
        """Set the window icon from assets/icon.ico (Windows) or icon_256.png (other)."""
        try:
            assets = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
            if platform.system() == "Windows":
                ico = os.path.join(assets, "icon.ico")
                if os.path.exists(ico):
                    self.iconbitmap(ico)
            else:
                png = os.path.join(assets, "icon_256.png")
                if os.path.exists(png):
                    from PIL import Image, ImageTk
                    img = Image.open(png).resize((64, 64), Image.LANCZOS)
                    self._icon_img = ImageTk.PhotoImage(img)
                    self.iconphoto(True, self._icon_img)
        except Exception:
            pass  # icon is cosmetic — never crash on failure
