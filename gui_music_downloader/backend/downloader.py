"""
Download Engine
Handles downloading and converting YouTube videos to MP3 with metadata
"""
import os
import logging
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import yt_dlp

from ..utils import constants, helpers
from ..backend.config_manager import get_config

logger = logging.getLogger(__name__)


@dataclass
class DownloadProgress:
    """Progress information for a download"""
    status: str  # downloading, processing, complete, error
    percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0  # bytes per second
    eta: int = 0  # seconds
    filename: str = ""
    
    def get_formatted_speed(self) -> str:
        """Get formatted download speed"""
        return helpers.format_speed(self.speed)
    
    def get_formatted_eta(self) -> str:
        """Get formatted ETA"""
        return helpers.calculate_eta(
            self.total_bytes - self.downloaded_bytes,
            self.speed
        )


class DownloadEngine(ABC):
    """Abstract base class for download engines"""
    
    @abstractmethod
    def download(
        self,
        url: str,
        output_path: Path,
        quality: int = 320,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None
    ) -> bool:
        """Download and convert video to MP3"""
        pass


class YtDlpEngine(DownloadEngine):
    """yt-dlp based download engine with metadata enhancement"""
    
    def __init__(self):
        """Initialize download engine"""
        self.config = get_config()
        self._cancel_event = threading.Event()
        
    def download(
        self,
        url: str,
        output_path: Path,
        quality: int = 320,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Download video and convert to MP3.
        
        Args:
            url: YouTube video URL
            output_path: Output file path
            quality: Audio quality in kbps (128, 192, 256, 320)
            progress_callback: Function to call with progress updates
            metadata: Optional metadata dict (artist, title, album, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._cancel_event.clear()
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Progress hook for yt-dlp
            def progress_hook(d):
                if self._cancel_event.is_set():
                    raise Exception("Download cancelled by user")
                
                if not progress_callback:
                    return
                
                status = d.get('status', 'unknown')
                
                if status == 'downloading':
                    progress = DownloadProgress(
                        status='downloading',
                        percent=self._parse_percent(d.get('_percent_str', '0%')),
                        downloaded_bytes=d.get('downloaded_bytes', 0),
                        total_bytes=d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0),
                        speed=d.get('speed', 0) or 0,
                        eta=d.get('eta', 0) or 0,
                        filename=d.get('filename', '')
                    )
                    progress_callback(progress)
                    
                elif status == 'finished':
                    progress = DownloadProgress(
                        status='processing',
                        percent=99.0,
                        filename=d.get('filename', '')
                    )
                    progress_callback(progress)
            
            # Configure yt-dlp options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_path.with_suffix('.%(ext)s')),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': str(quality),
                }],
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'writethumbnail': True,  # Download thumbnail for embedding
                'postprocessor_args': [
                    '-ar', '44100',  # Sample rate
                ],
            }
            
            # Add external downloader if aria2c is available
            if self._check_aria2():
                ydl_opts['external_downloader'] = 'aria2c'
                ydl_opts['external_downloader_args'] = [
                    '--max-connection-per-server=4',
                    '--min-split-size=1M',
                ]
            
            logger.info(f"Starting download: {url}")
            logger.info(f"Output: {output_path}")
            logger.info(f"Quality: {quality} kbps")
            
            # Download and convert
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    logger.error("Failed to extract video info")
                    return False
            
            # Apply metadata if provided or if auto-metadata is enabled
            if self.config.get('metadata.auto_metadata', True):
                logger.info("Applying metadata...")
                self._apply_metadata(output_path, metadata or {}, info)
            
            # Final progress update
            if progress_callback:
                progress_callback(DownloadProgress(
                    status='complete',
                    percent=100.0,
                    filename=str(output_path)
                ))
            
            logger.info(f"Download complete: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            if progress_callback:
                progress_callback(DownloadProgress(
                    status='error',
                    filename=str(output_path)
                ))
            return False
    
    def cancel(self):
        """Cancel the current download"""
        logger.info("Cancelling download...")
        self._cancel_event.set()
    
    def _parse_percent(self, percent_str: str) -> float:
        """Parse percentage string to float"""
        try:
            return float(percent_str.strip('%'))
        except:
            return 0.0
    
    def _check_aria2(self) -> bool:
        """Check if aria2c is available"""
        import shutil
        return shutil.which('aria2c') is not None
    
    def _apply_metadata(
        self,
        file_path: Path,
        metadata: Dict[str, Any],
        video_info: Dict[str, Any]
    ):
        """
        Apply metadata to MP3 file.
        
        Args:
            file_path: Path to MP3 file
            metadata: Metadata dict from user
            video_info: Video info from yt-dlp
        """
        try:
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, APIC
            from mutagen.mp3 import MP3
            
            # Get or create ID3 tags
            try:
                audio = MP3(str(file_path))
                if audio.tags is None:
                    audio.add_tags()
                tags = audio.tags
            except Exception as e:
                logger.error(f"Failed to load MP3 tags: {e}")
                return
            
            # Parse artist and title from video title if not provided
            if not metadata.get('artist') or not metadata.get('title'):
                video_title = video_info.get('title', '')
                artist, title = helpers.parse_artist_title(video_title)
                if not metadata.get('artist'):
                    metadata['artist'] = artist or video_info.get('uploader', 'Unknown')
                if not metadata.get('title'):
                    metadata['title'] = title or video_title
            
            # Set basic tags
            if metadata.get('title'):
                tags.setall('TIT2', [TIT2(encoding=3, text=metadata['title'])])
            
            if metadata.get('artist'):
                tags.setall('TPE1', [TPE1(encoding=3, text=metadata['artist'])])
            
            if metadata.get('album'):
                tags.setall('TALB', [TALB(encoding=3, text=metadata['album'])])
            
            if metadata.get('year'):
                tags.setall('TDRC', [TDRC(encoding=3, text=str(metadata['year']))])
            
            # Add album art if thumbnail was downloaded
            thumbnail_path = file_path.with_suffix('.jpg')
            if not thumbnail_path.exists():
                thumbnail_path = file_path.with_suffix('.webp')
            
            if thumbnail_path.exists():
                try:
                    with open(thumbnail_path, 'rb') as img:
                        tags.setall('APIC', [APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,  # Cover (front)
                            desc='Cover',
                            data=img.read()
                        )])
                    # Clean up thumbnail file
                    thumbnail_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to embed album art: {e}")
            
            # Save tags
            audio.save()
            logger.info("Metadata applied successfully")
            
            # Optionally enhance metadata using CLI backend
            if self.config.get('metadata.force_refresh', False):
                self._enhance_metadata(file_path, metadata)
            
        except Exception as e:
            logger.error(f"Failed to apply metadata: {e}")
    
    def _enhance_metadata(self, file_path: Path, metadata: Dict[str, Any]):
        """Enhance metadata using CLI backend services"""
        try:
            from cli_music_downloader import LyricsMetadataHandler
            
            genius_key = self.config.get('metadata.api_keys.genius', '')
            if not genius_key:
                logger.info("Genius API key not configured, skipping lyrics")
                return
            
            handler = LyricsMetadataHandler(genius_key)
            
            artist = metadata.get('artist', '')
            title = metadata.get('title', '')
            
            if artist and title:
                logger.info(f"Fetching lyrics for: {artist} - {title}")
                lyrics = handler.get_lyrics(artist, title)
                
                if lyrics:
                    # Add lyrics to file
                    from mutagen.id3 import USLT
                    from mutagen.mp3 import MP3
                    
                    audio = MP3(str(file_path))
                    if audio.tags:
                        audio.tags.setall('USLT', [USLT(
                            encoding=3,
                            lang='eng',
                            desc='',
                            text=lyrics
                        )])
                        audio.save()
                        logger.info("Lyrics added successfully")
            
        except ImportError:
            logger.warning("CLI backend not available for metadata enhancement")
        except Exception as e:
            logger.error(f"Failed to enhance metadata: {e}")


# Singleton instance
_engine_instance: Optional[YtDlpEngine] = None


def get_engine() -> YtDlpEngine:
    """Get global download engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = YtDlpEngine()
    return _engine_instance
