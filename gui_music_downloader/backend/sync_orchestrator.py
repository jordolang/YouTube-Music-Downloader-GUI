"""
Coordinates library syncs and download queue population.
"""
from __future__ import annotations

from typing import List, Optional

from .library_manager import LibraryManager
from .music_services.models import ResolvedTrack
from .queue_manager import QueueItem, QueueManager, get_queue_manager
from .service_factory import get_library_manager
from ..utils import constants


class SyncOrchestrator:
    """
    High-level helper that syncs a service and enqueues downloads.
    """

    def __init__(
        self,
        library_manager: Optional[LibraryManager] = None,
        queue_manager: Optional[QueueManager] = None,
    ):
        self._library_manager = library_manager or get_library_manager()
        self._queue_manager = queue_manager or get_queue_manager()

    def sync(self, service: str, auto_resolve: bool = True) -> List[ResolvedTrack]:
        """Run the service sync and return resolved tracks."""
        return self._library_manager.sync_service(service, auto_resolve=auto_resolve)

    def sync_and_enqueue(
        self,
        service: str,
        auto_resolve: bool = True,
    ) -> List[QueueItem]:
        """Sync a service and enqueue resulting resolved tracks."""
        resolved_tracks = self.sync(service, auto_resolve=auto_resolve)
        queue_items = [self._queue_manager.enqueue(resolved) for resolved in resolved_tracks]
        return queue_items
