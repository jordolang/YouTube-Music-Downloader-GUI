# Next Steps for YouTube Music Downloader GUI

## ✅ Completed (Steps 1-4)

- [x] **Prerequisites installed** (ffmpeg, aria2, terminal-notifier)
- [x] **Python environment setup** (Python 3.12.12 with venv)
- [x] **Git repository initialized** with proper .gitignore
- [x] **Project structure scaffolded** with all directories and base files
- [x] **Dependencies installed** (customtkinter, yt-dlp, etc.)
- [x] **CLI backend linked** (CLI-Music-Downloader)
- [x] **Configuration system** implemented and working
- [x] **Utility functions** created (helpers, constants)

## 🚧 Remaining Work

### Priority 1: Core Backend (Essential for MVP)

#### 5. YouTube Search Module (`backend/youtube_search.py`)
Create a module to search and extract YouTube video metadata.

**Key Functions:**
```python
def search_videos(query: str, limit: int = 10) -> List[SearchResult]:
    """Search YouTube and return list of results"""
    
def get_video_details(url: str) -> VideoDetails:
    """Get detailed metadata for a single video"""
    
def get_playlist_info(url: str) -> PlaylistInfo:
    """Extract playlist information and tracks"""
    
def estimate_file_size(duration_sec: int, bitrate_kbps: int) -> int:
    """Calculate estimated file size"""
```

**Implementation Tips:**
- Use `youtubesearch` from `youtube-search-python`
- Cache thumbnails in `THUMBNAILS_DIR`
- Handle errors gracefully (network issues, invalid URLs)
- Support YouTube, YouTube Music, and channel playlists

**Test Command:**
```bash
python -c "from gui_music_downloader.backend.youtube_search import search_videos; print(search_videos('The Beatles Hey Jude', 3))"
```

---

#### 6. Download Engine (`backend/downloader.py`)
Implement the download engine with yt-dlp integration.

**Key Classes:**
```python
class DownloadEngine(ABC):
    """Abstract base class for download engines"""
    @abstractmethod
    def download(self, url, quality, progress_callback): pass

class YtDlpEngine(DownloadEngine):
    """yt-dlp based download engine"""
    def __init__(self):
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'progress_hooks': [self._progress_hook],
        }
```

**Features to Implement:**
- Audio extraction to MP3
- Quality selection (320, 256, 192, 128 kbps)
- Progress callback for GUI updates
- Error handling and retry logic
- Pause/resume support (via aria2c external downloader)
- Metadata enhancement using CLI backend

---

#### 7. Queue Manager (`backend/queue_manager.py`)
Build a robust download queue with threading.

**Key Components:**
```python
@dataclass
class QueueItem:
    id: str
    url: str
    title: str
    artist: str
    status: str  # queued, downloading, processing, complete, error
    progress: float
    speed: float
    eta: str

class QueueManager:
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers)
        self.queue: List[QueueItem] = []
    
    def add(self, item: QueueItem): pass
    def start_downloads(self): pass
    def pause(self, item_id): pass
    def cancel(self, item_id): pass
```

---

### Priority 2: GUI Implementation

#### 8. Main Application Window (`gui/main_window.py`)
Replace the welcome screen with the full application interface.

**Layout:**
```
┌─────────────────────────────────────────────┐
│ [Search Bar] [Quality ▼] [🔍 Search]        │
├─────────────────────────────────────────────┤
│ [Tab: Search] [Tab: Playlist] [Tab: Queue] │ [Tab: Settings]
│                                             │
│  (Tab Content Area)                         │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│ Status: 3 active | Speed: 2.5 MB/s          │
└─────────────────────────────────────────────┘
```

**Widgets to Create:**
- CTkEntry for search
- CTkOptionMenu for quality selection
- CTkTabview for tabs
- CTkButton for actions
- Status bar with labels

---

#### 9. Search Results Tab (`gui/search_tab.py`)
Display search results in a scrollable list with selection.

**Components:**
- `CTkScrollableFrame` for results list
- Custom result cards showing:
  - Thumbnail (fetch asynchronously)
  - Title and channel
  - Duration and estimated size
  - Checkbox for selection
- Buttons: "Download Selected", "Add to Queue"

---

#### 10. Download Queue Tab (`gui/queue_tab.py`)
Show active and completed downloads with progress.

**Features:**
- List of queue items with progress bars
- Real-time updates via `after()` callbacks
- Pause/Resume/Cancel buttons per item
- Bulk actions: Clear completed, Pause all

---

#### 11. Playlist Tab (`gui/playlist_tab.py`)
Handle playlist URL input and track selection.

**UI Elements:**
- URL entry field
- "Load Playlist" button
- Scrollable list of tracks with checkboxes
- "Select All" / "Deselect All" buttons
- Total size estimate
- "Download Selected" button

---

#### 12. Settings Dialog (`gui/settings_dialog.py`)
Create a multi-tab settings window.

**Tabs:**
1. **General**: Quality, save location, filename patterns, theme
2. **Metadata**: API keys, source priorities, auto-metadata toggle
3. **Advanced**: Concurrent downloads, engine selection, logging
4. **About**: Version, credits, links

---

### Priority 3: Integration & Polish

#### 13. Threading & Event Flow
Ensure GUI remains responsive during downloads.

**Implementation:**
- Run downloads in ThreadPoolExecutor
- Use `app.after()` for GUI updates
- Thread-safe queue operations
- Graceful shutdown handling

---

#### 14. Metadata Integration
Connect the CLI backend metadata systems.

**Usage:**
```python
from cli_music_downloader import LyricsMetadataHandler, MetadataValidator

# After download
handler = LyricsMetadataHandler(genius_key)
metadata = handler.get_lyrics(artist, title)
# Apply to file
```

---

#### 15. Notifications & Error Handling
Add system notifications and user-friendly error messages.

```python
import pync

pync.notify(
    'Download Complete!',
    title='YouTube Music Downloader',
    sound='default'
)
```

---

## 📝 Development Workflow

### Testing the Application

1. **Activate venv:**
   ```bash
   cd ~/Repos/YouTube-Music-Downloader-GUI
   source .venv/bin/activate
   ```

2. **Run the app:**
   ```bash
   python launcher.py
   ```

3. **Test individual modules:**
   ```bash
   python -m gui_music_downloader.backend.youtube_search
   ```

---

### Iterative Development Approach

Work in this order for fastest results:

1. **Week 1**: YouTube search + basic downloader
   - Implement `youtube_search.py`
   - Implement basic `downloader.py` with yt-dlp
   - Test downloads from command line

2. **Week 2**: GUI Framework
   - Build `main_window.py` with tabs
   - Implement `search_tab.py`
   - Connect search to backend

3. **Week 3**: Downloads & Queue
   - Implement `queue_manager.py`
   - Build `queue_tab.py`
   - Connect downloader to queue

4. **Week 4**: Playlist & Polish
   - Implement `playlist_tab.py`
   - Add settings dialog
   - Metadata integration
   - Bug fixes and testing

---

## 🔍 Quick Reference

### Running the App
```bash
cd ~/Repos/YouTube-Music-Downloader-GUI
source .venv/bin/activate
python launcher.py
```

### Key File Locations
- **Config**: `~/Library/Application Support/YouTubeMusicDownloader/config.json`
- **Logs**: `~/Library/Logs/YouTubeMusicDownloader/app.log`
- **Downloads**: `~/Music/<Artist>/`

### Useful Commands
```bash
# Check dependencies
pip list | grep -E "(customtkinter|yt-dlp|youtube-search)"

# Verify CLI backend
python -c "import cli_music_downloader; print(cli_music_downloader.__version__)"

# Test configuration
python -c "from gui_music_downloader.backend.config_manager import get_config; print(get_config().config)"

# View logs
tail -f ~/Library/Logs/YouTubeMusicDownloader/app.log
```

---

## 📚 Resources

### Documentation
- [CustomTkinter Docs](https://customtkinter.tomschimansky.com/)
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [youtube-search-python](https://github.com/alexmercerind/youtube-search-python)

### Examples
Check your existing CLI-Music-Downloader project for metadata handling examples:
- `~/Repos/CLI-Music-Downloader/cli_music_downloader/download_music.py`
- `~/Repos/CLI-Music-Downloader/cli_music_downloader/lyrics_metadata.py`

---

## 🎯 Minimal Viable Product (MVP) Checklist

To get a working application quickly, focus on these essentials:

- [ ] YouTube search working
- [ ] Single video download working
- [ ] Basic GUI with search and queue tabs
- [ ] Progress indicator
- [ ] Metadata tagging (artist, title, album art)
- [ ] File organization to ~/Music/<Artist>/

**Everything else is enhancement!**

---

## 💡 Tips

1. **Start Simple**: Get one video downloading before adding complexity
2. **Test Often**: Run the app after each major change
3. **Use Logging**: The loguru setup is already configured - use `logger.info()` liberally
4. **Commit Frequently**: Small, focused commits make debugging easier
5. **Reuse CLI Code**: The CLI backend already has working metadata - just call it!

---

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `~/Library/Logs/YouTubeMusicDownloader/app.log`
2. Verify venv is activated: `which python` should show `.venv/bin/python`
3. Test dependencies: `pip list`
4. Read error messages carefully - they usually point to the issue

---

## 📈 Progress Tracking

Use the TODO list to track progress:
```bash
# View remaining tasks
python -c "from gui_music_downloader import read_todos; print(read_todos())"
```

You're off to a great start! The foundation is solid - now it's time to build the features one by one. 🚀
