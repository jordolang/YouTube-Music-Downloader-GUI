from __future__ import annotations

import time
from dataclasses import dataclass

import pytest

from gui_music_downloader.backend.config_manager import get_config
from gui_music_downloader.backend.music_services.models import (
    ResolutionCandidate,
    ResolvedTrack,
    StreamingTrack,
)
from gui_music_downloader.backend.queue_manager import QueueManager


@dataclass
class FakeProgress:
    percent: float
    status: str
    speed: float = 128_000

    def get_formatted_eta(self) -> str:
        return "1s"


class FakeEngine:
    def __init__(self, delay: float = 0.02, steps: int = 5):
        self.delay = delay
        self.steps = steps

    def download(self, url, output_path, quality, progress_callback, metadata):
        for index in range(self.steps):
            percent = (index / (self.steps - 1)) * 100 if self.steps > 1 else 100.0
            status = "processing" if percent >= 100.0 else "downloading"
            progress = FakeProgress(percent=percent, status=status)
            progress_callback(progress)
            time.sleep(self.delay)
        return True


def _make_resolved_track(name: str = "Test Track") -> ResolvedTrack:
    track = StreamingTrack(
        service="spotify",
        track_id="track-id",
        name=name,
        artists=["Artist"],
        album="Album",
    )
    candidate = ResolutionCandidate(
        youtube_id="yt123",
        url="https://youtu.be/yt123",
        title=name,
        channel="Channel",
        score=100.0,
    )
    return ResolvedTrack(track=track, candidate=candidate, confidence=100.0)


def _wait_for(condition, timeout: float = 1.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return False


def test_queue_pause_and_resume(tmp_path):
    config = get_config()
    config.set("general.save_location", str(tmp_path))

    engine = FakeEngine(delay=0.05)
    queue = QueueManager(engine=engine)

    try:
        resolved = _make_resolved_track()
        item = queue.enqueue(resolved)

        assert _wait_for(lambda: item.started_at is not None)
        assert queue.pause(item.id) is True
        assert item.paused is True
        assert item.status == "paused"

        assert queue.resume(item.id) is True

        queue.wait_for_all()
        assert item.status == "complete"
        assert item.percent == pytest.approx(100.0)
    finally:
        queue.shutdown()


def test_queue_cancel_during_download(tmp_path):
    config = get_config()
    config.set("general.save_location", str(tmp_path))

    engine = FakeEngine(delay=0.05)
    queue = QueueManager(engine=engine)

    try:
        item = queue.enqueue(_make_resolved_track("Cancel Track"))
        assert _wait_for(lambda: item.started_at is not None)

        assert queue.cancel(item.id) is True

        queue.wait_for_all()
        assert item.status == "cancelled"
    finally:
        queue.shutdown()


def test_queue_cancel_before_start(tmp_path):
    config = get_config()
    config.set("general.save_location", str(tmp_path))

    # Use longer delay to ensure we cancel before first progress callback runs.
    engine = FakeEngine(delay=0.1)
    queue = QueueManager(engine=engine)

    try:
        item = queue.enqueue(_make_resolved_track("Queued Track"))
        assert queue.cancel(item.id) is True

        queue.wait_for_all()
        assert item.status == "cancelled"
    finally:
        queue.shutdown()
