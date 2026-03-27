# ⬡ Shanu Fx Private Downloader

> **All-in-one media downloader & download manager** — modern desktop app for Windows

Built by **[Shanudha Tirosh](https://github.com/ShanudhaTirosh)** · v1.0.0

---

## ✨ Features

### 🎬 Social Media Downloader
- **1000+ sites** via yt-dlp — YouTube, TikTok, Instagram, Facebook, Twitter/X, Twitch, Vimeo, and more
- **Video downloads** — MP4, 144p → 4K resolution picker
- **Audio extraction** — MP3/M4A at 128/192/256/320 kbps via FFmpeg
- **Thumbnail preview** before downloading
- **Format browser** — see all available qualities per video
- FFmpeg post-processing for clean merging and conversion

### ⚡ Smart Download Manager
- **Multi-threaded** HTTP downloads (up to 32 threads for maximum speed)
- **Pause / Resume** support
- **Auto-retry** on failure (3 attempts)
- **Real-time speed graph** with peak tracking
- **File categorization** — Videos, Music, Documents, Programs
- Queue system with concurrency limits
- **Clipboard detection** — auto-detects copied URLs with download popup

### 🌀 Torrent Support
- Magnet link downloads
- `.torrent` file support
- Peer/seed tracking
- Uses `libtorrent` Python bindings (optional)

### 📋 Download History
- Persistent JSON-backed history
- Search + filter by type (Video / Audio / File)
- One-click file open from history
- Total size tracking

### ⚙️ Settings
- Custom download folder
- Default format/quality/bitrate preferences
- Max thread count slider
- Speed limit control
- Toggle clipboard detection and notifications

### 🎨 Modern UI
- Dark glassmorphism design with deep purple/pink gradients
- Sidebar navigation
- Animated toast notifications
- Speed graph visualization
- Responsive layout

---

## 📦 Requirements

- **Python 3.11+**
- **Windows 10/11** (primary target; also runs on Linux/macOS)
- **FFmpeg** (auto-downloaded on first run if missing)
- **yt-dlp** (installed via pip automatically)

---

## 🚀 Quick Start

### Windows (one-click)
```bat
install.bat      ← installs all dependencies
run.bat          ← launches the app (created by install.bat)
```

### Manual install
```bash
pip install -r requirements.txt
python main.py
```

### Linux / macOS
```bash
chmod +x install.sh && ./install.sh
./run.sh
```

---

## 📁 Project Structure

```
ShanuFxDownloader/
│
├── main.py                    # Entry point
├── requirements.txt
├── install.bat / install.sh   # One-click installers
├── build_exe.bat              # Compile to EXE
│
├── core/
│   ├── config.py              # App config, color palette, paths
│   └── setup.py               # First-run installer (FFmpeg, yt-dlp)
│
├── downloader/
│   ├── ytdlp_backend.py       # yt-dlp wrapper (fetch info + download)
│   ├── history.py             # Download history manager
│   └── torrent.py             # libtorrent wrapper
│
├── manager/
│   ├── download_manager.py    # Queue + task lifecycle manager
│   └── multi_thread.py        # Multi-thread HTTP downloader engine
│
├── ui/
│   ├── app.py                 # Root window, navigation, notifications
│   ├── sidebar.py             # Sidebar nav component
│   ├── setup_splash.py        # First-run splash screen
│   ├── pages/
│   │   ├── home.py            # Dashboard
│   │   ├── downloader.py      # Social media downloader
│   │   ├── manager.py         # Download manager
│   │   ├── history.py         # Download history
│   │   ├── torrent.py         # Torrent downloader
│   │   ├── settings.py        # Settings
│   │   └── about.py           # Developer info
│   └── widgets/
│       └── shared.py          # Reusable components
│
└── utils/
    ├── clipboard.py           # Clipboard URL monitor
    └── notifications.py       # Toast notification system
```

---

## 🛠 Build EXE (Windows)

```bat
build_exe.bat
```

Output: `dist/ShanuFxDownloader.exe` — standalone, no Python needed.

Alternatively:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ShanuFxDownloader main.py
```

---

## 🌀 Torrent Support (Optional)

Torrent downloading requires `libtorrent`. Install one of:

```bash
pip install lbry-libtorrent      # Easiest option
pip install python-libtorrent    # Alternative
```

---

## 📸 Supported Sites (partial list)

| Platform      | Video | Audio | Images |
|---------------|-------|-------|--------|
| YouTube       | ✅    | ✅    | ✅     |
| TikTok        | ✅    | ✅    | ✅     |
| Instagram     | ✅    | ✅    | ✅     |
| Facebook      | ✅    | ✅    | —      |
| Twitter/X     | ✅    | ✅    | ✅     |
| Twitch        | ✅    | ✅    | —      |
| Vimeo         | ✅    | ✅    | —      |
| Dailymotion   | ✅    | ✅    | —      |
| SoundCloud    | —     | ✅    | —      |
| + 990 more    | ✅    | ✅    | —      |

---

## 👤 Developer

| | |
|---|---|
| **Name** | Shanudha Tirosh |
| **GitHub** | [@ShanudhaTirosh](https://github.com/ShanudhaTirosh) |
| **Country** | 🇱🇰 Sri Lanka |

---

## 📄 License

MIT License © 2025 Shanudha Tirosh
