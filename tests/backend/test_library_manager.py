from datetime import UTC, datetime

from gui_music_downloader.backend.library_manager import LibraryManager, SyncProgress
from gui_music_downloader.backend.music_services.base import MusicServiceClient
from gui_music_downloader.backend.music_services.models import (
    AuthTokens,
    LibrarySnapshot,
    Playlist,
    ResolutionCandidate,
    StreamingTrack,
)


class DummyService(MusicServiceClient):
    service_name = "dummy"

    def __init__(self):
        super().__init__(token_store=None)
        self._authed = True
        track = StreamingTrack(
            service=self.service_name,
            track_id="t1",
            name="Test Song",
            artists=["Test Artist"],
            album="Test Album",
            duration_ms=200000,
        )
        playlist = Playlist(
            service=self.service_name,
            playlist_id="p1",
            name="Playlist",
            tracks=[track],
        )
        self._snapshot = LibrarySnapshot(
            service=self.service_name,
            fetched_at=datetime.now(UTC),
            playlists=[playlist],
        )

    def authenticate(self, interactive: bool = True):
        self._authed = True
        return AuthTokens(access_token="dummy")

    def refresh_tokens(self):
        return AuthTokens(access_token="dummy")

    def is_authenticated(self) -> bool:
        return self._authed

    def fetch_library(self) -> LibrarySnapshot:
        return self._snapshot

    def iter_tracks(self, playlist_id=None):
        yield from self._snapshot.playlists[0].tracks

    def resolve_track(self, track: StreamingTrack):
        return ResolutionCandidate(
            youtube_id="abc123",
            url="https://youtu.be/abc123",
            title=track.name,
            channel=track.display_artist(),
            score=100.0,
        )


def test_library_manager_emits_progress_and_returns_resolved_tracks():
    service = DummyService()
    manager = LibraryManager()
    manager.register_service(service)

    events: list[tuple[str, str]] = []

    def listener(event: str, progress: SyncProgress):
        events.append((event, progress.state))

    manager.subscribe(listener)
    resolved = manager.sync_service("dummy")

    assert resolved
    assert resolved[0].track.track_id == "t1"
    assert resolved[0].candidate.youtube_id == "abc123"
    assert ("start", "fetching") in events
    assert ("progress", "resolving") in events
    assert ("completed", "completed") in events
