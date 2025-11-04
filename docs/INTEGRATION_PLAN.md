# Music Service Integration Plan

## Goals
- Authenticate against Spotify and Apple Music, securely persisting refreshable tokens.
- Enumerate a user’s playlists, albums, and track metadata (artist, album, track number, artwork, duration, ISRC).
- Resolve each streaming track to the best YouTube audio source using deterministic matching with fallbacks.
- Feed resolved videos into the existing download pipeline, enriching the resulting MP3 files with streaming metadata.
- Provide manual overrides and progress visibility in the GUI.

## Architecture Overview
- `music_services/`: new backend package encapsulating third-party integrations.
  - `base.py`: abstract `MusicServiceClient` defining `authenticate()`, `fetch_library()`, `resolve_track()`, `refresh_token()`, and event hooks.
  - `models.py`: shared dataclasses for `StreamingTrack`, `Playlist`, `LibrarySnapshot`, and resolution results.
  - `auth.py`: token serialization helpers plus secure keychain/file-store adapters.
  - `spotify.py` and `apple_music.py`: concrete clients handling OAuth flow, API pagination, and rate limits.
  - `resolver.py`: mapping pipeline that scores potential YouTube matches using metadata heuristics and, when required, manual search fallback.
- `library_manager.py`: orchestrates sync jobs, queues resolved downloads, records status, and emits updates to the GUI.
- `config_manager`: extended to remember enabled services, token metadata, and sync preferences (auto-sync, include liked songs, etc.).
- CLI backend integration happens in `resolver.py` and `downloader.py`, ensuring metadata is carried through to tagging.

## Incremental Milestones
1. **Scaffolding (PR1)**: add `music_services` package with base classes, datamodels, and dependency hooks; wire `library_manager` skeleton; update config schema.
2. **Spotify Foundations (PR2)**: implement OAuth Device Code flow (no GUI yet), fetch user profile + playlists, persist tokens, add smoke tests.
3. **Spotify Library Sync (PR3)**: pull track metadata, normalize to `StreamingTrack`, prototype resolver that hits YouTube search, enqueue downloads manually.
4. **Apple Music Foundations (PR4)**: integrate MusicKit developer tokens + user tokens, basic library fetch.
5. **Unified Resolver (PR5)**: production-quality matching (fuzzy metadata, ISRC, duration scoring), add manual override UI hooks.
6. **Automation & GUI (PR6)**: background sync orchestration, queue manager integration, progress events surfaced in GUI.
7. **Metadata Fidelity (PR7)**: artwork caching, lyrics, error recovery, coverage improvements, and UX polish.
