# ═══════════════════════════════════════════════════════════════
# Shanu Fx Private Downloader - PyInstaller Build Spec
#
# Build command:
#   pyinstaller ShanuFxDownloader.spec --clean
#
# Or simple one-liner:
#   pyinstaller --onefile --windowed --name "ShanuFxDownloader"
#               --icon assets/icon.ico
#               --add-data "assets;assets"
#               main.py
# ═══════════════════════════════════════════════════════════════

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path(__file__).parent)],
    binaries=[],
    datas=[
        # Include customtkinter themes
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'yt_dlp',
        'yt_dlp.utils',
        'yt_dlp.extractor',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'urllib.request',
        'threading',
        'json',
        'pathlib',
        'subprocess',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ShanuFxDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',  # Uncomment if you have an icon
    version_info={
        'FileVersion': '1, 0, 0, 0',
        'ProductName': 'Shanu Fx Private Downloader',
        'FileDescription': 'All-in-one Media Downloader',
        'CompanyName': 'Shanudha Tirosh',
        'LegalCopyright': '© 2025 Shanudha Tirosh',
    },
)
