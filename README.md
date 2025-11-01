# YouTube Music Downloader GUI

🎵 **A modern, native-looking macOS GUI application for downloading music from YouTube with comprehensive metadata support**

Built with Python and CustomTkinter, featuring integration with the existing [CLI-Music-Downloader](https://github.com/jordolang/CLI-Music-Downloader) backend.

## ✨ Features

### Core Functionality
- 🔍 **Smart Search**: Search YouTube by song name and choose from multiple results
- 📋 **Playlist Support**: Download entire playlists with track selection
- 🎨 **Modern GUI**: Clean, native macOS look using CustomTkinter
- ⚙️ **Quality Selection**: Choose audio quality (Best, 320, 256, 192, 128 kbps)
- 📊 **Progress Tracking**: Real-time progress bars with speed and ETA
- ⏸️ **Pause/Resume**: Full control over downloads with pause and resume capability

### Metadata & Organization
- 🏷️ **Comprehensive Metadata**: Auto-tag with artist, title, album, year, genre, track numbers
- 🎵 **Multi-Source**: MusicBrainz, Shazam, Genius, Last.fm, Discogs integration
- 📝 **Lyrics Support**: Automatic lyrics fetching and embedding
- 🖼️ **Album Art**: High-quality artwork from iTunes API and Google Images
- 📁 **Smart Organization**: Saves to `~/Music/<Artist-Name>/<Song>.mp3`
- ✏️ **Metadata Editor**: Manual editing of tags and album art

### Advanced Features
- 🔄 **Download Queue**: Manage multiple downloads with queue system
- 🔔 **Notifications**: macOS system notifications for completed downloads
- 🎚️ **Configurable**: Extensive settings for download behavior and metadata sources
- 💾 **State Persistence**: Resume downloads after app restart
- 🔐 **Duplicate Handling**: Skip, overwrite, or rename duplicate files
- ⌨️ **Keyboard Shortcuts**: Cmd+F, Cmd+D, Cmd+P, Cmd+, (settings)

## 🚀 Installation

### Prerequisites
- macOS 10.15+ (Catalina or later)
- Python 3.12+ (via pyenv)
- Homebrew
- System dependencies: `ffmpeg`, `aria2`, `terminal-notifier`

### Quick Start

```bash
# 1. Install system dependencies
brew install ffmpeg aria2 terminal-notifier

# 2. Clone the repository
git clone https://github.com/jordolang/YouTube-Music-Downloader-GUI.git
cd YouTube-Music-Downloader-GUI

# 3. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Install CLI Music Downloader backend (if not already installed)
pip install -e ~/Repos/CLI-Music-Downloader

# 6. Run the application
python launcher.py
```

## 📖 Usage

### Basic Workflow

1. **Search for Music**
   - Type song name in search bar
   - Press Enter or click Search button
   - Select from multiple YouTube results

2. **Configure Download**
   - Choose audio quality from dropdown
   - Review estimated file size
   - Select tracks (for playlists)

3. **Download**
   - Click "Download" to start
   - Monitor progress in Download Queue tab
   - Pause/resume/cancel as needed

4. **Access Your Music**
   - Files saved to `~/Music/<Artist>/`
   - Complete with metadata, lyrics, and album art

### Playlist Downloads

1. Switch to "Playlist" tab
2. Paste YouTube playlist URL
3. Select individual tracks or "Select All"
4. Click "Download Selected"

### Settings

Access via **Cmd+,** or Settings button:

- **General**: Quality, save location, filename patterns, theme
- **Metadata**: API keys, source priorities, auto-metadata
- **Advanced**: Concurrent downloads, retry settings, engine selection

## 🛠️ Project Structure

```
YouTube-Music-Downloader-GUI/
├── gui_music_downloader/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── gui/                       # GUI components
│   │   ├── main_window.py         # Main application window
│   │   ├── search_tab.py          # Search results tab
│   │   ├── playlist_tab.py        # Playlist management tab
│   │   ├── queue_tab.py           # Download queue tab
│   │   ├── settings_dialog.py    # Settings dialog
│   │   ├── metadata_editor.py    # Metadata editor dialog
│   │   └── components/            # Reusable UI components
│   │       ├── progress_card.py   # Progress display card
│   │       ├── search_result_card.py  # Search result item
│   │       └── playlist_item.py   # Playlist track item
│   ├── backend/                   # Business logic
│   │   ├── config_manager.py      # Configuration management
│   │   ├── youtube_search.py      # YouTube search & metadata
│   │   ├── downloader.py          # Download engine abstraction
│   │   └── queue_manager.py       # Download queue management
│   ├── utils/                     # Utilities
│   │   ├── constants.py           # App constants
│   │   └── helpers.py             # Helper functions
│   └── assets/                    # Assets
│       ├── icons/                 # Application icons
│       └── themes/                # Custom themes
├── requirements.txt               # Python dependencies
├── launcher.py                    # Application launcher
├── setup.py                       # Package setup
├── config.json.example            # Example configuration
└── README.md                      # This file
```

## 🔧 Configuration

Configuration is stored at:
```
~/Library/Application Support/YouTubeMusicDownloader/config.json
```

### API Keys (Optional but Recommended)

For enhanced metadata, add API keys in Settings > Metadata:

- **Genius API**: [Get Key](https://genius.com/api-clients) - For lyrics
- **Last.fm API**: [Get Key](https://www.last.fm/api/account/create) - For genre/artist info
- **Discogs Token**: [Get Token](https://www.discogs.com/settings/developers) - For release info

### Example Configuration

```json
{
  "general": {
    "default_quality": "Best",
    "save_location": "~/Music",
    "filename_pattern": "{artist} - {title}",
    "theme": "System"
  },
  "metadata": {
    "api_keys": {
      "genius": "your_genius_api_key",
      "lastfm": "your_lastfm_api_key",
      "discogs": "your_discogs_token"
    },
    "auto_metadata": true,
    "fetch_lyrics": true
  },
  "advanced": {
    "concurrent_downloads": 3,
    "download_engine": "ytdlp"
  }
}
```

## 🎯 Roadmap

### v0.1.0 (Current - In Development)
- [x] Project structure and setup
- [x] Configuration management
- [x] Utility functions and constants
- [ ] YouTube search implementation
- [ ] Download engine with yt-dlp
- [ ] Main GUI window with tabs
- [ ] Search results display
- [ ] Download queue management
- [ ] Progress tracking
- [ ] Settings dialog
- [ ] Metadata integration

### v0.2.0 (Planned)
- [ ] Playlist support
- [ ] Pause/resume functionality
- [ ] Metadata editor dialog
- [ ] Drag & drop playlist URLs
- [ ] System notifications
- [ ] Search history
- [ ] Favorites

### v0.3.0 (Future)
- [ ] macOS app bundle packaging
- [ ] Auto-updates
- [ ] Batch operations
- [ ] Export/import playlists
- [ ] Dark mode refinements
- [ ] Performance optimizations

## 🐛 Troubleshooting

### Common Issues

**App won't start**
- Ensure Python 3.12+ is installed: `python --version`
- Activate virtual environment: `source .venv/bin/activate`
- Check dependencies: `pip install -r requirements.txt`

**Downloads failing**
- Verify `ffmpeg` is installed: `ffmpeg -version`
- Check internet connection
- Try different quality setting

**No metadata**
- Verify API keys in Settings > Metadata
- Check MusicBrainz server status
- Enable "Force Refresh" in settings

**Slow downloads**
- Reduce concurrent downloads in Settings > Advanced
- Check network speed
- Try different download engine

## 📝 Development

### Setting Up Development Environment

```bash
# Clone and enter directory
git clone https://github.com/jordolang/YouTube-Music-Downloader-GUI.git
cd YouTube-Music-Downloader-GUI

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e .
pip install -r requirements.txt

# Install CLI backend in editable mode
pip install -e ~/Repos/CLI-Music-Downloader

# Run the app
python -m gui_music_downloader.main
```

### Running Tests

```bash
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built on top of [CLI-Music-Downloader](https://github.com/jordolang/CLI-Music-Downloader)
- Uses [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern GUI
- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloads
- Metadata from MusicBrainz, Last.fm, Discogs, Genius APIs

## 💖 Support

If you find this tool useful, consider supporting the project:

<a href="https://www.buymeacoffee.com/jordolang" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" >
</a>

## 📧 Contact

- **Author**: Jordan Lang
- **GitHub**: [@jordolang](https://github.com/jordolang)
- **Issues**: [GitHub Issues](https://github.com/jordolang/YouTube-Music-Downloader-GUI/issues)

---

**Note**: This tool is for personal use. Please respect YouTube's Terms of Service and copyright laws.
