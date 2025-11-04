from __future__ import annotations

from gui_music_downloader.backend.music_services.apple_music import AppleMusicService
from gui_music_downloader.backend.music_services.models import AuthTokens


def test_map_track_transforms_apple_payload():
    service = AppleMusicService(
        token_store=None,
        developer_token="dev",
        music_user_token="user",
    )

    resource = {
        "id": "track.123",
        "attributes": {
            "name": "Song Title",
            "artistName": "Artist Name",
            "albumName": "Album Name",
            "albumArtistName": "Album Artist",
            "durationInMillis": 187000,
            "isrc": "USABC1234567",
            "discNumber": 1,
            "trackNumber": 4,
            "releaseDate": "2023-01-01",
            "contentRating": "explicit",
            "url": "https://music.apple.com/track",
            "playParams": {"id": "track.123", "kind": "song"},
            "artwork": {
                "url": "https://is{w}x{h}-example.mzstatic.com/image.jpg",
            },
        },
    }

    track = service._map_track(resource)

    assert track is not None
    assert track.track_id == "track.123"
    assert track.name == "Song Title"
    assert track.album == "Album Name"
    assert track.artists == ["Artist Name"]
    assert track.album_artist == "Album Artist"
    assert track.explicit is True
    assert track.artwork_url == "https://is512x512-example.mzstatic.com/image.jpg"
    assert track.metadata["play_params"]["id"] == "track.123"


def test_fetch_library_returns_snapshot(monkeypatch):
    service = AppleMusicService(
        token_store=None,
        developer_token="dev",
        music_user_token="user",
    )

    # Ensure tokens are treated as valid during the test
    service._tokens = AuthTokens(access_token="user-token")

    playlist_resource = {
        "id": "pl.123",
        "attributes": {
            "name": "Favorites Mix",
            "trackCount": 1,
            "curatorName": "Me",
            "artwork": {"url": "https://img{w}x{h}.png"},
        },
    }

    track_resource = {
        "id": "track.1",
        "attributes": {
            "name": "Song Title",
            "artistName": "Artist",
            "albumName": "Album",
            "durationInMillis": 200000,
        },
    }

    def fake_paginate(self, path, params=None):
        if path == "/me/library/playlists":
            yield playlist_resource
        elif path == "/me/library/playlists/pl.123/tracks":
            yield track_resource
        elif path == "/me/library/songs":
            yield track_resource
        else:
            return

    monkeypatch.setattr(service, "_paginate", fake_paginate.__get__(service, AppleMusicService))

    snapshot = service.fetch_library()

    assert snapshot.playlists
    assert snapshot.playlists[0].tracks
    assert snapshot.liked_tracks
    assert snapshot.liked_tracks[0].name == "Song Title"


class FakeAuthenticator:
    def __init__(self, token: str = "issued-token"):
        self.token = token
        self.called_with: str | None = None
        self.timeout: int | None = None

    def request_user_token(self, developer_token: str, timeout: int = 300) -> str:
        self.called_with = developer_token
        self.timeout = timeout
        return self.token


def test_authenticate_uses_musickit_authenticator():
    fake_auth = FakeAuthenticator("music-user-token")
    service = AppleMusicService(
        token_store=None,
        developer_token="dev-token",
        authenticator=fake_auth,
    )

    service._tokens = None
    tokens = service.authenticate(interactive=True)

    assert fake_auth.called_with == "dev-token"
    assert tokens.access_token == "music-user-token"
    assert service.is_authenticated()
