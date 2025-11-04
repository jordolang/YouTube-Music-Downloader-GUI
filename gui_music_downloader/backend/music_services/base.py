"""
Abstract base classes for music service integrations.
"""
from __future__ import annotations

import abc
from typing import Iterable, Optional

from .models import (
    AuthTokens,
    LibrarySnapshot,
    ResolutionCandidate,
    StreamingTrack,
)


class MusicServiceClient(abc.ABC):
    """
    Base contract for Spotify/Apple Music or any future streaming clients.
    """

    service_name: str

    def __init__(self, token_store: Optional["TokenStore"] = None):
        self._token_store = token_store

    @abc.abstractmethod
    def authenticate(self, interactive: bool = True) -> AuthTokens:
        """
        Perform initial authentication.

        Returns:
            AuthTokens representing the current session.
        """

    @abc.abstractmethod
    def refresh_tokens(self) -> AuthTokens:
        """Refresh and persist tokens when expired."""

    @abc.abstractmethod
    def is_authenticated(self) -> bool:
        """Return whether the client currently has valid credentials."""

    @abc.abstractmethod
    def fetch_library(self) -> LibrarySnapshot:
        """Return a snapshot of playlists and liked tracks."""

    @abc.abstractmethod
    def iter_tracks(self, playlist_id: Optional[str] = None) -> Iterable[StreamingTrack]:
        """Yield tracks for the entire library or a specific playlist."""

    def resolve_track(self, track: StreamingTrack) -> Optional[ResolutionCandidate]:
        """
        Services may override to provide first-party matching (e.g., ISRC lookup).
        Default implementation returns None and defers to the YouTube resolver.
        """
        return None

    def persist_tokens(self, tokens: AuthTokens) -> None:
        """Persist credentials using the configured token store."""
        if self._token_store:
            self._token_store.save(self.service_name, tokens)

    def load_tokens(self) -> Optional[AuthTokens]:
        """Load credentials via token store if available."""
        if not self._token_store:
            return None
        return self._token_store.load(self.service_name)

    def logout(self) -> None:
        """Forget stored credentials."""
        if self._token_store:
            self._token_store.delete(self.service_name)


class TokenStore(abc.ABC):
    """Abstract token persistence layer."""

    @abc.abstractmethod
    def load(self, service: str) -> Optional[AuthTokens]:
        """Return stored tokens for the service, if any."""

    @abc.abstractmethod
    def save(self, service: str, tokens: AuthTokens) -> None:
        """Persist tokens for future use."""

    @abc.abstractmethod
    def delete(self, service: str) -> None:
        """Remove cached tokens."""
