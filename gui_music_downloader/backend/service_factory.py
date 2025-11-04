"""
Helpers for constructing backend service instances from configuration.
"""
from __future__ import annotations

import logging
from typing import Optional

from .config_manager import get_config
from .library_manager import LibraryManager
from .music_services import (
    AppleMusicService,
    FileTokenStore,
    SpotifyService,
    TrackResolver,
)
from ..utils import constants

logger = logging.getLogger(__name__)

_library_manager: Optional[LibraryManager] = None


def get_library_manager(force_refresh: bool = False) -> LibraryManager:
    """
    Return a singleton LibraryManager configured with enabled services.
    """
    global _library_manager
    if _library_manager is not None and not force_refresh:
        return _library_manager

    config = get_config()
    token_store = FileTokenStore(constants.TOKENS_FILE)
    resolver = TrackResolver()

    manager = LibraryManager(resolver=resolver)

    _configure_spotify(manager, config, token_store)
    _configure_apple_music(manager, config, token_store)

    _library_manager = manager
    return manager


def _configure_spotify(manager: LibraryManager, config, token_store: FileTokenStore) -> None:
    spotify_cfg = config.get("services.spotify", {}) or {}
    if not spotify_cfg.get("enabled"):
        logger.info("Spotify service disabled in configuration")
        return

    client_id = spotify_cfg.get("client_id") or None
    client_secret = spotify_cfg.get("client_secret") or None

    if not client_id:
        logger.warning("Spotify service enabled but client_id is missing; skipping registration")
        return

    include_playlists = bool(spotify_cfg.get("include_playlists", True))
    include_liked = bool(spotify_cfg.get("include_liked", True))

    service = SpotifyService(
        token_store=token_store,
        client_id=client_id,
        client_secret=client_secret,
        include_playlists=include_playlists,
        include_liked=include_liked,
    )
    manager.register_service(service)


def _configure_apple_music(manager: LibraryManager, config, token_store: FileTokenStore) -> None:
    apple_cfg = config.get("services.apple_music", {}) or {}
    if not apple_cfg.get("enabled"):
        logger.info("Apple Music service disabled in configuration")
        return

    developer_token = apple_cfg.get("developer_token") or None
    if not developer_token:
        logger.warning("Apple Music service enabled but developer_token missing; skipping registration")
        return

    include_library = bool(apple_cfg.get("include_library", True))
    include_playlists = bool(apple_cfg.get("include_playlists", True))

    service = AppleMusicService(
        token_store=token_store,
        developer_token=developer_token,
        include_library=include_library,
        include_playlists=include_playlists,
    )
    manager.register_service(service)
