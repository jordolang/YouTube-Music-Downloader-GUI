"""
Download queue management for resolved tracks.
"""
from __future__ import annotations

import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .config_manager import get_config
from .downloader import DownloadProgress, get_engine
from .music_services.models import ResolvedTrack, StreamingTrack
from ..utils import constants, helpers

QueueListener = Callable[[str, "QueueItem"], None]


class DownloadCancelledError(Exception):
    """Internal signal used when a queue item is cancelled."""
    pass


@dataclass
class QueueItem:
    """Represents a single download job."""

    id: str
    service: str
    track: StreamingTrack
    output_path: Path
    status: str = "queued"
    candidate_url: str = ""
    percent: float = 0.0
    speed: float = 0.0
    eta: str = ""
    error: Optional[str] = None
    paused: bool = False
    cancel_requested: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    def metadata(self) -> Dict[str, str]:
        """Return metadata dict used for tagging."""
        artist = self.track.display_artist()
        year = (self.track.release_date or "")[:4]
        return {
            "title": self.track.name,
            "artist": artist,
            "album": self.track.album or "",
            "album_artist": self.track.album_artist or artist,
            "year": year,
        }


class QueueManager:
    """
    Threaded download queue that executes resolved tracks via the download engine.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        engine=None,
        synchronous: bool = False,
    ):
        config = get_config()
        workers = max_workers or int(
            config.get(
                "advanced.concurrent_downloads",
                constants.DEFAULT_CONCURRENT_DOWNLOADS,
            )
        )
        self._engine = engine or get_engine()
        self._synchronous = synchronous
        self._executor = (
            None
            if self._synchronous
            else ThreadPoolExecutor(max_workers=workers, thread_name_prefix="download")
        )
        self._items: Dict[str, QueueItem] = {}
        self._futures: Dict[str, Future] = {}
        self._listeners: List[QueueListener] = []
        self._lock = threading.Lock()
        self._pause_events: Dict[str, threading.Event] = {}
        self._duplicate_strategy = config.get(
            "general.duplicate_handling",
            "rename",
        )
        self._quality_label = config.get("general.default_quality", constants.DEFAULT_QUALITY)
        self._bitrate = constants.QUALITY_OPTIONS.get(self._quality_label, 320)
        self._base_dir = Path(config.get("general.save_location", str(constants.DEFAULT_MUSIC_DIR))).expanduser()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def enqueue(self, resolved: ResolvedTrack) -> QueueItem:
        """Add a resolved track to the queue."""
        with self._lock:
            item_id = uuid.uuid4().hex
            output_path = self._build_output_path(resolved.track)
            queue_item = QueueItem(
                id=item_id,
                service=resolved.track.service,
                track=resolved.track,
                output_path=output_path,
                candidate_url=resolved.candidate.url,
            )
            self._items[item_id] = queue_item
            pause_event = threading.Event()
            pause_event.set()
            self._pause_events[item_id] = pause_event
            self._notify("queued", queue_item)
            if self._synchronous:
                future = Future()
                self._futures[item_id] = future
            else:
                future = self._executor.submit(self._run_download, queue_item, resolved)
                self._futures[item_id] = future

        if self._synchronous:
            try:
                self._run_download(queue_item, resolved)
                future.set_result(True)
            except Exception as exc:  # pragma: no cover - synchronous mode ensures propagation
                future.set_exception(exc)
        return queue_item

    def list_items(self) -> List[QueueItem]:
        with self._lock:
            return list(self._items.values())

    def pause(self, item_id: str) -> bool:
        """Pause a queued or in-flight download."""
        with self._lock:
            item = self._items.get(item_id)
            if not item or item.status in {"complete", "error", "cancelled"}:
                return False
            if item.paused:
                return True
            item.paused = True
            pause_event = self._pause_events.get(item_id)
            if pause_event:
                pause_event.clear()
            item.status = "paused"
        self._notify("paused", item)
        return True

    def resume(self, item_id: str) -> bool:
        """Resume a paused download."""
        with self._lock:
            item = self._items.get(item_id)
            if not item or not item.paused:
                return False
            item.paused = False
            pause_event = self._pause_events.get(item_id)
            if pause_event:
                pause_event.set()
            if item.cancel_requested:
                return False
            if item.started_at:
                item.status = "downloading"
            else:
                item.status = "queued"
        self._notify("resumed", item)
        return True

    def cancel(self, item_id: str) -> bool:
        """Cancel a queued or active download."""
        mark_now = False
        with self._lock:
            item = self._items.get(item_id)
            if not item or item.status in {"complete", "error", "cancelled"}:
                return False
            item.cancel_requested = True
            pause_event = self._pause_events.get(item_id)
            if pause_event:
                pause_event.set()
            future = self._futures.get(item_id)
            if future and not future.done():
                future.cancel()
            mark_now = item.started_at is None
        if mark_now:
            self._mark_cancelled(item)
        return True

    def subscribe(self, listener: QueueListener) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def unsubscribe(self, listener: QueueListener) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def shutdown(self, wait_for_completion: bool = True) -> None:
        if wait_for_completion:
            self.wait_for_all()
        if self._executor:
            self._executor.shutdown(wait=True)

    def wait_for_all(self, timeout: Optional[float] = None) -> None:
        with self._lock:
            futures = [f for f in self._futures.values() if isinstance(f, Future)]
        if futures:
            wait(futures, timeout=timeout)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _run_download(self, item: QueueItem, resolved: ResolvedTrack) -> None:
        pause_event = self._pause_events.get(item.id)
        if pause_event and not pause_event.is_set():
            while not pause_event.wait(0.1):
                if item.cancel_requested:
                    self._mark_cancelled(item)
                    return

        if item.cancel_requested:
            self._mark_cancelled(item)
            return

        item.status = "downloading"
        item.started_at = datetime.now(UTC)
        self._notify("started", item)

        metadata = item.metadata()
        metadata.update(
            {
                "artwork_url": resolved.track.artwork_url or "",
                "isrc": resolved.track.isrc or "",
            }
        )

        def on_progress(progress: DownloadProgress):
            if pause_event:
                while not pause_event.wait(0.1):
                    if item.cancel_requested:
                        raise DownloadCancelledError()
            if item.cancel_requested:
                raise DownloadCancelledError()
            item.percent = progress.percent
            item.speed = progress.speed
            item.eta = progress.get_formatted_eta()
            if progress.status == "processing":
                item.status = "processing"
            elif progress.status == "downloading":
                item.status = "downloading"
            self._notify("progress", item)

        try:
            success = self._engine.download(
                url=resolved.candidate.url,
                output_path=item.output_path,
                quality=self._bitrate,
                progress_callback=on_progress,
                metadata=metadata,
            )
            if item.cancel_requested:
                raise DownloadCancelledError()
            item.finished_at = datetime.now(UTC)
            if success:
                item.status = "complete"
                item.percent = 100.0
                self._notify("completed", item)
            else:
                item.status = "error"
                item.error = item.error or "Download failed"
                self._notify("error", item)
        except DownloadCancelledError:
            self._mark_cancelled(item)
        except Exception as exc:
            item.finished_at = datetime.now(UTC)
            item.status = "error"
            item.error = str(exc)
            self._notify("error", item)
        finally:
            with self._lock:
                self._pause_events.pop(item.id, None)

    def _build_output_path(self, track: StreamingTrack) -> Path:
        artist = helpers.sanitize_filename(track.display_artist())
        album = helpers.sanitize_filename(track.album) if track.album else None
        title = helpers.sanitize_filename(track.name) or "unknown"

        target_dir = self._base_dir / artist
        if album:
            target_dir = target_dir / album
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / f"{title}.mp3"
        return helpers.resolve_duplicate_path(file_path, strategy=self._duplicate_strategy)

    def _mark_cancelled(self, item: QueueItem) -> None:
        with self._lock:
            self._pause_events.pop(item.id, None)
        item.status = "cancelled"
        item.finished_at = datetime.now(UTC)
        self._notify("cancelled", item)

    def _notify(self, event: str, item: QueueItem) -> None:
        listeners: List[QueueListener]
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(event, item)
            except Exception:
                continue


_queue_manager: Optional[QueueManager] = None


def get_queue_manager(force_refresh: bool = False) -> QueueManager:
    global _queue_manager
    if _queue_manager is None or force_refresh:
        _queue_manager = QueueManager()
    return _queue_manager
