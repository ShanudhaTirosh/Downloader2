"""
Shanu Fx Private Downloader - About Page
Developer info, version details, and social links.
Author: Shanudha Tirosh
"""

import webbrowser
from typing import TYPE_CHECKING

import customtkinter as ctk

from core.config import COLORS, FONTS, APP_NAME, APP_VERSION, APP_AUTHOR, APP_GITHUB

if TYPE_CHECKING:
    from ui.app import App

# ─── Feature Pill ─────────────────────────────────────────────────────────────

class FeaturePill(ctk.CTkFrame):
    def __init__(self, parent, icon: str, text: str, **kwargs):
        super().__init__(parent, fg_color=COLORS["accent"] + "22",
                         corner_radius=20, **kwargs)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(padx=12, pady=6)
        ctk.CTkLabel(inner, text=f"{icon}  {text}", font=FONTS["body_sm"],
                     text_color=COLORS["accent_light"]).pack()


class SocialButton(ctk.CTkButton):
    def __init__(self, parent, icon: str, label: str, url: str,
                 color: str = COLORS["accent"], **kwargs):
        super().__init__(
            parent,
            text=f"  {icon}  {label}  ",
            height=44, width=180,
            fg_color=color + "22",
            hover_color=color + "44",
            border_width=1,
            border_color=color,
            font=FONTS["body_md"],
            text_color=COLORS["text_primary"],
            command=lambda: webbrowser.open(url),
            **kwargs,
        )


# ─── About Page ───────────────────────────────────────────────────────────────

class AboutPage(ctk.CTkFrame):
    """About / Developer info page."""

    def __init__(self, parent, app: "App", **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_primary"], corner_radius=0, **kwargs)
        self._app = app
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
        )
        scroll.pack(fill="both", expand=True)

        # ── App Hero section ──────────────────────────────────────────────────
        hero = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=20,
                             border_width=1, border_color=COLORS["border"])
        hero.pack(fill="x", padx=30, pady=(24, 0))

        # App icon + name
        top_row = ctk.CTkFrame(hero, fg_color="transparent")
        top_row.pack(fill="x", padx=28, pady=(24, 8))

        # Big icon
        icon_frame = ctk.CTkFrame(top_row, width=72, height=72, corner_radius=18,
                                   fg_color=COLORS["accent"] + "33")
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="⬡", font=("Segoe UI", 34, "bold"),
                     text_color=COLORS["accent"]).place(relx=0.5, rely=0.5, anchor="center")

        info_col = ctk.CTkFrame(top_row, fg_color="transparent")
        info_col.pack(side="left", padx=(16, 0))
        ctk.CTkLabel(info_col, text=APP_NAME, font=FONTS["heading_lg"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(info_col, text=f"Version {APP_VERSION}  ·  Windows Edition",
                     font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(anchor="w")

        # Version badge
        badge = ctk.CTkFrame(top_row, fg_color=COLORS["accent_green"] + "22",
                              corner_radius=8)
        badge.pack(side="right", anchor="n")
        ctk.CTkLabel(badge, text=f"  v{APP_VERSION}  ", font=FONTS["body_sm"],
                     text_color=COLORS["accent_green"]).pack(padx=4, pady=4)

        # Description
        ctk.CTkLabel(
            hero,
            text=(
                "Shanu Fx Private Downloader is a powerful all-in-one media downloader and download manager.\n"
                "Download from 1000+ sites including YouTube, TikTok, Instagram, Facebook, and more.\n"
                "Combines yt-dlp, FFmpeg, and a custom multi-thread engine for lightning-fast downloads."
            ),
            font=FONTS["body_md"],
            text_color=COLORS["text_secondary"],
            wraplength=700,
            justify="left",
        ).pack(anchor="w", padx=28, pady=(0, 12))

        # Feature pills
        pills_frame = ctk.CTkFrame(hero, fg_color="transparent")
        pills_frame.pack(fill="x", padx=28, pady=(0, 20))

        features = [
            ("⬇", "yt-dlp Powered"),
            ("⚡", "Multi-thread Engine"),
            ("🎬", "1000+ Sites"),
            ("🎵", "MP3 Conversion"),
            ("📋", "Clipboard Detection"),
            ("📊", "Speed Graph"),
            ("🔄", "Pause & Resume"),
            ("🗂", "Queue System"),
        ]
        for icon, text in features:
            FeaturePill(pills_frame, icon=icon, text=text).pack(side="left", padx=(0, 8))

        # ── Developer section ─────────────────────────────────────────────────
        dev_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=20,
                                 border_width=1, border_color=COLORS["border"])
        dev_card.pack(fill="x", padx=30, pady=(14, 0))

        ctk.CTkLabel(dev_card, text="Developer", font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=24, pady=(18, 2))
        ctk.CTkFrame(dev_card, height=1, fg_color=COLORS["border"]).pack(fill="x")

        dev_row = ctk.CTkFrame(dev_card, fg_color="transparent")
        dev_row.pack(fill="x", padx=24, pady=18)

        # Avatar placeholder
        avatar = ctk.CTkFrame(dev_row, width=64, height=64, corner_radius=32,
                               fg_color=COLORS["accent"] + "33")
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text="ST", font=("Segoe UI", 20, "bold"),
                     text_color=COLORS["accent"]).place(relx=0.5, rely=0.5, anchor="center")

        dev_info = ctk.CTkFrame(dev_row, fg_color="transparent")
        dev_info.pack(side="left", padx=(16, 0))
        ctk.CTkLabel(dev_info, text=APP_AUTHOR, font=FONTS["heading_md"],
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(dev_info, text="Full-Stack Developer  ·  Sri Lanka 🇱🇰",
                     font=FONTS["body_md"], text_color=COLORS["text_secondary"]).pack(anchor="w")
        ctk.CTkLabel(dev_info,
                     text="Building powerful tools for the web and beyond.\nOpen source enthusiast and creative coder.",
                     font=FONTS["body_sm"], text_color=COLORS["text_muted"]).pack(anchor="w", pady=(4, 0))

        # Social links
        links_frame = ctk.CTkFrame(dev_card, fg_color="transparent")
        links_frame.pack(fill="x", padx=24, pady=(0, 18))

        SocialButton(links_frame, "⭐", "GitHub Profile",
                     APP_GITHUB, COLORS["accent"]).pack(side="left", padx=(0, 10))
        SocialButton(links_frame, "📸", "Instagram",
                     "https://www.instagram.com/shanu.fx/",
                     COLORS["accent_2"]).pack(side="left", padx=(0, 10))
        SocialButton(links_frame, "💬", "WhatsApp Bot",
                     "https://github.com/ShanudhaTirosh",
                     COLORS["accent_green"]).pack(side="left")

        # ── Tech stack ────────────────────────────────────────────────────────
        tech_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=20,
                                  border_width=1, border_color=COLORS["border"])
        tech_card.pack(fill="x", padx=30, pady=(14, 0))

        ctk.CTkLabel(tech_card, text="Technology Stack", font=FONTS["heading_sm"],
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=24, pady=(18, 2))
        ctk.CTkFrame(tech_card, height=1, fg_color=COLORS["border"]).pack(fill="x")

        tech_grid = ctk.CTkFrame(tech_card, fg_color="transparent")
        tech_grid.pack(fill="x", padx=24, pady=16)

        techs = [
            ("🐍", "Python 3.11+",        "Core language"),
            ("🎨", "CustomTkinter",        "Modern UI framework"),
            ("⬇", "yt-dlp",               "Media downloader engine"),
            ("🎬", "FFmpeg",               "Video/audio processing"),
            ("🖼", "Pillow",               "Image handling"),
            ("🔌", "Tkinter",              "Base GUI library"),
        ]

        for i, (icon, name, desc) in enumerate(techs):
            row = i // 3
            col = i % 3
            cell = ctk.CTkFrame(tech_grid, fg_color=COLORS["bg_elevated"], corner_radius=10)
            cell.grid(row=row, column=col, padx=(0, 10) if col < 2 else 0,
                      pady=(0, 10) if row == 0 else 0, sticky="ew")
            tech_grid.grid_columnconfigure(col, weight=1)

            ctk.CTkLabel(cell, text=f"{icon}  {name}", font=FONTS["heading_sm"],
                         text_color=COLORS["text_primary"]).pack(anchor="w", padx=12, pady=(10, 2))
            ctk.CTkLabel(cell, text=desc, font=FONTS["caption"],
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=12, pady=(0, 10))

        # ── Build info ────────────────────────────────────────────────────────
        build_card = ctk.CTkFrame(scroll, fg_color=COLORS["bg_card"], corner_radius=20,
                                   border_width=1, border_color=COLORS["border"])
        build_card.pack(fill="x", padx=30, pady=(14, 30))

        info_row = ctk.CTkFrame(build_card, fg_color="transparent")
        info_row.pack(fill="x", padx=24, pady=16)

        build_items = [
            ("App Name",    APP_NAME),
            ("Version",     APP_VERSION),
            ("Platform",    "Windows 10/11"),
            ("License",     "MIT License"),
            ("GitHub",      APP_GITHUB),
        ]

        for label, value in build_items:
            row = ctk.CTkFrame(info_row, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{label}:", font=FONTS["body_sm"],
                         text_color=COLORS["text_secondary"], width=100).pack(side="left")
            ctk.CTkLabel(row, text=value, font=FONTS["body_sm"],
                         text_color=COLORS["text_primary"]).pack(side="left", padx=(8, 0))

        # Copyright
        ctk.CTkLabel(
            scroll,
            text=f"© 2025 {APP_AUTHOR}  ·  All rights reserved  ·  {APP_NAME}",
            font=FONTS["caption"], text_color=COLORS["text_muted"],
        ).pack(pady=(0, 20))
