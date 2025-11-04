"""
Coordinates music-service sync jobs and resolution pipeline.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Callable, Dict, List, Optional

from .music_services import (
    MusicServiceClient,
    ResolvedTrack,
    TrackResolver,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, "SyncProgress"], None]


@dataclass
class SyncProgress:
    """Represents sync status for observers/GUI."""

    service: str
    state: str  # idle, authenticating, fetching, resolving, completed, error
    detail: Optional[str] = None
    current: int = 0
    total: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: Optional[datetime] = None


class LibraryManager:
    """
    Orchestrates end-to-end synchronization from streaming services to download queue.
    """

    def __init__(self, resolver: Optional[TrackResolver] = None):
        self._services: Dict[str, MusicServiceClient] = {}
        self._resolver = resolver or TrackResolver()
        self._listeners: List[ProgressCallback] = []

    def register_service(self, service: MusicServiceClient) -> None:
        logger.info("Registering music service: %s", service.service_name)
        self._services[service.service_name] = service

    def get_service(self, service_name: str) -> Optional[MusicServiceClient]:
        return self._services.get(service_name)

    def list_services(self) -> List[str]:
        """Return registered service identifiers."""
        return sorted(self._services.keys())

    def subscribe(self, callback: ProgressCallback) -> None:
        """Register a listener for progress updates."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unsubscribe(self, callback: ProgressCallback) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def sync_service(
        self,
        service_name: str,
        auto_resolve: bool = True,
    ) -> List[ResolvedTrack]:
        """
        Fetch library content for a service and resolve tracks to YouTube candidates.
        """
        service = self._services.get(service_name)
        if not service:
            raise ValueError(f"Service '{service_name}' is not registered")

        progress = SyncProgress(service=service_name, state="fetching")
        self._notify("start", progress)

        try:
            snapshot = service.fetch_library()
            total_tracks = sum(len(pl.tracks) for pl in snapshot.playlists) + len(snapshot.liked_tracks)
            progress.total = total_tracks

            resolved: List[ResolvedTrack] = []

            # Resolve playlists
            for playlist in snapshot.playlists:
                for track in playlist.tracks:
                    progress.current += 1
                    progress.state = "resolving"
                    progress.detail = f"{playlist.name} - {track.name}"
                    self._notify("progress", progress)

                    candidate = None
                    if auto_resolve:
                        candidate = service.resolve_track(track) or self._resolver.pick_best(track)

                    if candidate:
                        resolved.append(ResolvedTrack(track=track, candidate=candidate, confidence=candidate.score))
                    else:
                        logger.info("No candidate found for %s - %s", track.display_artist(), track.name)

            # Resolve liked tracks
            for track in snapshot.liked_tracks:
                progress.current += 1
                progress.state = "resolving"
                progress.detail = f"Liked - {track.name}"
                self._notify("progress", progress)

                candidate = None
                if auto_resolve:
                    candidate = service.resolve_track(track) or self._resolver.pick_best(track)

                if candidate:
                    resolved.append(ResolvedTrack(track=track, candidate=candidate, confidence=candidate.score))

            progress.state = "completed"
            progress.finished_at = datetime.now(UTC)
            self._notify("completed", progress)
            return resolved

        except Exception as exc:
            progress.state = "error"
            progress.detail = str(exc)
            progress.finished_at = datetime.now(UTC)
            self._notify("error", progress)
            logger.exception("Failed to sync service %s", service_name)
            raise

    def _notify(self, event: str, progress: SyncProgress) -> None:
        for listener in list(self._listeners):
            try:
                listener(event, progress)
            except Exception as exc:
                logger.warning("LibraryManager listener error: %s", exc)
