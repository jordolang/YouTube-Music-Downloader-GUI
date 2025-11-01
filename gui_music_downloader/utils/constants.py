"""
Application constants and default settings
"""
from pathlib import Path
import os

# App Information
APP_NAME = "YouTube Music Downloader"
APP_VERSION = "0.1.0"
APP_AUTHOR = "Jordan Lang"
APP_REPO_URL = "https://github.com/jordolang/YouTube-Music-Downloader-GUI"

# Paths
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / "Library" / "Application Support" / "YouTubeMusicDownloader"
LOGS_DIR = HOME_DIR / "Library" / "Logs" / "YouTubeMusicDownloader"
CACHE_DIR = CONFIG_DIR / "cache"
THUMBNAILS_DIR = CONFIG_DIR / "thumbnails"
DEFAULT_MUSIC_DIR = HOME_DIR / "Music"

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

# File Paths
CONFIG_FILE = CONFIG_DIR / "config.json"
QUEUE_STATE_FILE = CONFIG_DIR / "queue_state.json"
LOG_FILE = LOGS_DIR / "app.log"

# Quality Options (kbps)
QUALITY_OPTIONS = {
    "Best": 320,
    "High (320 kbps)": 320,
    "Medium (256 kbps)": 256,
    "Standard (192 kbps)": 192,
    "Low (128 kbps)": 128,
}

# Default Settings
DEFAULT_QUALITY = "Best"
DEFAULT_FOLDER_STRUCTURE = "{music_dir}/{artist}/{title}.mp3"
DEFAULT_FILENAME_PATTERN = "{artist} - {title}"
DEFAULT_CONCURRENT_DOWNLOADS = 3
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 300

# Filename Pattern Variables
FILENAME_VARIABLES = ["artist", "title", "album", "year", "track_number"]

# Download Engine Options
DOWNLOAD_ENGINES = ["ytdlp", "instantmusic"]
DEFAULT_DOWNLOAD_ENGINE = "ytdlp"

# Metadata Source Priorities
METADATA_SOURCES = ["musicbrainz", "shazam", "genius", "lastfm", "discogs"]
DEFAULT_METADATA_PRIORITY = ["musicbrainz", "shazam", "lastfm", "discogs", "genius"]

# Album Art Settings
DEFAULT_ALBUM_ART_SIZE = "600x600"
ALBUM_ART_SOURCES = ["itunes", "google"]

# UI Settings
DEFAULT_THEME = "System"  # System, Dark, Light
THEME_OPTIONS = ["System", "Dark", "Light"]
SEARCH_RESULTS_LIMIT = 10

# Network Settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2

# File Size Estimation (bytes per second at given quality)
BITRATE_TO_SIZE = {
    320: 40000,   # 320 kbps ≈ 40 KB/s
    256: 32000,   # 256 kbps ≈ 32 KB/s
    192: 24000,   # 192 kbps ≈ 24 KB/s
    128: 16000,   # 128 kbps ≈ 16 KB/s
}

# Status Icons/Emojis
STATUS_ICONS = {
    "queued": "⏳",
    "downloading": "⬇️",
    "processing": "⚙️",
    "complete": "✅",
    "error": "❌",
    "paused": "⏸️",
    "canceled": "🚫",
}

# Keyboard Shortcuts (macOS)
SHORTCUTS = {
    "search": "<Command-f>",
    "download": "<Command-d>",
    "pause": "<Command-p>",
    "settings": "<Command-comma>",
    "quit": "<Command-q>",
}

# API URLs
ITUNES_SEARCH_API = "https://itunes.apple.com/search"
MUSICBRAINZ_API = "https://musicbrainz.org/ws/2"
