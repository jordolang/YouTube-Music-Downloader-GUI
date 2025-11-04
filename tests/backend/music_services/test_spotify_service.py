from gui_music_downloader.backend.music_services.spotify import SpotifyService


def test_map_track_transforms_spotify_payload():
    service = SpotifyService(token_store=None, client_id="client")
    raw_item = {
        "track": {
            "id": "track123",
            "name": "Song Title",
            "duration_ms": 210000,
            "explicit": False,
            "disc_number": 1,
            "track_number": 3,
            "preview_url": "https://example.com/preview.mp3",
            "uri": "spotify:track:track123",
            "external_urls": {"spotify": "https://open.spotify.com/track/track123"},
            "external_ids": {"isrc": "USRC17607839"},
            "artists": [{"name": "Artist One"}, {"name": "Artist Two"}],
            "album": {
                "name": "Album Name",
                "release_date": "2024-01-01",
                "artists": [{"name": "Album Artist"}],
                "images": [
                    {"url": "https://img-small", "width": 64},
                    {"url": "https://img-large", "width": 640},
                ],
            },
        }
    }

    track = service._map_track(raw_item)

    assert track is not None
    assert track.track_id == "track123"
    assert track.name == "Song Title"
    assert track.artists == ["Artist One", "Artist Two"]
    assert track.album == "Album Name"
    assert track.album_artist == "Album Artist"
    assert track.artwork_url == "https://img-large"
    assert track.isrc == "USRC17607839"
    assert track.metadata["uri"] == "spotify:track:track123"


def test_map_track_skips_local_and_episodes():
    service = SpotifyService(token_store=None, client_id="client")

    local_track = {"track": {"is_local": True, "uri": "spotify:local:abc"}}
    assert service._map_track(local_track) is None

    episode = {"track": {"type": "episode", "id": "ep1"}}
    assert service._map_track(episode) is None


def test_map_track_captures_added_at_metadata():
    service = SpotifyService(token_store=None, client_id="client")
    raw_item = {
        "added_at": "2024-01-01T12:00:00Z",
        "track": {
            "id": "track456",
            "name": "Track Name",
            "type": "track",
            "artists": [{"name": "Artist"}],
            "album": {"name": "Album", "artists": [{"name": "Artist"}]},
        },
    }

    track = service._map_track(raw_item)
    assert track is not None
    assert track.metadata["added_at"] == "2024-01-01T12:00:00Z"
