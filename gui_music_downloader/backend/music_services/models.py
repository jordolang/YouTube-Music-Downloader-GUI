"""
Shared dataclasses for music service integrations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Dict, List, Optional


@dataclass
class AuthTokens:
    """
    Represents the access/refresh credentials returned by a music service.
    """
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    token_type: str = "Bearer"
    raw: Dict[str, str] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check whether the token is past its expiry time."""
        if not self.expires_at:
            return False
        return datetime.now(UTC) >= self.expires_at


@dataclass
class StreamingTrack:
    """
    Canonical representation of a track sourced from a streaming service.
    """
    service: str
    track_id: str
    name: str
    artists: List[str]
    album: str
    album_artist: Optional[str] = None
    duration_ms: Optional[int] = None
    isrc: Optional[str] = None
    artwork_url: Optional[str] = None
    disc_number: Optional[int] = None
    track_number: Optional[int] = None
    explicit: Optional[bool] = None
    release_date: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def display_artist(self) -> str:
        """Return a human readable artist string."""
        return ", ".join(self.artists) if self.artists else self.album_artist or "Unknown"

    def canonical_query(self) -> str:
        """Build a deterministic search query for resolver heuristics."""
        pieces = [self.display_artist(), self.name]
        if self.album:
            pieces.append(self.album)
        return " ".join(filter(None, pieces))


@dataclass
class Playlist:
    """Represents a playlist or library collection."""
    service: str
    playlist_id: str
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    track_count: int = 0
    artwork_url: Optional[str] = None
    tracks: List[StreamingTrack] = field(default_factory=list)


@dataclass
class LibrarySnapshot:
    """Summary of fetched library data."""
    service: str
    fetched_at: datetime
    playlists: List[Playlist] = field(default_factory=list)
    liked_tracks: List[StreamingTrack] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResolutionCandidate:
    """Potential YouTube match for a streaming track."""
    youtube_id: str
    url: str
    title: str
    channel: str
    score: float
    duration_sec: Optional[int] = None
    view_count: Optional[int] = None
    reason: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ResolvedTrack:
    """Final mapping between streaming track and YouTube source."""
    track: StreamingTrack
    candidate: ResolutionCandidate
    confidence: float
    manual_override: bool = False
    notes: Optional[str] = None
