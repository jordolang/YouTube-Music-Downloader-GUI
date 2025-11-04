from datetime import UTC, datetime, timedelta

from gui_music_downloader.backend.music_services.models import (
    AuthTokens,
    StreamingTrack,
)


def test_auth_tokens_expired_property():
    tokens = AuthTokens(
        access_token="token",
        expires_at=datetime.now(UTC) - timedelta(seconds=5),
    )
    assert tokens.is_expired is True


def test_streaming_track_canonical_query_builds_artist_title():
    track = StreamingTrack(
        service="spotify",
        track_id="123",
        name="Midnight City",
        artists=["M83"],
        album="Hurry Up, We're Dreaming",
    )
    query = track.canonical_query()
    assert "Midnight City" in query
    assert "M83" in query
