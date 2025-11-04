"""
Apple Music integration.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Dict, Iterable, Iterator, List, Optional

import requests

from .base import MusicServiceClient
from .models import AuthTokens, LibrarySnapshot, Playlist, StreamingTrack
from .musickit_auth import MusicKitAuthenticator

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.music.apple.com/v1"


class AppleMusicService(MusicServiceClient):
    """Handles Apple Music authentication and library retrieval."""

    service_name = "apple_music"

    def __init__(
        self,
        token_store=None,
        developer_token: Optional[str] = None,
        music_user_token: Optional[str] = None,
        include_library: bool = True,
        include_playlists: bool = True,
        session: Optional[requests.Session] = None,
        authenticator: Optional[MusicKitAuthenticator] = None,
    ):
        super().__init__(token_store=token_store)
        self._developer_token = developer_token
        self._session = session or requests.Session()
        self._tokens: Optional[AuthTokens] = self.load_tokens()
        if music_user_token and not self._tokens:
            self._tokens = AuthTokens(access_token=music_user_token)
            self.persist_tokens(self._tokens)
        self._include_library = include_library
        self._include_playlists = include_playlists
        self._authenticator = authenticator

    # ------------------------------------------------------------------ #
    # Authentication
    # ------------------------------------------------------------------ #
    def authenticate(self, interactive: bool = True) -> AuthTokens:
        """
        Apple Music authentication currently requires a pre-generated Music User Token.

        The application expects the token to be supplied via configuration or token store.
        """
        if self._tokens and self._tokens.access_token:
            return self._tokens
        if not self._developer_token:
            raise RuntimeError("Apple Music developer token is required")
        if not interactive:
            raise RuntimeError(
                "Apple Music authentication requires a Music User Token. "
                "Provide one via the settings UI or token store."
            )

        authenticator = self._authenticator or MusicKitAuthenticator()
        logger.info("Launching MusicKit authentication flow")
        token = authenticator.request_user_token(self._developer_token)
        if not token:
            raise RuntimeError("Failed to retrieve Music User Token from MusicKit")

        self._tokens = AuthTokens(access_token=token)
        self.persist_tokens(self._tokens)
        logger.info("Received Apple Music Music User Token")
        return self._tokens

    def refresh_tokens(self) -> AuthTokens:
        """
        Apple Music user tokens are long-lived and do not support refresh via API.
        """
        if not self._tokens or not self._tokens.access_token:
            raise RuntimeError("Apple Music tokens are not available")
        return self._tokens

    def is_authenticated(self) -> bool:
        return bool(self._developer_token) and bool(self._tokens and self._tokens.access_token)

    # ------------------------------------------------------------------ #
    # Library retrieval
    # ------------------------------------------------------------------ #
    def fetch_library(self) -> LibrarySnapshot:
        self._ensure_authenticated()

        snapshot = LibrarySnapshot(service=self.service_name, fetched_at=datetime.now(UTC))

        if self._include_playlists:
            snapshot.playlists = self._fetch_playlists()

        if self._include_library:
            snapshot.liked_tracks = list(self._iter_library_songs())

        logger.info(
            "Fetched Apple Music library: %d playlists, %d liked tracks",
            len(snapshot.playlists),
            len(snapshot.liked_tracks),
        )
        return snapshot

    def iter_tracks(self, playlist_id: Optional[str] = None) -> Iterable[StreamingTrack]:
        self._ensure_authenticated()

        if playlist_id:
            yield from self._iter_playlist_tracks(playlist_id)
        else:
            yield from self._iter_library_songs()

    # ------------------------------------------------------------------ #
    # Playlist helpers
    # ------------------------------------------------------------------ #
    def _fetch_playlists(self) -> List[Playlist]:
        playlists: List[Playlist] = []
        for item in self._paginate("/me/library/playlists", params={"limit": 100}):
            playlist = self._map_playlist(item)
            playlist.tracks = list(self._iter_playlist_tracks(playlist.playlist_id))
            playlists.append(playlist)
        return playlists

    def _iter_playlist_tracks(self, playlist_id: str) -> Iterator[StreamingTrack]:
        for item in self._paginate(f"/me/library/playlists/{playlist_id}/tracks", params={"limit": 100}):
            track = self._map_track(item)
            if track:
                yield track

    def _iter_library_songs(self) -> Iterator[StreamingTrack]:
        for item in self._paginate("/me/library/songs", params={"limit": 100}):
            track = self._map_track(item)
            if track:
                yield track

    # ------------------------------------------------------------------ #
    # Mapping helpers
    # ------------------------------------------------------------------ #
    def _map_playlist(self, data: dict) -> Playlist:
        attributes = data.get("attributes") or {}
        artwork_url = self._format_artwork(attributes.get("artwork"))
        owner = attributes.get("curatorName") or "Me"
        track_count = attributes.get("trackCount") or 0
        return Playlist(
            service=self.service_name,
            playlist_id=data.get("id") or "",
            name=attributes.get("name") or "Untitled Playlist",
            description=attributes.get("description", {}).get("standard"),
            owner=owner,
            track_count=track_count,
            artwork_url=artwork_url,
        )

    def _map_track(self, resource: dict) -> Optional[StreamingTrack]:
        attributes = resource.get("attributes") or {}
        if not attributes:
            return None

        artist_name = attributes.get("artistName") or ""
        album_name = attributes.get("albumName") or ""
        artwork_url = self._format_artwork(attributes.get("artwork"))

        metadata = {
            "url": attributes.get("url"),
            "play_params": attributes.get("playParams"),
        }

        return StreamingTrack(
            service=self.service_name,
            track_id=resource.get("id") or "",
            name=attributes.get("name") or "Unknown Track",
            artists=[artist_name] if artist_name else [],
            album=album_name,
            album_artist=attributes.get("albumArtistName") or artist_name or None,
            duration_ms=attributes.get("durationInMillis"),
            isrc=attributes.get("isrc"),
            artwork_url=artwork_url,
            disc_number=attributes.get("discNumber"),
            track_number=attributes.get("trackNumber"),
            explicit=attributes.get("contentRating") == "explicit",
            release_date=attributes.get("releaseDate"),
            metadata=metadata,
        )

    @staticmethod
    def _format_artwork(artwork: Optional[dict], size: int = 512) -> Optional[str]:
        if not artwork:
            return None
        url = artwork.get("url")
        if not url:
            return None
        return url.replace("{w}", str(size)).replace("{h}", str(size))

    # ------------------------------------------------------------------ #
    # HTTP helpers
    # ------------------------------------------------------------------ #
    def _ensure_authenticated(self) -> None:
        if not self.is_authenticated():
            raise RuntimeError("Apple Music client is not authenticated")

    def _headers(self) -> Dict[str, str]:
        if not self._developer_token:
            raise RuntimeError("Apple Music developer token is required")
        if not self._tokens or not self._tokens.access_token:
            raise RuntimeError("Apple Music Music User Token is missing")
        return {
            "Authorization": f"Bearer {self._developer_token}",
            "Music-User-Token": self._tokens.access_token,
        }

    def _api_get(self, path: str, params: Optional[Dict[str, str]] = None) -> dict:
        url = f"{API_BASE_URL}{path}"
        response = self._session.get(url, headers=self._headers(), params=params, timeout=20)
        self._raise_for_status(response)
        return response.json()

    def _paginate(self, path: str, params: Optional[Dict[str, str]] = None) -> Iterator[dict]:
        next_url: Optional[str] = f"{API_BASE_URL}{path}"
        current_params = params or {}

        while next_url:
            response = self._session.get(
                next_url,
                headers=self._headers(),
                params=current_params if next_url.endswith(path) else None,
                timeout=20,
            )
            self._raise_for_status(response)
            payload = response.json()
            for item in payload.get("data", []):
                yield item
            next_url = payload.get("next")
            current_params = None

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            message = f"Apple Music API error: {payload}"
            raise RuntimeError(message) from exc
