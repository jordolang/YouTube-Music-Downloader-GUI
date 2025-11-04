"""
Backend exports.
"""
from .config_manager import ConfigManager, get_config
from .library_manager import LibraryManager, SyncProgress
from .music_services import (
    AppleMusicService,
    FileTokenStore,
    MusicServiceClient,
    SpotifyService,
    TrackResolver,
)
from .queue_manager import QueueItem, QueueManager, get_queue_manager
from .service_factory import get_library_manager
from .sync_orchestrator import SyncOrchestrator

__all__ = [
    "AppleMusicService",
    "ConfigManager",
    "FileTokenStore",
    "LibraryManager",
    "MusicServiceClient",
    "QueueItem",
    "QueueManager",
    "SpotifyService",
    "SyncProgress",
    "TrackResolver",
    "SyncOrchestrator",
    "get_library_manager",
    "get_queue_manager",
    "get_config",
]
