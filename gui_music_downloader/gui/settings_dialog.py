"""
Settings Dialog
Tabbed dialog for configuring application settings with import/export support.
"""
from __future__ import annotations

import json
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from ..backend.config_manager import get_config
from ..utils import constants


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog with tabbed interface."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.config = get_config()
        self.changes_made = False
        
        # Window setup
        self.title("Settings")
        self.geometry("700x600")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        self._center_on_parent(parent)
        
        # Build UI
        self._create_ui()
        
        # Load current settings
        self._load_settings()
    
    def _center_on_parent(self, parent):
        """Center dialog on parent window."""
        self.update_idletasks()
        
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def _create_ui(self):
        """Create the settings UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Create tabs
        self.general_tab = self.tabview.add("General")
        self.metadata_tab = self.tabview.add("Metadata")
        self.advanced_tab = self.tabview.add("Advanced")
        self.about_tab = self.tabview.add("About")
        
        # Populate tabs
        self._create_general_tab()
        self._create_metadata_tab()
        self._create_advanced_tab()
        self._create_about_tab()
        
        # Bottom buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        import_btn = ctk.CTkButton(
            button_frame,
            text="Import Settings",
            command=self._import_settings,
            width=150
        )
        import_btn.grid(row=0, column=0, padx=5, sticky="w")
        
        export_btn = ctk.CTkButton(
            button_frame,
            text="Export Settings",
            command=self._export_settings,
            width=150
        )
        export_btn.grid(row=0, column=1, padx=5)
        
        button_group = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_group.grid(row=0, column=2, sticky="e")
        
        cancel_btn = ctk.CTkButton(
            button_group,
            text="Cancel",
            command=self._on_cancel,
            width=100,
            fg_color="gray40",
            hover_color="gray30"
        )
        cancel_btn.pack(side="left", padx=5)
        
        save_btn = ctk.CTkButton(
            button_group,
            text="Save",
            command=self._on_save,
            width=100,
            fg_color="#1DB954",
            hover_color="#1ed760"
        )
        save_btn.pack(side="left")
    
    def _create_general_tab(self):
        """Create General settings tab."""
        tab = self.general_tab
        tab.grid_columnconfigure(1, weight=1)
        
        # Quality
        quality_label = ctk.CTkLabel(
            tab,
            text="Default Quality:",
            font=("SF Pro Display", 13, "bold")
        )
        quality_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.quality_var = ctk.StringVar(value="Best")
        quality_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.quality_var,
            values=list(constants.QUALITY_OPTIONS.keys()),
            width=200
        )
        quality_menu.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        
        # Save Location
        save_label = ctk.CTkLabel(
            tab,
            text="Save Location:",
            font=("SF Pro Display", 13, "bold")
        )
        save_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        location_frame = ctk.CTkFrame(tab, fg_color="transparent")
        location_frame.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        location_frame.grid_columnconfigure(0, weight=1)
        
        self.save_location_var = ctk.StringVar()
        location_entry = ctk.CTkEntry(
            location_frame,
            textvariable=self.save_location_var,
            width=300
        )
        location_entry.grid(row=0, column=0, sticky="ew")
        
        browse_btn = ctk.CTkButton(
            location_frame,
            text="Browse...",
            command=self._browse_save_location,
            width=80
        )
        browse_btn.grid(row=0, column=1, padx=(5, 0))
        
        # Filename Pattern
        pattern_label = ctk.CTkLabel(
            tab,
            text="Filename Pattern:",
            font=("SF Pro Display", 13, "bold")
        )
        pattern_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.filename_pattern_var = ctk.StringVar()
        pattern_entry = ctk.CTkEntry(
            tab,
            textvariable=self.filename_pattern_var,
            width=300
        )
        pattern_entry.grid(row=2, column=1, padx=20, pady=5, sticky="w")
        
        pattern_help = ctk.CTkLabel(
            tab,
            text="Variables: {artist}, {title}, {album}, {year}",
            font=("SF Pro Display", 11),
            text_color="gray"
        )
        pattern_help.grid(row=3, column=1, padx=20, pady=(0, 5), sticky="w")
        
        # Duplicate Handling
        duplicate_label = ctk.CTkLabel(
            tab,
            text="Duplicate Files:",
            font=("SF Pro Display", 13, "bold")
        )
        duplicate_label.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        self.duplicate_var = ctk.StringVar(value="rename")
        duplicate_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.duplicate_var,
            values=["Skip", "Overwrite", "Rename"],
            width=200
        )
        duplicate_menu.grid(row=4, column=1, padx=20, pady=5, sticky="w")
        
        # Theme
        theme_label = ctk.CTkLabel(
            tab,
            text="Theme:",
            font=("SF Pro Display", 13, "bold")
        )
        theme_label.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        
        self.theme_var = ctk.StringVar(value="System")
        theme_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.theme_var,
            values=["System", "Dark", "Light"],
            width=200,
            command=self._on_theme_change
        )
        theme_menu.grid(row=5, column=1, padx=20, pady=5, sticky="w")
    
    def _create_metadata_tab(self):
        """Create Metadata settings tab."""
        tab = self.metadata_tab
        tab.grid_columnconfigure(1, weight=1)
        
        # Auto Metadata
        self.auto_metadata_var = ctk.BooleanVar(value=True)
        auto_check = ctk.CTkCheckBox(
            tab,
            text="Automatically enhance metadata",
            variable=self.auto_metadata_var,
            font=("SF Pro Display", 13, "bold")
        )
        auto_check.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Fetch Lyrics
        self.fetch_lyrics_var = ctk.BooleanVar(value=True)
        lyrics_check = ctk.CTkCheckBox(
            tab,
            text="Fetch and embed lyrics",
            variable=self.fetch_lyrics_var,
            font=("SF Pro Display", 13, "bold")
        )
        lyrics_check.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="w")
        
        # API Keys Section
        api_label = ctk.CTkLabel(
            tab,
            text="API Keys (Optional)",
            font=("SF Pro Display", 14, "bold")
        )
        api_label.grid(row=2, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")
        
        # Genius API
        genius_label = ctk.CTkLabel(tab, text="Genius API:", font=("SF Pro Display", 12))
        genius_label.grid(row=3, column=0, padx=20, pady=5, sticky="w")
        
        self.genius_api_var = ctk.StringVar()
        genius_entry = ctk.CTkEntry(
            tab,
            textvariable=self.genius_api_var,
            placeholder_text="Enter Genius API key for lyrics",
            width=350,
            show="•"
        )
        genius_entry.grid(row=3, column=1, padx=20, pady=5, sticky="w")
        
        # Last.fm API
        lastfm_label = ctk.CTkLabel(tab, text="Last.fm API:", font=("SF Pro Display", 12))
        lastfm_label.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        self.lastfm_api_var = ctk.StringVar()
        lastfm_entry = ctk.CTkEntry(
            tab,
            textvariable=self.lastfm_api_var,
            placeholder_text="Enter Last.fm API key for genres",
            width=350,
            show="•"
        )
        lastfm_entry.grid(row=4, column=1, padx=20, pady=5, sticky="w")
        
        # Discogs Token
        discogs_label = ctk.CTkLabel(tab, text="Discogs Token:", font=("SF Pro Display", 12))
        discogs_label.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        
        self.discogs_token_var = ctk.StringVar()
        discogs_entry = ctk.CTkEntry(
            tab,
            textvariable=self.discogs_token_var,
            placeholder_text="Enter Discogs token for releases",
            width=350,
            show="•"
        )
        discogs_entry.grid(row=5, column=1, padx=20, pady=5, sticky="w")
        
        # Help text
        help_text = ctk.CTkLabel(
            tab,
            text="API keys enhance metadata quality but are optional.\nSee documentation for signup instructions.",
            font=("SF Pro Display", 11),
            text_color="gray",
            justify="left"
        )
        help_text.grid(row=6, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="w")
    
    def _create_advanced_tab(self):
        """Create Advanced settings tab."""
        tab = self.advanced_tab
        tab.grid_columnconfigure(1, weight=1)
        
        # Concurrent Downloads
        concurrent_label = ctk.CTkLabel(
            tab,
            text="Concurrent Downloads:",
            font=("SF Pro Display", 13, "bold")
        )
        concurrent_label.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.concurrent_var = ctk.StringVar(value="3")
        concurrent_entry = ctk.CTkEntry(
            tab,
            textvariable=self.concurrent_var,
            width=100
        )
        concurrent_entry.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        
        concurrent_help = ctk.CTkLabel(
            tab,
            text="Number of simultaneous downloads (1-10)",
            font=("SF Pro Display", 11),
            text_color="gray"
        )
        concurrent_help.grid(row=1, column=1, padx=20, pady=(0, 5), sticky="w")
        
        # Retry Attempts
        retry_label = ctk.CTkLabel(
            tab,
            text="Retry Attempts:",
            font=("SF Pro Display", 13, "bold")
        )
        retry_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.retry_var = ctk.StringVar(value="3")
        retry_entry = ctk.CTkEntry(
            tab,
            textvariable=self.retry_var,
            width=100
        )
        retry_entry.grid(row=2, column=1, padx=20, pady=5, sticky="w")
        
        # Timeout
        timeout_label = ctk.CTkLabel(
            tab,
            text="Timeout (seconds):",
            font=("SF Pro Display", 13, "bold")
        )
        timeout_label.grid(row=3, column=0, padx=20, pady=5, sticky="w")
        
        self.timeout_var = ctk.StringVar(value="30")
        timeout_entry = ctk.CTkEntry(
            tab,
            textvariable=self.timeout_var,
            width=100
        )
        timeout_entry.grid(row=3, column=1, padx=20, pady=5, sticky="w")
        
        # Download Engine
        engine_label = ctk.CTkLabel(
            tab,
            text="Download Engine:",
            font=("SF Pro Display", 13, "bold")
        )
        engine_label.grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        self.engine_var = ctk.StringVar(value="ytdlp")
        engine_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.engine_var,
            values=["ytdlp", "instantmusic"],
            width=200
        )
        engine_menu.grid(row=4, column=1, padx=20, pady=5, sticky="w")
        
        # Logging Level
        logging_label = ctk.CTkLabel(
            tab,
            text="Logging Level:",
            font=("SF Pro Display", 13, "bold")
        )
        logging_label.grid(row=5, column=0, padx=20, pady=5, sticky="w")
        
        self.logging_var = ctk.StringVar(value="INFO")
        logging_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.logging_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            width=200
        )
        logging_menu.grid(row=5, column=1, padx=20, pady=5, sticky="w")
    
    def _create_about_tab(self):
        """Create About tab."""
        tab = self.about_tab
        tab.grid_columnconfigure(0, weight=1)
        
        # App icon/title
        title = ctk.CTkLabel(
            tab,
            text=f"🎵 {constants.APP_NAME}",
            font=("SF Pro Display", 24, "bold")
        )
        title.grid(row=0, column=0, pady=(40, 10))
        
        # Version
        version = ctk.CTkLabel(
            tab,
            text=f"Version {constants.APP_VERSION}",
            font=("SF Pro Display", 14),
            text_color="gray"
        )
        version.grid(row=1, column=0, pady=5)
        
        # Description
        description = ctk.CTkLabel(
            tab,
            text="A modern macOS GUI for downloading music from YouTube\nwith Spotify and Apple Music integration",
            font=("SF Pro Display", 12),
            text_color="gray",
            justify="center"
        )
        description.grid(row=2, column=0, pady=20)
        
        # Credits
        credits_frame = ctk.CTkFrame(tab)
        credits_frame.grid(row=3, column=0, padx=40, pady=20, sticky="ew")
        
        credits_title = ctk.CTkLabel(
            credits_frame,
            text="Credits",
            font=("SF Pro Display", 14, "bold")
        )
        credits_title.pack(pady=(10, 5))
        
        credits_text = ctk.CTkLabel(
            credits_frame,
            text=f"Created by {constants.APP_AUTHOR}\n\n"
                 "Built with:\n"
                 "• CustomTkinter for GUI\n"
                 "• yt-dlp for downloads\n"
                 "• FFmpeg for audio conversion\n"
                 "• Spotipy & Apple Music Kit",
            font=("SF Pro Display", 11),
            text_color="gray",
            justify="left"
        )
        credits_text.pack(pady=(0, 10))
        
        # Links
        links_frame = ctk.CTkFrame(tab, fg_color="transparent")
        links_frame.grid(row=4, column=0, pady=10)
        
        github_btn = ctk.CTkButton(
            links_frame,
            text="📖 Documentation",
            command=lambda: self._open_url("https://github.com/jordolang/YouTube-Music-Downloader-GUI"),
            width=150
        )
        github_btn.pack(side="left", padx=5)
        
        issues_btn = ctk.CTkButton(
            links_frame,
            text="🐛 Report Issue",
            command=lambda: self._open_url("https://github.com/jordolang/YouTube-Music-Downloader-GUI/issues"),
            width=150
        )
        issues_btn.pack(side="left", padx=5)
    
    def _browse_save_location(self):
        """Open folder picker for save location."""
        current = Path(self.save_location_var.get()).expanduser()
        
        folder = filedialog.askdirectory(
            title="Select Music Save Location",
            initialdir=str(current) if current.exists() else str(Path.home())
        )
        
        if folder:
            self.save_location_var.set(folder)
    
    def _on_theme_change(self, choice: str):
        """Handle theme change."""
        if choice == "System":
            ctk.set_appearance_mode("system")
        elif choice == "Dark":
            ctk.set_appearance_mode("dark")
        elif choice == "Light":
            ctk.set_appearance_mode("light")
    
    def _open_url(self, url: str):
        """Open URL in browser."""
        import webbrowser
        webbrowser.open(url)
    
    def _load_settings(self):
        """Load current settings from config."""
        # General
        self.quality_var.set(
            self.config.get("general.default_quality", "Best")
        )
        self.save_location_var.set(
            self.config.get("general.save_location", str(constants.DEFAULT_MUSIC_DIR))
        )
        self.filename_pattern_var.set(
            self.config.get("general.filename_pattern", "{artist} - {title}")
        )
        self.duplicate_var.set(
            self.config.get("general.duplicate_handling", "rename").capitalize()
        )
        self.theme_var.set(
            self.config.get("general.theme", "System")
        )
        
        # Metadata
        self.auto_metadata_var.set(
            self.config.get("metadata.auto_metadata", True)
        )
        self.fetch_lyrics_var.set(
            self.config.get("metadata.fetch_lyrics", True)
        )
        self.genius_api_var.set(
            self.config.get("metadata.api_keys.genius", "")
        )
        self.lastfm_api_var.set(
            self.config.get("metadata.api_keys.lastfm", "")
        )
        self.discogs_token_var.set(
            self.config.get("metadata.api_keys.discogs", "")
        )
        
        # Advanced
        self.concurrent_var.set(
            str(self.config.get("advanced.concurrent_downloads", constants.DEFAULT_CONCURRENT_DOWNLOADS))
        )
        self.retry_var.set(
            str(self.config.get("advanced.retry_attempts", 3))
        )
        self.timeout_var.set(
            str(self.config.get("advanced.timeout", 30))
        )
        self.engine_var.set(
            self.config.get("advanced.download_engine", "ytdlp")
        )
        self.logging_var.set(
            self.config.get("advanced.logging_level", "INFO")
        )
    
    def _save_settings(self):
        """Save settings to config."""
        # General
        self.config.set("general.default_quality", self.quality_var.get())
        self.config.set("general.save_location", self.save_location_var.get())
        self.config.set("general.filename_pattern", self.filename_pattern_var.get())
        self.config.set("general.duplicate_handling", self.duplicate_var.get().lower())
        self.config.set("general.theme", self.theme_var.get())
        
        # Metadata
        self.config.set("metadata.auto_metadata", self.auto_metadata_var.get())
        self.config.set("metadata.fetch_lyrics", self.fetch_lyrics_var.get())
        
        # Only save non-empty API keys
        genius = self.genius_api_var.get().strip()
        lastfm = self.lastfm_api_var.get().strip()
        discogs = self.discogs_token_var.get().strip()
        
        if genius:
            self.config.set("metadata.api_keys.genius", genius)
        if lastfm:
            self.config.set("metadata.api_keys.lastfm", lastfm)
        if discogs:
            self.config.set("metadata.api_keys.discogs", discogs)
        
        # Advanced
        try:
            concurrent = int(self.concurrent_var.get())
            concurrent = max(1, min(10, concurrent))  # Clamp 1-10
            self.config.set("advanced.concurrent_downloads", concurrent)
        except ValueError:
            pass
        
        try:
            retry = int(self.retry_var.get())
            self.config.set("advanced.retry_attempts", max(0, retry))
        except ValueError:
            pass
        
        try:
            timeout = int(self.timeout_var.get())
            self.config.set("advanced.timeout", max(5, timeout))
        except ValueError:
            pass
        
        self.config.set("advanced.download_engine", self.engine_var.get())
        self.config.set("advanced.logging_level", self.logging_var.get())
        
        # Save to disk
        self.config.save()
        self.changes_made = True
    
    def _import_settings(self):
        """Import settings from JSON file."""
        filename = filedialog.askopenfilename(
            title="Import Settings",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=str(Path.home())
        )
        
        if not filename:
            return
        
        try:
            self.config.import_config(filename)
            self._load_settings()
            
            # Show success message
            success_dialog = ctk.CTkToplevel(self)
            success_dialog.title("Success")
            success_dialog.geometry("300x100")
            success_dialog.transient(self)
            success_dialog.grab_set()
            
            msg = ctk.CTkLabel(
                success_dialog,
                text="✅ Settings imported successfully!",
                font=("SF Pro Display", 13)
            )
            msg.pack(pady=20)
            
            ok_btn = ctk.CTkButton(
                success_dialog,
                text="OK",
                command=success_dialog.destroy,
                width=100
            )
            ok_btn.pack(pady=10)
            
        except Exception as e:
            # Show error
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error")
            error_dialog.geometry("400x120")
            error_dialog.transient(self)
            error_dialog.grab_set()
            
            msg = ctk.CTkLabel(
                error_dialog,
                text=f"❌ Failed to import settings:\n{str(e)}",
                font=("SF Pro Display", 12)
            )
            msg.pack(pady=20)
            
            ok_btn = ctk.CTkButton(
                error_dialog,
                text="OK",
                command=error_dialog.destroy,
                width=100
            )
            ok_btn.pack(pady=10)
    
    def _export_settings(self):
        """Export settings to JSON file."""
        filename = filedialog.asksaveasfilename(
            title="Export Settings",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="youtube_music_downloader_settings.json",
            initialdir=str(Path.home())
        )
        
        if not filename:
            return
        
        try:
            self.config.export_config(filename)
            
            # Show success message
            success_dialog = ctk.CTkToplevel(self)
            success_dialog.title("Success")
            success_dialog.geometry("300x100")
            success_dialog.transient(self)
            success_dialog.grab_set()
            
            msg = ctk.CTkLabel(
                success_dialog,
                text="✅ Settings exported successfully!",
                font=("SF Pro Display", 13)
            )
            msg.pack(pady=20)
            
            ok_btn = ctk.CTkButton(
                success_dialog,
                text="OK",
                command=success_dialog.destroy,
                width=100
            )
            ok_btn.pack(pady=10)
            
        except Exception as e:
            # Show error
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error")
            error_dialog.geometry("400x120")
            error_dialog.transient(self)
            error_dialog.grab_set()
            
            msg = ctk.CTkLabel(
                error_dialog,
                text=f"❌ Failed to export settings:\n{str(e)}",
                font=("SF Pro Display", 12)
            )
            msg.pack(pady=20)
            
            ok_btn = ctk.CTkButton(
                error_dialog,
                text="OK",
                command=error_dialog.destroy,
                width=100
            )
            ok_btn.pack(pady=10)
    
    def _on_save(self):
        """Handle Save button."""
        self._save_settings()
        self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button."""
        self.destroy()
