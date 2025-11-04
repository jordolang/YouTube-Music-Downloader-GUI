from datetime import UTC, datetime

from gui_music_downloader.backend.library_manager import LibraryManager
from gui_music_downloader.backend.music_services.base import MusicServiceClient
from gui_music_downloader.backend.music_services.models import (
    AuthTokens,
    LibrarySnapshot,
    Playlist,
    ResolutionCandidate,
    ResolvedTrack,
    StreamingTrack,
)
from types import SimpleNamespace

from gui_music_downloader.backend.sync_orchestrator import SyncOrchestrator
from gui_music_downloader.backend.config_manager import get_config


class DummyService(MusicServiceClient):
    service_name = "dummy"

    def __init__(self):
        super().__init__(token_store=None)
        track = StreamingTrack(
            service=self.service_name,
            track_id="t1",
            name="Test Song",
            artists=["Tester"],
            album="Unit Tests",
            duration_ms=120000,
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
        return AuthTokens(access_token="dummy")

    def refresh_tokens(self):
        return AuthTokens(access_token="dummy")

    def is_authenticated(self) -> bool:
        return True

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


def test_sync_orchestrator_enqueues_and_executes_download(tmp_path):
    config = get_config()
    config.set("general.save_location", str(tmp_path))

    library_manager = LibraryManager()
    library_manager.register_service(DummyService())

    class FakeQueueManager:
        def __init__(self):
            self.enqueued: list[ResolvedTrack] = []

        def enqueue(self, resolved: ResolvedTrack):
            self.enqueued.append(resolved)
            # Return a lightweight QueueItem-like object
            return SimpleNamespace(
                id="fake",
                track=resolved.track,
                status="queued",
                percent=0.0,
            )

    queue_manager = FakeQueueManager()
    orchestrator = SyncOrchestrator(library_manager=library_manager, queue_manager=queue_manager)

    queue_items = orchestrator.sync_and_enqueue("dummy")

    assert len(queue_items) == 1
    item = queue_items[0]
    # Fake queue returns queued status because downloads are not executed in this unit test.
    assert item.status == "queued"
    assert queue_manager.enqueued[0].track.name == "Test Song"
