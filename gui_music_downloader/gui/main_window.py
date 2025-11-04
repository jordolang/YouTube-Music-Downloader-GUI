"""
Main Application Window
Complete GUI with search, results, and library sync/download management.
"""
import logging
import threading
from typing import Dict, List, Optional

import customtkinter as ctk

from ..backend.config_manager import get_config
from ..backend.library_manager import SyncProgress
from ..backend.music_services.models import ResolutionCandidate, ResolvedTrack, StreamingTrack
from ..backend.queue_manager import QueueItem, get_queue_manager
from ..backend.service_factory import get_library_manager
from ..backend.sync_orchestrator import SyncOrchestrator
from ..backend.youtube_search import SearchResult, get_searcher
from ..utils import constants, helpers
from .settings_dialog import SettingsDialog
from .playlist_tab import PlaylistTab

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.config = get_config()
        self.searcher = get_searcher()
        self.library_manager = get_library_manager()
        self.queue_manager = get_queue_manager()
        self.orchestrator = SyncOrchestrator(
            library_manager=self.library_manager,
            queue_manager=self.queue_manager,
        )

        # State
        self.search_results: List[SearchResult] = []
        self.selected_indices: List[int] = []
        self.queue_rows: Dict[str, Dict[str, object]] = {}
        self.available_services: List[str] = []

        # Tk variables
        self.service_var = ctk.StringVar(value="")
        self.auto_resolve_var = ctk.BooleanVar(value=True)

        # Setup window
        self.title(f"{constants.APP_NAME} v{constants.APP_VERSION}")
        self.geometry("1200x780")
        self._center_window()

        # Setup UI
        self._setup_ui()
        self._load_services()

        # Backend observers
        self.library_manager.subscribe(self._handle_sync_progress)
        self.queue_manager.subscribe(self._handle_queue_event)

        # Keyboard shortcuts
        self.bind("<Command-f>", lambda e: self.search_entry.focus())
        self.bind("<Command-,>", lambda e: self._open_settings())
        self.bind("<Command-q>", lambda e: self.quit())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        logger.info("Main window initialized")
    
    def _center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _setup_ui(self):
        """Setup user interface"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top bar (search)
        self._create_search_bar()

        # Main content tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.tabview.grid_rowconfigure(0, weight=1)
        self.tabview.grid_columnconfigure(0, weight=1)

        self.search_tab = self.tabview.add("Search")
        self.playlist_tab_frame = self.tabview.add("Playlist")
        self.sync_tab = self.tabview.add("Library Sync")

        self._create_results_area(self.search_tab)
        self._create_playlist_tab()
        self._create_sync_tab(self.sync_tab)

        # Status bar
        self._create_status_bar()
    
    def _create_search_bar(self):
        """Create search bar with entry and quality selector"""
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            search_frame,
            text="🎵 YouTube Music Downloader",
            font=("SF Pro Display", 24, "bold")
        )
        title.grid(row=0, column=0, columnspan=4, pady=(0, 15))
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search for a song (e.g., 'The Beatles Hey Jude')...",
            height=40,
            font=("SF Pro Display", 14)
        )
        self.search_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda e: self._on_search())
        
        # Quality selector
        quality_label = ctk.CTkLabel(search_frame, text="Quality:", font=("SF Pro Display", 12))
        quality_label.grid(row=1, column=2, padx=(0, 5))
        
        self.quality_var = ctk.StringVar(value="Best")
        quality_menu = ctk.CTkOptionMenu(
            search_frame,
            values=list(constants.QUALITY_OPTIONS.keys()),
            variable=self.quality_var,
            width=140,
            height=40
        )
        quality_menu.grid(row=1, column=3, padx=(0, 10))
        
        # Search button
        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍 Search",
            command=self._on_search,
            height=40,
            width=100,
            font=("SF Pro Display", 14, "bold")
        )
        search_btn.grid(row=1, column=4)
    
    def _create_results_area(self, parent: ctk.CTkFrame):
        """Create scrollable results area"""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        self.results_frame = ctk.CTkScrollableFrame(
            parent,
            label_text="Search Results",
            label_font=("SF Pro Display", 16, "bold")
        )
        self.results_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        # Welcome message
        self.welcome_label = ctk.CTkLabel(
            self.results_frame,
            text="👆 Search for a song to get started\n\nThe app will find official versions and avoid live performances!",
            font=("SF Pro Display", 14),
            text_color="gray"
        )
        self.welcome_label.grid(row=0, column=0, pady=50)
    
    def _create_playlist_tab(self):
        """Create playlist tab using PlaylistTab component."""
        self.playlist_tab = PlaylistTab(
            parent=self.playlist_tab_frame,
            quality_var=self.quality_var,
            status_callback=self._update_status
        )
        self.playlist_tab.pack(fill="both", expand=True)

    def _create_sync_tab(self, parent: ctk.CTkFrame):
        """Create library sync controls and queue view."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(3, weight=1)

        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        controls.grid_columnconfigure(1, weight=1)

        service_label = ctk.CTkLabel(
            controls,
            text="Service:",
            font=("SF Pro Display", 13, "bold"),
        )
        service_label.grid(row=0, column=0, sticky="w")

        self.sync_service_menu = ctk.CTkOptionMenu(
            controls,
            variable=self.service_var,
            values=["Loading..."],
            width=220,
        )
        self.sync_service_menu.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.auto_resolve_switch = ctk.CTkCheckBox(
            controls,
            text="Automatic YouTube matching",
            variable=self.auto_resolve_var,
        )
        self.auto_resolve_switch.grid(row=0, column=2, padx=(20, 0))

        self.sync_button = ctk.CTkButton(
            controls,
            text="Sync & Download",
            command=self._start_sync,
            width=160,
        )
        self.sync_button.grid(row=0, column=3, padx=(20, 0))

        progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
        progress_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        progress_frame.grid_columnconfigure(1, weight=1)

        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Progress:",
            font=("SF Pro Display", 12),
        )
        progress_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.sync_progress_bar = ctk.CTkProgressBar(progress_frame, height=10)
        self.sync_progress_bar.grid(row=0, column=1, sticky="ew")
        self.sync_progress_bar.set(0)

        self.sync_progress_detail = ctk.CTkLabel(
            progress_frame,
            text="Idle",
            font=("SF Pro Display", 11),
            text_color="gray",
        )
        self.sync_progress_detail.grid(row=1, column=1, sticky="w", pady=(6, 0))

        queue_label = ctk.CTkLabel(
            parent,
            text="Download Queue",
            font=("SF Pro Display", 15, "bold"),
        )
        queue_label.grid(row=2, column=0, sticky="w", padx=10, pady=(15, 0))

        self.queue_list_frame = ctk.CTkScrollableFrame(parent)
        self.queue_list_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(8, 10))
        self.queue_list_frame.grid_columnconfigure(0, weight=1)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_frame = ctk.CTkFrame(self, height=40)
        self.status_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=("SF Pro Display", 11)
        )
        self.status_label.pack(side="left", padx=10)
        
        # Settings button
        settings_btn = ctk.CTkButton(
            self.status_frame,
            text="⚙️ Settings",
            command=self._open_settings,
            width=100,
            height=28
        )
        settings_btn.pack(side="right", padx=10)

    def _load_services(self):
        """Populate streaming service selector based on configured services."""
        services = self.library_manager.list_services()
        self.available_services = services

        if services:
            self.sync_service_menu.configure(values=services, state="normal")
            if self.service_var.get() not in services:
                self.service_var.set(services[0])
            self.sync_button.configure(state="normal")
        else:
            placeholder = ["No services configured"]
            self.sync_service_menu.configure(values=placeholder, state="disabled")
            self.service_var.set(placeholder[0])
            self.sync_button.configure(state="disabled")

    def _on_search(self):
        """Handle search button click"""
        query = self.search_entry.get().strip()
        if not query:
            self._update_status("⚠️ Please enter a search query")
            return
        
        self._update_status(f"🔍 Searching for '{query}'...")
        self.search_entry.configure(state="disabled")
        
        # Run search in background thread
        thread = threading.Thread(target=self._search_thread, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _search_thread(self, query: str):
        """Search in background thread"""
        try:
            results = self.searcher.search_videos(query, limit=10)
            
            # Update UI in main thread
            self.after(0, self._display_results, results)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.after(0, self._update_status, f"❌ Search failed: {e}")
        finally:
            self.after(0, lambda: self.search_entry.configure(state="normal"))
    
    def _display_results(self, results: List[SearchResult]):
        """Display search results"""
        self.search_results = results
        self.selected_indices = []
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        if not results:
            self._update_status("❌ No results found")
            no_results = ctk.CTkLabel(
                self.results_frame,
                text="No results found. Try a different search query.",
                font=("SF Pro Display", 14),
                text_color="gray"
            )
            no_results.grid(row=0, column=0, pady=50)
            return
        
        self._update_status(f"✅ Found {len(results)} results")
        
        # Display each result
        for i, result in enumerate(results):
            self._create_result_card(i, result)
        
        # Download button
        download_all_btn = ctk.CTkButton(
            self.results_frame,
            text="⬇️ Download Selected",
            command=self._download_selected,
            height=45,
            font=("SF Pro Display", 15, "bold"),
            fg_color="#1DB954",
            hover_color="#1ed760"
        )
        download_all_btn.grid(row=len(results) + 1, column=0, pady=20, sticky="ew")
    
    def _create_result_card(self, index: int, result: SearchResult):
        """Create a result card"""
        card = ctk.CTkFrame(self.results_frame)
        card.grid(row=index, column=0, pady=8, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        
        # Checkbox
        var = ctk.BooleanVar(value=True)
        checkbox = ctk.CTkCheckBox(
            card,
            text="",
            variable=var,
            command=lambda: self._toggle_selection(index, var.get()),
            width=30
        )
        checkbox.grid(row=0, column=0, rowspan=2, padx=(10, 5), pady=10)
        
        # Initialize as selected
        self.selected_indices.append(index)
        
        # Title
        title_text = result.title
        if len(title_text) > 70:
            title_text = title_text[:70] + "..."
        
        title = ctk.CTkLabel(
            card,
            text=title_text,
            font=("SF Pro Display", 13, "bold"),
            anchor="w"
        )
        title.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 2))
        
        # Info line
        quality_kbps = constants.QUALITY_OPTIONS[self.quality_var.get()]
        size_est = result.get_formatted_size(quality_kbps)
        
        info_text = f"👤 {result.channel}  |  ⏱ {result.get_formatted_duration()}  |  💾 ~{size_est}  |  👁 {result.view_count:,} views"
        if result.ranking_score > 0:
            info_text += f"  |  🏆 Score: {result.ranking_score:.0f}"
        
        info = ctk.CTkLabel(
            card,
            text=info_text,
            font=("SF Pro Display", 11),
            text_color="gray",
            anchor="w"
        )
        info.grid(row=1, column=1, sticky="w", padx=10, pady=(2, 10))
        
        # Download button
        download_btn = ctk.CTkButton(
            card,
            text="⬇️",
            command=lambda: self._download_single(index),
            width=40,
            height=40
        )
        download_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=5)

    def _start_sync(self):
        """Kick off library synchronization and queue population."""
        if not self.available_services or self.service_var.get() not in self.available_services:
            self._update_status("⚠️ Configure Spotify or Apple Music in Settings before syncing")
            return

        service = self.service_var.get()
        auto_resolve = bool(self.auto_resolve_var.get())

        self.sync_button.configure(state="disabled")
        self.sync_service_menu.configure(state="disabled")
        self.sync_progress_bar.set(0)
        self.sync_progress_detail.configure(text=f"Syncing {service}…")
        self._update_status(f"🔄 Syncing {service} library…")

        thread = threading.Thread(
            target=self._run_sync,
            args=(service, auto_resolve),
            daemon=True,
        )
        thread.start()

    def _run_sync(self, service: str, auto_resolve: bool):
        """Background worker that runs the orchestrator."""
        try:
            self.orchestrator.sync_and_enqueue(service, auto_resolve=auto_resolve)
            message = f"✅ {service.title()} sync queued downloads"
        except Exception as exc:
            logger.exception("Library sync failed for %s", service)
            message = f"❌ Sync failed: {exc}"
        finally:
            self.after(0, self._on_sync_complete, message)

    def _on_sync_complete(self, message: str):
        """Restore controls after sync completes."""
        if self.available_services:
            self.sync_button.configure(state="normal")
            self.sync_service_menu.configure(state="normal")
        self._update_status(message)

    def _handle_sync_progress(self, event: str, progress: SyncProgress) -> None:
        """Receive progress callbacks from the library manager."""
        self.after(0, self._update_sync_ui, event, progress)

    def _update_sync_ui(self, event: str, progress: SyncProgress) -> None:
        """Update sync progress widgets on the main thread."""
        total = max(progress.total, 0)
        completed = min(progress.current, total) if total else 0

        if total:
            percent = max(0.0, min(completed / total, 1.0))
        else:
            percent = 0.0

        if event == "completed":
            percent = 1.0
        elif event == "error":
            percent = 0.0

        self.sync_progress_bar.set(percent)

        detail_parts = [progress.state.title()]
        if total:
            detail_parts.append(f"{completed}/{total}")
        if progress.detail:
            detail_parts.append(progress.detail)
        detail_text = " · ".join(detail_parts)
        self.sync_progress_detail.configure(text=detail_text)

        if event == "error":
            self._update_status(f"❌ Sync error: {progress.detail}")

    def _handle_queue_event(self, event: str, item: QueueItem) -> None:
        """Receive queue updates for download activity."""
        self.after(0, self._update_queue_ui, event, item)

    def _update_queue_ui(self, event: str, item: QueueItem) -> None:
        """Render queue progress in the UI."""
        widgets = self._ensure_queue_row(item)

        status_text = self._format_queue_status(item)
        widgets["status"].configure(text=status_text)

        progress_value = max(0.0, min(item.percent / 100.0, 1.0))
        widgets["progress"].set(progress_value)

        widgets["eta"].configure(text=self._format_queue_eta(item))

        if event in {"completed", "error"}:
            widgets["progress"].set(1.0 if event == "completed" else progress_value)

        if event == "error":
            self._update_status(f"❌ Download failed: {item.error or item.track.name}")
        elif event == "completed":
            self._update_status(f"✅ Download complete: {item.track.name}")
            self._show_success_notification(str(item.output_path))
        elif event == "queued":
            self._update_status(f"🗂️ Queued: {item.track.name}")
        elif event == "started":
            self._update_status(f"⬇️ Downloading: {item.track.name}")

    def _ensure_queue_row(self, item: QueueItem) -> Dict[str, object]:
        """Create queue row widgets if needed."""
        if item.id in self.queue_rows:
            return self.queue_rows[item.id]

        row_index = len(self.queue_rows)
        frame = ctk.CTkFrame(self.queue_list_frame)
        frame.grid(row=row_index, column=0, sticky="ew", padx=10, pady=6)
        frame.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(
            frame,
            text=f"{item.track.display_artist()} — {item.track.name}",
            font=("SF Pro Display", 13, "bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w")

        status = ctk.CTkLabel(
            frame,
            text="Queued",
            font=("SF Pro Display", 12),
        )
        status.grid(row=1, column=0, sticky="w")

        progress_bar = ctk.CTkProgressBar(frame, height=10)
        progress_bar.grid(row=1, column=1, sticky="ew", padx=(12, 0))
        progress_bar.set(max(0.0, min(item.percent / 100.0, 1.0)))

        eta = ctk.CTkLabel(
            frame,
            text=self._format_queue_eta(item),
            font=("SF Pro Display", 11),
            text_color="gray",
        )
        eta.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        widgets = {"frame": frame, "title": title, "status": status, "progress": progress_bar, "eta": eta}
        self.queue_rows[item.id] = widgets
        return widgets

    def _format_queue_status(self, item: QueueItem) -> str:
        """Build a friendly status string for a queue item."""
        if item.error:
            return f"Error · {item.error}"
        if item.status == "downloading":
            return f"Downloading · {item.percent:.0f}%"
        if item.status == "processing":
            return "Processing"
        if item.status == "complete":
            return "Completed"
        return item.status.capitalize()

    def _format_queue_eta(self, item: QueueItem) -> str:
        """Format ETA and speed details."""
        if item.status == "downloading":
            parts = []
            if item.speed:
                parts.append(helpers.format_speed(int(item.speed)))
            if item.eta:
                parts.append(f"ETA {item.eta}")
            return " · ".join(parts) if parts else "Downloading…"
        if item.status == "processing":
            return "Processing…"
        if item.status == "complete":
            return "Saved to library"
        if item.error:
            return item.error
        return ""

    
    def _toggle_selection(self, index: int, selected: bool):
        """Toggle result selection"""
        if selected and index not in self.selected_indices:
            self.selected_indices.append(index)
        elif not selected and index in self.selected_indices:
            self.selected_indices.remove(index)
    
    def _download_selected(self):
        """Download all selected results via the shared queue."""
        if not self.selected_indices:
            self._update_status("⚠️ No results selected")
            return

        for index in list(self.selected_indices):
            self._download_single(index)

    def _download_single(self, index: int):
        """Queue a single search result for download."""
        if index < 0 or index >= len(self.search_results):
            return

        result = self.search_results[index]
        self._enqueue_search_result(result)

    def _enqueue_search_result(self, result: SearchResult) -> None:
        """Convert a search result into a queue job."""
        artist, title = helpers.parse_artist_title(result.title)
        artist = artist or result.channel or "Unknown Artist"
        title = title or result.title

        # Persist chosen quality so queue uses the same bitrate.
        selected_quality = self.quality_var.get()
        if selected_quality != self.config.get("general.default_quality"):
            self.config.set("general.default_quality", selected_quality)

        track = StreamingTrack(
            service="manual",
            track_id=result.video_id or result.url,
            name=helpers.clean_metadata_text(title),
            artists=[helpers.clean_metadata_text(artist)],
            album="",
            album_artist=helpers.clean_metadata_text(artist),
            duration_ms=(result.duration_sec * 1000) if result.duration_sec else None,
            artwork_url=result.thumbnail_url,
            explicit=None,
            metadata={
                "channel": result.channel,
                "manual_source": True,
                "original_title": result.title,
            },
        )

        candidate = ResolutionCandidate(
            youtube_id=result.video_id,
            url=result.url,
            title=result.title,
            channel=result.channel,
            score=result.ranking_score or 100.0,
            duration_sec=result.duration_sec,
            view_count=result.view_count,
            reason="Manual search selection",
        )

        resolved = ResolvedTrack(
            track=track,
            candidate=candidate,
            confidence=candidate.score or 1.0,
        )

        self.queue_manager.enqueue(resolved)
        self._update_status(f"🗂️ Queued: {track.name}")
    
    def _show_success_notification(self, file_path: str):
        """Show success notification"""
        try:
            import pync
            pync.notify(
                f"Downloaded to: {file_path}",
                title="Download Complete",
                sound="default"
            )
        except:
            pass  # Notifications are optional
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.status_label.configure(text=message)
        logger.info(f"Status: {message}")

    def _open_settings(self):
        """Open settings dialog."""
        dialog = SettingsDialog(self)
        dialog.wait_window()
        
        # Reload config after dialog closes
        if hasattr(dialog, 'changes_made') and dialog.changes_made:
            self._update_status("✅ Settings saved")
    
    def _on_close(self):
        """Clean up subscriptions before closing the window."""
        try:
            self.library_manager.unsubscribe(self._handle_sync_progress)
        except Exception:
            pass
        try:
            self.queue_manager.unsubscribe(self._handle_queue_event)
        except Exception:
            pass
        self.destroy()
