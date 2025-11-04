"""
Spotify integration implementation.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import secrets
import string
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Iterable, Iterator, List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from .base import MusicServiceClient
from .models import (
    AuthTokens,
    LibrarySnapshot,
    Playlist,
    StreamingTrack,
)

logger = logging.getLogger(__name__)

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"

DEFAULT_SCOPES = [
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-library-read",
]


@dataclass
class _AuthorizationResult:
    code: Optional[str] = None
    error: Optional[str] = None
    state: Optional[str] = None


class SpotifyService(MusicServiceClient):
    """Handles Spotify authentication and library retrieval."""

    service_name = "spotify"

    def __init__(
        self,
        token_store=None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: str = "http://127.0.0.1:8765/callback",
        scopes: Optional[List[str]] = None,
        session: Optional[requests.Session] = None,
        include_playlists: bool = True,
        include_liked: bool = True,
    ):
        super().__init__(token_store=token_store)
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._scopes = scopes or DEFAULT_SCOPES
        self._session = session or requests.Session()
        self._tokens: Optional[AuthTokens] = self.load_tokens()
        self._include_playlists = include_playlists
        self._include_liked = include_liked

    # ------------------------------------------------------------------ #
    # Authentication
    # ------------------------------------------------------------------ #
    def authenticate(self, interactive: bool = True) -> AuthTokens:
        """
        Perform Authorization Code flow with PKCE.

        Launches a local HTTP server to capture the redirect from Spotify.
        """
        if not interactive:
            raise RuntimeError("Spotify authentication requires interactive flag")
        if not self._client_id:
            raise RuntimeError("Spotify client_id must be configured")

        code_verifier = self._generate_code_verifier()
        code_challenge = self._generate_code_challenge(code_verifier)

        state = secrets.token_urlsafe(16)
        auth_params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": self._redirect_uri,
            "code_challenge_method": "S256",
            "code_challenge": code_challenge,
            "scope": " ".join(self._scopes),
            "state": state,
        }
        auth_url = f"{AUTH_URL}?{urlencode(auth_params)}"

        logger.info("Authorize Spotify by visiting the following URL:\n%s", auth_url)

        result = self._await_authorization(state)
        if result.error:
            raise RuntimeError(f"Spotify authorization failed: {result.error}")
        if not result.code:
            raise RuntimeError("Spotify authorization did not return a code")

        tokens = self._exchange_code(
            code=result.code,
            code_verifier=code_verifier,
        )
        self._tokens = tokens
        self.persist_tokens(tokens)
        logger.info("Spotify authorization completed successfully")
        return tokens

    def refresh_tokens(self) -> AuthTokens:
        """
        Refresh the access token using the stored refresh token.
        """
        if not self._tokens or not self._tokens.refresh_token:
            raise RuntimeError("Spotify refresh token is not available")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._tokens.refresh_token,
            "client_id": self._client_id,
        }
        if self._client_secret:
            payload["client_secret"] = self._client_secret

        response = self._session.post(
            TOKEN_URL,
            data=payload,
            timeout=15,
        )
        self._raise_for_status(response)
        token_data = response.json()
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in))

        new_tokens = AuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", self._tokens.refresh_token),
            expires_at=expires_at,
            scope=token_data.get("scope"),
            token_type=token_data.get("token_type", "Bearer"),
            raw=token_data,
        )

        self._tokens = new_tokens
        self.persist_tokens(new_tokens)
        logger.info("Spotify access token refreshed")
        return new_tokens

    def is_authenticated(self) -> bool:
        return bool(self._tokens) and not self._tokens.is_expired

    # ------------------------------------------------------------------ #
    # Library retrieval
    # ------------------------------------------------------------------ #
    def fetch_library(self) -> LibrarySnapshot:
        """
        Retrieve playlists and liked songs for the authenticated user.
        """
        self._ensure_access_token()

        logger.info("Fetching Spotify library")
        snapshot = LibrarySnapshot(service=self.service_name, fetched_at=datetime.now(UTC))

        profile = self._api_get("/me")
        snapshot.metadata.update(
            {
                "user_id": profile.get("id"),
                "display_name": profile.get("display_name"),
                "product": profile.get("product"),
            }
        )

        if self._include_playlists:
            snapshot.playlists = self._fetch_playlists()

        if self._include_liked:
            snapshot.liked_tracks = list(self._iter_saved_tracks())

        logger.info(
            "Fetched Spotify library: %d playlists, %d liked tracks",
            len(snapshot.playlists),
            len(snapshot.liked_tracks),
        )
        return snapshot

    def iter_tracks(self, playlist_id: Optional[str] = None) -> Iterable[StreamingTrack]:
        """
        Yield tracks for an entire library or a specific playlist.
        """
        self._ensure_access_token()

        if playlist_id:
            yield from self._iter_playlist_tracks(playlist_id)
        else:
            yield from self._iter_saved_tracks()

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _ensure_access_token(self) -> None:
        if not self._tokens:
            raise RuntimeError("Spotify client is not authenticated")
        if self._tokens.is_expired:
            self.refresh_tokens()

    def _headers(self) -> Dict[str, str]:
        if not self._tokens:
            raise RuntimeError("Spotify tokens are missing")
        return {"Authorization": f"Bearer {self._tokens.access_token}"}

    def _api_get(self, path: str, params: Optional[Dict[str, str]] = None) -> dict:
        url = f"{API_BASE_URL}{path}"
        for attempt in range(2):
            response = self._session.get(url, headers=self._headers(), params=params, timeout=15)
            if response.status_code == 401 and attempt == 0:
                logger.info("Spotify request unauthorized, refreshing token")
                self.refresh_tokens()
                continue
            self._raise_for_status(response)
            return response.json()
        raise RuntimeError("Spotify API request failed after token refresh")

    def _paginate(self, path: str, params: Optional[Dict[str, str]] = None) -> Iterator[dict]:
        next_url = f"{API_BASE_URL}{path}"
        current_params = params or {}

        while next_url:
            response = self._session.get(
                next_url,
                headers=self._headers(),
                params=current_params if next_url.endswith(path) else None,
                timeout=15,
            )
            if response.status_code == 401:
                self.refresh_tokens()
                continue
            self._raise_for_status(response)
            payload = response.json()
            for item in payload.get("items", []):
                yield item
            next_url = payload.get("next")
            current_params = None

    def _iter_playlist_tracks(self, playlist_id: str) -> Iterator[StreamingTrack]:
        logger.info("Fetching tracks for playlist %s", playlist_id)
        for item in self._paginate(f"/playlists/{playlist_id}/tracks", params={"limit": 100}):
            track = self._map_track(item)
            if track:
                yield track

    def _iter_saved_tracks(self) -> Iterator[StreamingTrack]:
        logger.info("Fetching saved tracks")
        for item in self._paginate("/me/tracks", params={"limit": 50}):
            track = self._map_track(item)
            if track:
                yield track

    def _fetch_playlists(self) -> List[Playlist]:
        playlists: List[Playlist] = []
        for item in self._paginate("/me/playlists", params={"limit": 50}):
            playlist = self._map_playlist(item)
            playlist.tracks = list(self._iter_playlist_tracks(playlist.playlist_id))
            playlists.append(playlist)
        return playlists

    def _map_playlist(self, data: dict) -> Playlist:
        images = data.get("images", [])
        artwork_url = self._select_image(images)
        owner = data.get("owner") or {}
        owner_name = owner.get("display_name") or owner.get("id")
        return Playlist(
            service=self.service_name,
            playlist_id=data.get("id") or "",
            name=data.get("name") or "Untitled Playlist",
            description=data.get("description"),
            owner=owner_name,
            track_count=data.get("tracks", {}).get("total", 0),
            artwork_url=artwork_url,
        )

    def _map_track(self, item: dict) -> Optional[StreamingTrack]:
        """
        Convert raw Spotify API payloads into StreamingTrack objects.
        Handles playlist items, saved tracks, and filters unsupported entries (episodes/local).
        """
        track = item.get("track") if isinstance(item, dict) else None
        track = track or item  # Saved tracks may pass the track directly.
        if not track or not isinstance(track, dict):
            return None

        if track.get("is_local"):
            logger.debug("Skipping local track %s", track.get("uri"))
            return None

        track_type = track.get("type")
        if track_type and track_type.lower() != "track":
            logger.debug("Skipping non-track entry type=%s", track_type)
            return None

        album = track.get("album") or {}
        album_artists = album.get("artists") or []
        images = album.get("images") or []

        artists = [artist.get("name") for artist in track.get("artists", []) if artist.get("name")]
        album_artist = album_artists[0]["name"] if album_artists else None
        artwork_url = self._select_image(images)

        external_ids = track.get("external_ids") or {}
        metadata = {
            "uri": track.get("uri"),
            "preview_url": track.get("preview_url"),
            "external_url": (track.get("external_urls") or {}).get("spotify"),
            "added_at": item.get("added_at") if isinstance(item, dict) else None,
            "available_markets": track.get("available_markets"),
        }

        return StreamingTrack(
            service=self.service_name,
            track_id=track.get("id") or "",
            name=track.get("name") or "Unknown Track",
            artists=artists,
            album=album.get("name") or "",
            album_artist=album_artist,
            duration_ms=track.get("duration_ms"),
            isrc=external_ids.get("isrc"),
            artwork_url=artwork_url,
            disc_number=track.get("disc_number"),
            track_number=track.get("track_number"),
            explicit=track.get("explicit"),
            release_date=album.get("release_date"),
            metadata=metadata,
        )

    # ------------------------------------------------------------------ #
    # Authorization helpers
    # ------------------------------------------------------------------ #
    def _await_authorization(self, expected_state: str, timeout: int = 300) -> _AuthorizationResult:
        """
        Start a local HTTP server to receive the OAuth callback.
        """
        parsed = urlparse(self._redirect_uri)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 8765

        result = _AuthorizationResult(state=expected_state)
        event = threading.Event()

        class CallbackHandler(BaseHTTPRequestHandler):
            server_version = "SpotifyAuthServer/1.0"

            def do_GET(self):  # type: ignore[override]
                nonlocal result
                query = parse_qs(urlparse(self.path).query)
                received_state = query.get("state", [None])[0]
                code = query.get("code", [None])[0]
                error = query.get("error", [None])[0]

                if received_state != expected_state:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"State mismatch. Authorization aborted.")
                    result.error = "state_mismatch"
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"You can close this window.")
                    result.code = code
                    result.error = error

                event.set()

            def log_message(self, format, *args):
                return  # Suppress HTTP server logging

        server = HTTPServer((host, port), CallbackHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        logger.info("Waiting for Spotify authorization callback on %s:%s", host, port)
        finished = event.wait(timeout=timeout)
        server.shutdown()
        server_thread.join(timeout=5)

        if not finished:
            result.error = "timeout"
            logger.error("Spotify authorization timed out after %ss", timeout)
        return result

    def _exchange_code(self, code: str, code_verifier: str) -> AuthTokens:
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._redirect_uri,
            "client_id": self._client_id,
            "code_verifier": code_verifier,
        }
        if self._client_secret:
            payload["client_secret"] = self._client_secret

        response = self._session.post(TOKEN_URL, data=payload, timeout=15)
        self._raise_for_status(response)
        data = response.json()

        expires_in = data.get("expires_in", 3600)
        expires_at = datetime.now(UTC) + timedelta(seconds=int(expires_in))

        return AuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            scope=data.get("scope"),
            token_type=data.get("token_type", "Bearer"),
            raw=data,
        )

    # ------------------------------------------------------------------ #
    # Utility helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _generate_code_verifier(length: int = 128) -> str:
        alphabet = string.ascii_letters + string.digits + "-._~"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def _generate_code_challenge(code_verifier: str) -> str:
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    @staticmethod
    def _select_image(images: List[dict]) -> Optional[str]:
        if not images:
            return None
        sorted_images = sorted(
            (img for img in images if img.get("url")),
            key=lambda img: img.get("width", 0),
            reverse=True,
        )
        return sorted_images[0]["url"] if sorted_images else None

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            message = f"Spotify API error: {payload}"
            raise RuntimeError(message) from exc
