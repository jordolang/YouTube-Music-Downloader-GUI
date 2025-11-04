"""
Music service integration package.
"""
from .apple_music import AppleMusicService
from .auth import FileTokenStore
from .base import MusicServiceClient, TokenStore
from .models import (
    AuthTokens,
    LibrarySnapshot,
    Playlist,
    ResolutionCandidate,
    ResolvedTrack,
    StreamingTrack,
)
from .resolver import TrackResolver
from .spotify import SpotifyService
from .musickit_auth import MusicKitAuthenticator

__all__ = [
    "AppleMusicService",
    "AuthTokens",
    "FileTokenStore",
    "LibrarySnapshot",
    "MusicServiceClient",
    "Playlist",
    "ResolutionCandidate",
    "ResolvedTrack",
    "StreamingTrack",
    "TokenStore",
    "TrackResolver",
    "SpotifyService",
    "MusicKitAuthenticator",
]
