"""
Temporary CLI helpers for exercising backend integrations.
"""
from __future__ import annotations

import argparse
import logging
from typing import List

from .library_manager import SyncProgress
from .queue_manager import QueueItem, get_queue_manager
from .service_factory import get_library_manager
from .sync_orchestrator import SyncOrchestrator

logger = logging.getLogger(__name__)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Music service sync utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Sync a configured music service")
    sync_parser.add_argument("service", help="Service name (e.g., spotify, apple_music)")
    sync_parser.add_argument(
        "--no-resolve",
        action="store_true",
        help="Skip automatic YouTube resolution",
    )
    sync_parser.add_argument(
        "--queue",
        action="store_true",
        help="Enqueue resolved tracks for download",
    )
    sync_parser.add_argument(
        "--watch",
        action="store_true",
        help="Follow download queue progress until completion (implies --queue)",
    )

    args = parser.parse_args(argv)

    if args.command == "sync":
        queue_flag = args.queue or args.watch
        return _run_sync(
            args.service,
            auto_resolve=not args.no_resolve,
            enqueue=queue_flag,
            watch=args.watch,
        )

    parser.print_help()
    return 1


def _run_sync(service: str, auto_resolve: bool, enqueue: bool, watch: bool) -> int:
    queue_manager = get_queue_manager()
    library_manager = get_library_manager()
    orchestrator = SyncOrchestrator(
        library_manager=library_manager,
        queue_manager=queue_manager,
    )

    if not library_manager.get_service(service):
        logger.error("Service '%s' is not registered. Check configuration.", service)
        return 1

    def listener(event: str, progress: SyncProgress) -> None:
        detail = progress.detail or ""
        msg = f"[{event.upper():8}] {progress.state:12} {progress.current}/{progress.total} {detail}"
        print(msg)

    library_manager.subscribe(listener)
    resolved = []
    queue_items = []
    try:
        if enqueue:
            queue_items = orchestrator.sync_and_enqueue(service, auto_resolve=auto_resolve)
        else:
            resolved = orchestrator.sync(service, auto_resolve=auto_resolve)
            queue_items = []
    finally:
        library_manager.unsubscribe(listener)

    if not enqueue:
        print(f"Resolved {len(resolved)} tracks")
        return 0

    print(f"Enqueued {len(queue_items)} tracks for download")

    if watch:
        def queue_listener(event: str, item: QueueItem) -> None:
            detail = f"{item.track.display_artist()} - {item.track.name}"
            print(f"[QUEUE {event.upper():7}] {item.status:12} {item.percent:5.1f}% {detail}")

        queue_manager.subscribe(queue_listener)
        try:
            queue_manager.wait_for_all()
        finally:
            queue_manager.unsubscribe(queue_listener)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
