"""
Main Application Window
Complete GUI with search, results, and download functionality
"""
import customtkinter as ctk
from pathlib import Path
import threading
import logging
from typing import List, Optional

from ..backend.youtube_search import get_searcher, SearchResult
from ..backend.downloader import get_engine, DownloadProgress
from ..backend.config_manager import get_config
from ..utils import constants, helpers

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.searcher = get_searcher()
        self.engine = get_engine()
        
        # State
        self.search_results: List[SearchResult] = []
        self.selected_indices: List[int] = []
        
        # Setup window
        self.title(f"{constants.APP_NAME} v{constants.APP_VERSION}")
        self.geometry("1100x750")
        self._center_window()
        
        # Setup UI
        self._setup_ui()
        
        # Keyboard shortcuts
        self.bind("<Command-f>", lambda e: self.search_entry.focus())
        self.bind("<Command-q>", lambda e: self.quit())
        
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
        
        # Results area
        self._create_results_area()
        
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
    
    def _create_results_area(self):
        """Create scrollable results area"""
        self.results_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Search Results",
            label_font=("SF Pro Display", 16, "bold")
        )
        self.results_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        
        # Welcome message
        self.welcome_label = ctk.CTkLabel(
            self.results_frame,
            text="👆 Search for a song to get started\n\nThe app will find official versions and avoid live performances!",
            font=("SF Pro Display", 14),
            text_color="gray"
        )
        self.welcome_label.grid(row=0, column=0, pady=50)
    
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
    
    def _toggle_selection(self, index: int, selected: bool):
        """Toggle result selection"""
        if selected and index not in self.selected_indices:
            self.selected_indices.append(index)
        elif not selected and index in self.selected_indices:
            self.selected_indices.remove(index)
    
    def _download_selected(self):
        """Download all selected results"""
        if not self.selected_indices:
            self._update_status("⚠️ No results selected")
            return
        
        # Download each selected result
        for index in self.selected_indices:
            if 0 <= index < len(self.search_results):
                self._download_single(index)
    
    def _download_single(self, index: int):
        """Download a single result"""
        if index >= len(self.search_results):
            return
        
        result = self.search_results[index]
        
        # Get quality
        quality_kbps = constants.QUALITY_OPTIONS[self.quality_var.get()]
        
        # Determine output path
        save_location = Path(self.config.get('general.save_location', constants.DEFAULT_MUSIC_DIR))
        
        # Parse artist and title for folder organization
        artist, title = helpers.parse_artist_title(result.title)
        if not artist:
            artist = result.channel
        
        # Sanitize names
        artist_safe = helpers.sanitize_filename(artist)
        title_safe = helpers.sanitize_filename(title or result.title)
        
        # Create output path: ~/Music/Artist/Title.mp3
        output_dir = save_location / artist_safe
        output_path = output_dir / f"{title_safe}.mp3"
        
        # Check for duplicates
        output_path = helpers.resolve_duplicate_path(
            output_path,
            self.config.get('general.duplicate_handling', 'rename')
        )
        
        self._update_status(f"⬇️ Downloading: {result.title[:50]}...")
        
        # Download in background thread
        thread = threading.Thread(
            target=self._download_thread,
            args=(result, output_path, quality_kbps, artist, title)
        )
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, result: SearchResult, output_path: Path, quality: int, artist: str, title: str):
        """Download in background thread"""
        try:
            def progress_cb(progress: DownloadProgress):
                if progress.status == 'downloading':
                    msg = f"⬇️ {result.title[:40]}... {progress.percent:.0f}% ({progress.get_formatted_speed()})"
                    self.after(0, self._update_status, msg)
                elif progress.status == 'processing':
                    self.after(0, self._update_status, f"⚙️ Converting {result.title[:40]}...")
                elif progress.status == 'complete':
                    self.after(0, self._update_status, f"✅ Downloaded: {result.title[:50]}")
                    self.after(0, self._show_success_notification, str(output_path))
            
            # Prepare metadata
            metadata = {
                'artist': artist,
                'title': title,
            }
            
            # Download
            success = self.engine.download(
                url=result.url,
                output_path=output_path,
                quality=quality,
                progress_callback=progress_cb,
                metadata=metadata
            )
            
            if success:
                logger.info(f"Download complete: {output_path}")
            else:
                self.after(0, self._update_status, f"❌ Download failed: {result.title[:50]}")
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            self.after(0, self._update_status, f"❌ Error: {e}")
    
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
