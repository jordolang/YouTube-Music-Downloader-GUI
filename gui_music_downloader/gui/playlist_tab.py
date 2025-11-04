"""
Playlist Tab
UI for entering YouTube playlist URLs and batch downloading tracks.
"""
from __future__ import annotations

import threading
from typing import List, Optional

import customtkinter as ctk

from ..backend.music_services.models import ResolutionCandidate, ResolvedTrack, StreamingTrack
from ..backend.queue_manager import get_queue_manager
from ..backend.youtube_search import PlaylistInfo, get_searcher
from ..utils import constants, helpers


class PlaylistTab(ctk.CTkFrame):
    """Tab for YouTube playlist downloads."""
    
    def __init__(self, parent, quality_var: ctk.StringVar, status_callback):
        super().__init__(parent, fg_color="transparent")
        
        self.quality_var = quality_var
        self.status_callback = status_callback
        self.searcher = get_searcher()
        self.queue_manager = get_queue_manager()
        
        self.playlist_info: Optional[PlaylistInfo] = None
        self.selected_indices: List[int] = []
        self.track_checkboxes: List[tuple] = []  # (checkbox_var, track_index)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create playlist tab UI."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # URL input section
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        url_frame.grid_columnconfigure(1, weight=1)
        
        url_label = ctk.CTkLabel(
            url_frame,
            text="Playlist URL:",
            font=("SF Pro Display", 13, "bold")
        )
        url_label.grid(row=0, column=0, sticky="w")
        
        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="Paste YouTube playlist URL (e.g., https://youtube.com/playlist?list=...)",
            height=40,
            font=("SF Pro Display", 13)
        )
        self.url_entry.grid(row=0, column=1, padx=(10, 10), sticky="ew")
        self.url_entry.bind("<Return>", lambda e: self._fetch_playlist())
        
        fetch_btn = ctk.CTkButton(
            url_frame,
            text="Fetch Playlist",
            command=self._fetch_playlist,
            height=40,
            width=120,
            font=("SF Pro Display", 13, "bold")
        )
        fetch_btn.grid(row=0, column=2)
        
        # Playlist info section
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text="Enter a YouTube playlist URL above",
            font=("SF Pro Display", 12),
            text_color="gray"
        )
        self.info_label.pack(pady=10)
        
        # Tracks list
        self.tracks_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Playlist Tracks",
            label_font=("SF Pro Display", 15, "bold")
        )
        self.tracks_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.tracks_frame.grid_columnconfigure(0, weight=1)
        
        # Welcome message
        self.welcome_label = ctk.CTkLabel(
            self.tracks_frame,
            text="👆 Fetch a playlist to see tracks here",
            font=("SF Pro Display", 13),
            text_color="gray"
        )
        self.welcome_label.grid(row=0, column=0, pady=50)
        
        # Action buttons
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.action_frame.grid_columnconfigure(1, weight=1)
        
        self.select_all_btn = ctk.CTkButton(
            self.action_frame,
            text="Select All",
            command=self._select_all,
            width=120,
            state="disabled"
        )
        self.select_all_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.select_none_btn = ctk.CTkButton(
            self.action_frame,
            text="Select None",
            command=self._select_none,
            width=120,
            state="disabled"
        )
        self.select_none_btn.grid(row=0, column=1, padx=(0, 10), sticky="w")
        
        self.download_btn = ctk.CTkButton(
            self.action_frame,
            text="⬇️ Download Selected",
            command=self._download_selected,
            height=45,
            width=200,
            font=("SF Pro Display", 14, "bold"),
            fg_color="#1DB954",
            hover_color="#1ed760",
            state="disabled"
        )
        self.download_btn.grid(row=0, column=2, sticky="e")
    
    def _fetch_playlist(self):
        """Fetch playlist info from URL."""
        url = self.url_entry.get().strip()
        
        if not url:
            self.status_callback("⚠️ Please enter a playlist URL")
            return
        
        if not self.searcher.is_playlist_url(url):
            self.status_callback("⚠️ Invalid playlist URL")
            return
        
        # Disable UI during fetch
        self.url_entry.configure(state="disabled")
        self.status_callback("🔍 Fetching playlist...")
        
        # Run in background thread
        thread = threading.Thread(target=self._fetch_thread, args=(url,))
        thread.daemon = True
        thread.start()
    
    def _fetch_thread(self, url: str):
        """Background thread to fetch playlist."""
        try:
            playlist_info = self.searcher.get_playlist_info(url)
            
            if not playlist_info or not playlist_info.tracks:
                self.after(0, self._on_fetch_error, "No tracks found in playlist")
                return
            
            # Update UI in main thread
            self.after(0, self._display_playlist, playlist_info)
            
        except Exception as e:
            self.after(0, self._on_fetch_error, str(e))
    
    def _on_fetch_error(self, error: str):
        """Handle fetch error."""
        self.status_callback(f"❌ Fetch failed: {error}")
        self.url_entry.configure(state="normal")
    
    def _display_playlist(self, playlist_info: PlaylistInfo):
        """Display fetched playlist."""
        self.playlist_info = playlist_info
        self.selected_indices = []
        self.track_checkboxes = []
        
        # Update info section
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        title_label = ctk.CTkLabel(
            self.info_frame,
            text=f"📋 {playlist_info.name}",
            font=("SF Pro Display", 14, "bold")
        )
        title_label.pack(pady=(10, 5))
        
        quality_kbps = constants.QUALITY_OPTIONS[self.quality_var.get()]
        total_size = sum(track.get_estimated_size(quality_kbps) for track in playlist_info.tracks)
        total_size_str = helpers.format_bytes(total_size)
        
        info_text = f"👤 {playlist_info.author}  |  🎵 {len(playlist_info.tracks)} tracks  |  💾 ~{total_size_str} total"
        info_label = ctk.CTkLabel(
            self.info_frame,
            text=info_text,
            font=("SF Pro Display", 12),
            text_color="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # Clear tracks list
        for widget in self.tracks_frame.winfo_children():
            widget.destroy()
        
        # Display tracks
        for i, track in enumerate(playlist_info.tracks):
            self._create_track_card(i, track, quality_kbps)
        
        # Enable action buttons
        self.select_all_btn.configure(state="normal")
        self.select_none_btn.configure(state="normal")
        self.download_btn.configure(state="normal")
        
        # Re-enable URL entry
        self.url_entry.configure(state="normal")
        
        # Select all by default
        self._select_all()
        
        self.status_callback(f"✅ Loaded playlist with {len(playlist_info.tracks)} tracks")
    
    def _create_track_card(self, index: int, track, quality_kbps: int):
        """Create a track card."""
        card = ctk.CTkFrame(self.tracks_frame)
        card.grid(row=index, column=0, pady=6, sticky="ew")
        card.grid_columnconfigure(1, weight=1)
        
        # Checkbox
        var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(
            card,
            text="",
            variable=var,
            command=lambda: self._toggle_selection(index, var.get()),
            width=30
        )
        checkbox.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=10)
        
        self.track_checkboxes.append((var, index))
        
        # Track number and title
        title_text = f"{index + 1}. {track.title}"
        if len(title_text) > 80:
            title_text = title_text[:80] + "..."
        
        title = ctk.CTkLabel(
            card,
            text=title_text,
            font=("SF Pro Display", 12, "bold"),
            anchor="w"
        )
        title.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 2))
        
        # Info line
        size_est = track.get_formatted_size(quality_kbps)
        duration_str = track.get_formatted_duration()
        
        info_text = f"👤 {track.channel}  |  ⏱ {duration_str}  |  💾 ~{size_est}"
        if track.view_count:
            info_text += f"  |  👁 {track.view_count:,} views"
        
        info = ctk.CTkLabel(
            card,
            text=info_text,
            font=("SF Pro Display", 10),
            text_color="gray",
            anchor="w"
        )
        info.grid(row=1, column=1, sticky="w", padx=10, pady=(2, 10))
    
    def _toggle_selection(self, index: int, selected: bool):
        """Toggle track selection."""
        if selected and index not in self.selected_indices:
            self.selected_indices.append(index)
        elif not selected and index in self.selected_indices:
            self.selected_indices.remove(index)
        
        # Update button text
        count = len(self.selected_indices)
        if count > 0:
            self.download_btn.configure(text=f"⬇️ Download {count} Selected")
        else:
            self.download_btn.configure(text="⬇️ Download Selected")
    
    def _select_all(self):
        """Select all tracks."""
        if not self.playlist_info:
            return
        
        self.selected_indices = list(range(len(self.playlist_info.tracks)))
        
        for var, _ in self.track_checkboxes:
            var.set(True)
        
        self.download_btn.configure(text=f"⬇️ Download All ({len(self.selected_indices)})")
    
    def _select_none(self):
        """Deselect all tracks."""
        self.selected_indices = []
        
        for var, _ in self.track_checkboxes:
            var.set(False)
        
        self.download_btn.configure(text="⬇️ Download Selected")
    
    def _download_selected(self):
        """Download selected tracks."""
        if not self.playlist_info or not self.selected_indices:
            self.status_callback("⚠️ No tracks selected")
            return
        
        count = len(self.selected_indices)
        self.status_callback(f"🗂️ Queuing {count} tracks...")
        
        # Queue selected tracks
        for index in self.selected_indices:
            track = self.playlist_info.tracks[index]
            self._enqueue_track(track)
        
        self.status_callback(f"✅ Queued {count} tracks for download")
    
    def _enqueue_track(self, track):
        """Enqueue a single track."""
        # Parse artist and title
        artist, title = helpers.parse_artist_title(track.title)
        artist = artist or track.channel or "Unknown Artist"
        title = title or track.title
        
        # Create streaming track model
        streaming_track = StreamingTrack(
            service="playlist",
            track_id=track.video_id or track.url,
            name=helpers.clean_metadata_text(title),
            artists=[helpers.clean_metadata_text(artist)],
            album=self.playlist_info.name if self.playlist_info else "",
            album_artist=helpers.clean_metadata_text(artist),
            duration_ms=(track.duration_sec * 1000) if track.duration_sec else None,
            artwork_url=track.thumbnail_url,
            explicit=None,
            metadata={
                "channel": track.channel,
                "playlist_source": True,
                "playlist_name": self.playlist_info.name if self.playlist_info else "",
                "original_title": track.title,
            },
        )
        
        # Create resolution candidate
        candidate = ResolutionCandidate(
            youtube_id=track.video_id,
            url=track.url,
            title=track.title,
            channel=track.channel,
            score=track.ranking_score or 100.0,
            duration_sec=track.duration_sec,
            view_count=track.view_count,
            reason="Playlist track",
        )
        
        # Create resolved track
        resolved = ResolvedTrack(
            track=streaming_track,
            candidate=candidate,
            confidence=candidate.score or 1.0,
        )
        
        # Enqueue
        self.queue_manager.enqueue(resolved)
