"""
Shanu Fx Private Downloader
═══════════════════════════════════════════════════════════════
Author:  Shanudha Tirosh
GitHub:  https://github.com/ShanudhaTirosh
Version: 1.0.0
Platform: Windows 10/11 (also runs on Linux/macOS)

Entry point — launches setup splash on first run, then the main app.
═══════════════════════════════════════════════════════════════
"""

import sys
import os

# ── Ensure project root is in path ────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Suppress DeprecationWarnings from dependencies ────────────────────────────
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import customtkinter as ctk

from core.config import config
from core.setup  import setup_manager


def launch_app():
    """Create and start the main application window."""
    from ui.app import App
    app = App()
    app.mainloop()


def main():
    """
    Application bootstrap.
    On first run: show setup splash → install dependencies → launch app.
    Subsequent runs: launch directly.
    """
    # Check if first-run setup is needed
    if config.get("first_run", True) or setup_manager.needs_setup():
        # Create a hidden root to host the splash
        root = ctk.CTk()
        root.withdraw()
        root.geometry("1x1+0+0")

        from ui.setup_splash import SetupSplash

        def after_setup():
            root.destroy()
            launch_app()

        splash = SetupSplash(root, on_complete=after_setup)
        root.mainloop()
    else:
        launch_app()


if __name__ == "__main__":
    main()
