"""
Shanu Fx Private Downloader - Shared Widget Library
Reusable UI components: gradient frames, icon buttons, badges, cards.
Author: Shanudha Tirosh
"""

import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from core.config import COLORS, FONTS


# ─── Gradient Canvas Frame ────────────────────────────────────────────────────

class GradientFrame(tk.Canvas):
    """
    A canvas that draws a linear gradient from `color1` to `color2`.
    Use as a background behind other widgets.
    """

    def __init__(self, parent, color1: str, color2: str,
                 direction: str = "horizontal", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        self._c1 = color1
        self._c2 = color2
        self._dir = direction
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("gradient")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 2 or h < 2:
            return

        r1, g1, b1 = self._hex_to_rgb(self._c1)
        r2, g2, b2 = self._hex_to_rgb(self._c2)

        steps = w if self._dir == "horizontal" else h
        for i in range(steps):
            t = i / steps
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            color = f"#{r:02x}{g:02x}{b:02x}"
            if self._dir == "horizontal":
                self.create_line(i, 0, i, h, fill=color, tags="gradient")
            else:
                self.create_line(0, i, w, i, fill=color, tags="gradient")

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ─── Animated Button ──────────────────────────────────────────────────────────

class AnimatedButton(ctk.CTkButton):
    """
    A button that smoothly scales/brightens on hover.
    Wraps standard CTkButton with extra animation hooks.
    """

    def __init__(self, parent, **kwargs):
        self._orig_fg = kwargs.get("fg_color", COLORS["accent"])
        super().__init__(parent, **kwargs)
        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, _e=None):
        self.configure(font=(self.cget("font")[0],
                              self.cget("font")[1] + 0))  # trigger repaint

    def _on_leave(self, _e=None):
        pass


# ─── Icon Label ───────────────────────────────────────────────────────────────

class IconLabel(ctk.CTkFrame):
    """
    Displays a colored icon badge + text label side-by-side.
    Usage: IconLabel(parent, icon="⬇", text="720p", accent=COLORS["accent"])
    """

    def __init__(self, parent, icon: str, text: str,
                 accent: str = COLORS["accent"],
                 icon_size: int = 13,
                 text_font: tuple = FONTS["body_sm"],
                 **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text=icon,
            font=("Segoe UI", icon_size),
            text_color=accent,
            width=20,
        ).pack(side="left")

        ctk.CTkLabel(
            self, text=text,
            font=text_font,
            text_color=COLORS["text_primary"],
        ).pack(side="left", padx=(2, 0))


# ─── Status Badge ─────────────────────────────────────────────────────────────

class StatusBadge(ctk.CTkLabel):
    """
    A pill-shaped colored label used to show status (Active, Paused, Done…).
    """

    STATUS_STYLES = {
        "active":      (COLORS["accent_green"], "Active"),
        "downloading": (COLORS["accent"],       "Downloading"),
        "paused":      (COLORS["accent_orange"],"Paused"),
        "done":        (COLORS["accent_green"], "Done"),
        "error":       (COLORS["accent_red"],   "Error"),
        "queued":      (COLORS["text_muted"],   "Queued"),
        "cancelled":   (COLORS["text_muted"],   "Cancelled"),
        "processing":  (COLORS["accent_orange"],"Processing"),
    }

    def __init__(self, parent, status: str = "queued", **kwargs):
        color, label = self.STATUS_STYLES.get(status, (COLORS["text_muted"], status.title()))
        super().__init__(
            parent,
            text=f"  {label}  ",
            font=FONTS["caption"],
            text_color=color,
            fg_color=color + "22",
            corner_radius=6,
            **kwargs,
        )
        self._color = color

    def set_status(self, status: str):
        color, label = self.STATUS_STYLES.get(status, (COLORS["text_muted"], status.title()))
        self.configure(
            text=f"  {label}  ",
            text_color=color,
            fg_color=color + "22",
        )
        self._color = color


# ─── Card Frame ───────────────────────────────────────────────────────────────

class Card(ctk.CTkFrame):
    """
    Standard glassmorphism card used across pages.
    Provides a consistent bordered, rounded container.
    """

    def __init__(self, parent, accent_bar: Optional[str] = None, **kwargs):
        kwargs.setdefault("fg_color", COLORS["bg_card"])
        kwargs.setdefault("corner_radius", 16)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])
        super().__init__(parent, **kwargs)

        if accent_bar:
            bar = ctk.CTkFrame(self, height=3, fg_color=accent_bar, corner_radius=0)
            bar.pack(fill="x", side="top")


# ─── Divider ──────────────────────────────────────────────────────────────────

class Divider(ctk.CTkFrame):
    """Horizontal separator line."""

    def __init__(self, parent, color: str = COLORS["border"], **kwargs):
        super().__init__(parent, height=1, fg_color=color, corner_radius=0, **kwargs)


# ─── Search Entry ─────────────────────────────────────────────────────────────

class SearchEntry(ctk.CTkFrame):
    """
    A search input with a magnifier icon prefix and optional clear button.
    on_change(text) fires with every keystroke.
    """

    def __init__(self, parent, placeholder: str = "Search…",
                 on_change: Optional[Callable[[str], None]] = None,
                 width: int = 260, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_elevated"],
                         corner_radius=10, width=width,
                         border_width=1, border_color=COLORS["border"],
                         **kwargs)
        self.pack_propagate(False)
        self._on_change = on_change

        ctk.CTkLabel(self, text="🔍", font=FONTS["body_sm"],
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(8, 0))

        self._var = tk.StringVar()
        self._var.trace_add("write", self._on_type)

        self._entry = ctk.CTkEntry(
            self, textvariable=self._var,
            placeholder_text=placeholder,
            border_width=0, fg_color="transparent",
            font=FONTS["body_md"], text_color=COLORS["text_primary"],
            width=width - 52,
        )
        self._entry.pack(side="left", fill="y", pady=2)

    def _on_type(self, *_):
        if self._on_change:
            self._on_change(self._var.get())

    def get(self) -> str:
        return self._var.get()

    def clear(self):
        self._var.set("")


# ─── Empty State ──────────────────────────────────────────────────────────────

class EmptyState(ctk.CTkFrame):
    """
    Centered empty-state with icon, title, and optional subtitle.
    Used when a list has no items.
    """

    def __init__(self, parent, icon: str, title: str, subtitle: str = "", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        ctk.CTkLabel(self, text=icon, font=("Segoe UI", 48),
                     text_color=COLORS["text_muted"]).pack(pady=(30, 8))
        ctk.CTkLabel(self, text=title, font=FONTS["heading_md"],
                     text_color=COLORS["text_secondary"]).pack()
        if subtitle:
            ctk.CTkLabel(self, text=subtitle, font=FONTS["body_sm"],
                         text_color=COLORS["text_muted"]).pack(pady=(4, 0))


# ─── Tooltip ─────────────────────────────────────────────────────────────────

class Tooltip:
    """
    Simple hover tooltip for any widget.
    Usage: Tooltip(widget, "This button downloads the file")
    """

    def __init__(self, widget: tk.Widget, text: str):
        self._widget = widget
        self._text   = text
        self._tip:   Optional[tk.Toplevel] = None

        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)
        widget.bind("<Motion>", self._move)

    def _show(self, event=None):
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self._tip,
            text=self._text,
            background=COLORS["bg_elevated"],
            foreground=COLORS["text_primary"],
            font=("Segoe UI", 10),
            relief="flat",
            padx=10, pady=5,
        )
        lbl.pack()

    def _hide(self, _event=None):
        if self._tip:
            self._tip.destroy()
            self._tip = None

    def _move(self, event=None):
        if self._tip:
            x = self._widget.winfo_rootx() + 20
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
            self._tip.wm_geometry(f"+{x}+{y}")
