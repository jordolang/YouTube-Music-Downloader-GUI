# Testing Guide

## Manual Testing Checklist

### 1. Search & Download Tests

#### Single Track Search
- [ ] Search for "Queen Bohemian Rhapsody"
- [ ] Verify 10 results appear with proper ranking (official video first)
- [ ] Check that live performances have lower scores
- [ ] Select quality: Best (320 kbps)
- [ ] Download single track
- [ ] Verify file saved to `~/Music/Queen/Bohemian Rhapsody.mp3`
- [ ] Check metadata: Title, Artist, Album art
- [ ] Try all quality options: 320, 256, 192, 128 kbps

#### Batch Download
- [ ] Search for any artist
- [ ] Select 3-5 tracks
- [ ] Click "Download Selected"
- [ ] Verify all tracks queue properly
- [ ] Check progress in Library Sync tab

### 2. Playlist Tests

#### Small Playlist (< 20 tracks)
- [ ] Go to Playlist tab
- [ ] Paste URL: `https://www.youtube.com/playlist?list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG`
- [ ] Click "Fetch Playlist"
- [ ] Verify playlist name, track count, total size appear
- [ ] Verify all tracks listed with proper info
- [ ] Click "Select All"
- [ ] Verify button shows count
- [ ] Click "Select None"
- [ ] Manually select 5 tracks
- [ ] Download selected tracks
- [ ] Verify all appear in queue

#### Large Playlist (> 50 tracks)
- [ ] Fetch a large playlist
- [ ] Verify UI remains responsive
- [ ] Select subset of tracks
- [ ] Download and monitor progress

### 3. Settings Tests

#### General Settings
- [ ] Open Settings (Cmd+, or button)
- [ ] Change quality to 256 kbps
- [ ] Change save location to custom folder
- [ ] Change theme to Dark
- [ ] Verify theme changes immediately
- [ ] Click Save
- [ ] Restart app
- [ ] Verify settings persisted

#### Metadata Settings
- [ ] Add Genius API key (optional)
- [ ] Enable "Fetch and embed lyrics"
- [ ] Save and download a track
- [ ] Verify lyrics embedded (if API key provided)

#### Advanced Settings
- [ ] Change concurrent downloads to 5
- [ ] Change logging level to DEBUG
- [ ] Save
- [ ] Download multiple tracks
- [ ] Verify 5 run concurrently

#### Import/Export
- [ ] Click "Export Settings"
- [ ] Save to ~/Downloads/test_settings.json
- [ ] Change several settings
- [ ] Click "Import Settings"
- [ ] Select exported file
- [ ] Verify settings restored

### 4. Library Sync Tests (Spotify/Apple Music)

#### Spotify Sync
- [ ] Configure Spotify credentials in tokens.json
- [ ] Go to Library Sync tab
- [ ] Select "spotify" service
- [ ] Enable "Automatic YouTube matching"
- [ ] Click "Sync & Download"
- [ ] Verify tracks fetched from Spotify
- [ ] Verify YouTube matching progress
- [ ] Verify downloads begin automatically
- [ ] Check queue for progress

#### Apple Music Sync
- [ ] Configure Apple Music credentials
- [ ] Follow same steps as Spotify
- [ ] Verify sync works

### 5. Queue Management Tests

#### Progress Monitoring
- [ ] Queue 5+ downloads
- [ ] Verify progress bars update in real-time
- [ ] Verify speed and ETA shown
- [ ] Verify status updates (downloading → processing → complete)

#### Pause/Resume
- [ ] Start downloading a large file
- [ ] Pause download (if UI supports)
- [ ] Resume download
- [ ] Verify continues from where it left off

#### Cancel
- [ ] Start download
- [ ] Cancel before completion
- [ ] Verify download stops
- [ ] Verify partial file cleaned up (optional)

### 6. File Organization Tests

#### Artist/Title Organization
- [ ] Download tracks from different artists
- [ ] Verify structure: `~/Music/Artist/Title.mp3`
- [ ] Verify artist folders created

#### Duplicate Handling
- [ ] Download same track twice with setting "Rename"
- [ ] Verify second file: `Title_1.mp3`
- [ ] Change setting to "Skip"
- [ ] Download same track
- [ ] Verify skipped
- [ ] Change to "Overwrite"
- [ ] Download again
- [ ] Verify file replaced

### 7. Keyboard Shortcuts

- [ ] Cmd+F focuses search field
- [ ] Cmd+, opens Settings
- [ ] Cmd+Q quits app
- [ ] Enter in search field triggers search
- [ ] Enter in playlist URL triggers fetch

### 8. Error Handling

#### Network Errors
- [ ] Disconnect Wi-Fi
- [ ] Try to search
- [ ] Verify error message shown
- [ ] Try to download
- [ ] Verify graceful failure

#### Invalid Input
- [ ] Search for gibberish that returns no results
- [ ] Verify "No results" message
- [ ] Enter invalid playlist URL
- [ ] Verify validation error

#### Missing Dependencies
- [ ] (Advanced) Temporarily rename ffmpeg
- [ ] Try to download
- [ ] Verify error about missing ffmpeg
- [ ] Restore ffmpeg

### 9. System Integration

#### Notifications
- [ ] Download a track
- [ ] Verify macOS notification appears on completion
- [ ] Click notification (should do nothing or focus app)

#### Metadata in Finder
- [ ] Download track
- [ ] Right-click file in Finder → Get Info
- [ ] Verify metadata visible: Title, Artist, Album
- [ ] Open in Music.app
- [ ] Verify metadata and album art display

### 10. Persistence & Recovery

#### Settings Persistence
- [ ] Change settings
- [ ] Quit app (Cmd+Q)
- [ ] Reopen app
- [ ] Verify settings retained

#### Queue Recovery
- [ ] Queue several downloads
- [ ] Force quit app (Cmd+Opt+Esc)
- [ ] Reopen app
- [ ] Verify incomplete downloads resume (if supported)

---

## Automated Test Execution

Run the test suite:
```bash
cd ~/Repos/YouTube-Music-Downloader-GUI
source .venv/bin/activate
pytest tests/ -v
```

Run specific test modules:
```bash
pytest tests/backend/test_queue_manager.py -v
pytest tests/backend/test_sync_orchestrator.py -v
```

Run with coverage:
```bash
pytest --cov=gui_music_downloader --cov-report=html tests/
open htmlcov/index.html
```

---

## Performance Tests

### Load Testing
- [ ] Queue 100+ tracks at once
- [ ] Monitor CPU and memory usage
- [ ] Verify UI remains responsive
- [ ] Verify downloads complete without errors

### Playlist Stress Test
- [ ] Fetch playlist with 500+ tracks
- [ ] Verify loading completes
- [ ] Verify scrolling is smooth
- [ ] Verify select/deselect operations work

---

## Known Limitations

1. **Pause/Resume**: May not work for all download methods (depends on aria2c)
2. **Very Large Playlists**: May take time to load (1000+ tracks)
3. **Concurrent Downloads**: Limited by system resources and network
4. **Metadata Accuracy**: Depends on YouTube video titles and external APIs
5. **Streaming Services**: Requires valid credentials and active subscriptions

---

## Bug Reporting

If you find issues during testing:

1. Note the exact steps to reproduce
2. Check logs at `~/Library/Logs/YouTubeMusicDownloader/`
3. Include:
   - OS version (macOS 13.x, 14.x, etc.)
   - Python version (`python --version`)
   - Error message or unexpected behavior
   - Log excerpt if relevant

Report at: https://github.com/jordolang/YouTube-Music-Downloader-GUI/issues

---

## Test Results Template

```
Date: YYYY-MM-DD
Tester: [Your Name]
macOS Version: 
App Version: 0.1.0

PASSED: X/Y tests
FAILED: Z tests

Failed Tests:
- [Test Name]: [Description of failure]

Notes:
- [Any observations]
```
