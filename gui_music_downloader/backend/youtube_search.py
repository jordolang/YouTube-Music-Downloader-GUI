"""
YouTube Search and Metadata Extraction
Handles YouTube video search, details extraction, and playlist parsing
"""
import re
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import yt_dlp

from ..utils import constants, helpers

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a YouTube search result"""
    video_id: str
    url: str
    title: str
    channel: str
    duration_sec: int
    view_count: int
    thumbnail_url: str
    estimated_size_bytes: Dict[int, int] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate estimated sizes for different qualities"""
        if not self.estimated_size_bytes:
            for quality_name, bitrate in constants.QUALITY_OPTIONS.items():
                self.estimated_size_bytes[bitrate] = helpers.estimate_file_size(
                    self.duration_sec, bitrate
                )
    
    def get_formatted_duration(self) -> str:
        """Get formatted duration string"""
        return helpers.format_duration(self.duration_sec)
    
    def get_formatted_size(self, bitrate: int = 320) -> str:
        """Get formatted size for given bitrate"""
        size_bytes = self.estimated_size_bytes.get(bitrate, 0)
        return helpers.format_bytes(size_bytes)


@dataclass
class PlaylistInfo:
    """Represents a YouTube playlist"""
    playlist_id: str
    url: str
    title: str
    author: str
    video_count: int
    videos: List[SearchResult] = field(default_factory=list)
    
    def get_total_size(self, bitrate: int = 320) -> int:
        """Calculate total size for all videos"""
        return sum(v.estimated_size_bytes.get(bitrate, 0) for v in self.videos)
    
    def get_formatted_total_size(self, bitrate: int = 320) -> str:
        """Get formatted total size"""
        return helpers.format_bytes(self.get_total_size(bitrate))


class YouTubeSearcher:
    """Handles YouTube search and metadata extraction"""
    
    def __init__(self):
        """Initialize YouTube searcher"""
        self.thumbnail_cache_dir = constants.THUMBNAILS_DIR
        self.thumbnail_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # yt-dlp options for metadata extraction
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
    
    def search_videos(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Search YouTube for videos.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        try:
            logger.info(f"Searching YouTube for: {query}")
            
            # Use yt-dlp's search functionality
            ydl_opts = {
                **self.ydl_opts,
                'extract_flat': True,
                'skip_download': True,
            }
            
            search_query = f"ytsearch{limit}:{query}"
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results_raw = ydl.extract_info(search_query, download=False)
            
            if not search_results_raw or 'entries' not in search_results_raw:
                logger.warning(f"No results found for: {query}")
                return []
            
            search_results = []
            for item in search_results_raw['entries']:
                if not item:
                    continue
                    
                try:
                    video_id = item.get('id', '')
                    
                    if not video_id:
                        continue
                    
                    # Build URL
                    url = item.get('url', f"https://www.youtube.com/watch?v={video_id}")
                    
                    # Duration in seconds
                    duration_sec = item.get('duration', 0) or 0
                    
                    # Get thumbnail
                    thumbnail_url = item.get('thumbnail', '')
                    
                    # View count
                    view_count = item.get('view_count', 0) or 0
                    
                    result = SearchResult(
                        video_id=video_id,
                        url=url,
                        title=helpers.clean_metadata_text(item.get('title', 'Unknown')),
                        channel=item.get('uploader', 'Unknown') or item.get('channel', 'Unknown'),
                        duration_sec=duration_sec,
                        view_count=view_count,
                        thumbnail_url=thumbnail_url,
                    )
                    
                    search_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_video_details(self, url: str) -> Optional[SearchResult]:
        """
        Get detailed metadata for a single video using yt-dlp.
        
        Args:
            url: YouTube video URL
            
        Returns:
            SearchResult object or None
        """
        try:
            logger.info(f"Fetching video details: {url}")
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                video_id = info.get('id', '')
                title = helpers.clean_metadata_text(info.get('title', 'Unknown'))
                channel = info.get('uploader', 'Unknown')
                duration_sec = info.get('duration', 0)
                view_count = info.get('view_count', 0)
                thumbnail_url = info.get('thumbnail', '')
                
                result = SearchResult(
                    video_id=video_id,
                    url=url,
                    title=title,
                    channel=channel,
                    duration_sec=duration_sec,
                    view_count=view_count,
                    thumbnail_url=thumbnail_url,
                )
                
                logger.info(f"Retrieved details for: {title}")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get video details: {e}")
            return None
    
    def get_playlist_info(self, url: str) -> Optional[PlaylistInfo]:
        """
        Extract playlist information and videos using yt-dlp.
        
        Args:
            url: YouTube playlist URL
            
        Returns:
            PlaylistInfo object or None
        """
        try:
            logger.info(f"Fetching playlist info: {url}")
            
            ydl_opts = {
                **self.ydl_opts,
                'extract_flat': True,  # Don't download, just get metadata
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info or info.get('_type') != 'playlist':
                    logger.error("URL is not a playlist")
                    return None
                
                playlist_id = info.get('id', '')
                title = info.get('title', 'Unknown Playlist')
                author = info.get('uploader', 'Unknown')
                entries = info.get('entries', [])
                
                # Convert entries to SearchResult objects
                videos = []
                for entry in entries:
                    if not entry:
                        continue
                    
                    try:
                        video_id = entry.get('id', '')
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        
                        video = SearchResult(
                            video_id=video_id,
                            url=video_url,
                            title=helpers.clean_metadata_text(entry.get('title', 'Unknown')),
                            channel=entry.get('uploader', author),
                            duration_sec=entry.get('duration', 0),
                            view_count=entry.get('view_count', 0),
                            thumbnail_url=entry.get('thumbnail', ''),
                        )
                        
                        videos.append(video)
                        
                    except Exception as e:
                        logger.error(f"Error parsing playlist entry: {e}")
                        continue
                
                playlist = PlaylistInfo(
                    playlist_id=playlist_id,
                    url=url,
                    title=title,
                    author=author,
                    video_count=len(videos),
                    videos=videos,
                )
                
                logger.info(f"Retrieved playlist: {title} ({len(videos)} videos)")
                return playlist
                
        except Exception as e:
            logger.error(f"Failed to get playlist info: {e}")
            return None
    
    def is_playlist_url(self, url: str) -> bool:
        """
        Check if URL is a playlist.
        
        Args:
            url: URL to check
            
        Returns:
            True if playlist URL
        """
        playlist_patterns = [
            r'[?&]list=',
            r'/playlist\?',
            r'youtube\.com/playlist',
        ]
        
        return any(re.search(pattern, url) for pattern in playlist_patterns)
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse duration string to seconds.
        
        Formats supported:
        - "MM:SS" (e.g., "3:45")
        - "HH:MM:SS" (e.g., "1:23:45")
        """
        if not duration_str:
            return 0
        
        try:
            parts = duration_str.split(':')
            parts = [int(p) for p in parts]
            
            if len(parts) == 2:  # MM:SS
                return parts[0] * 60 + parts[1]
            elif len(parts) == 3:  # HH:MM:SS
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            else:
                return 0
        except:
            return 0
    
    def _parse_views(self, views_str: str) -> int:
        """
        Parse view count string to integer.
        
        Examples: "1,234,567 views" -> 1234567
        """
        if not views_str:
            return 0
        
        try:
            # Remove non-numeric characters except commas and periods
            cleaned = re.sub(r'[^\d,.]', '', views_str)
            # Remove commas
            cleaned = cleaned.replace(',', '')
            return int(float(cleaned))
        except:
            return 0


# Singleton instance
_searcher_instance: Optional[YouTubeSearcher] = None


def get_searcher() -> YouTubeSearcher:
    """Get global YouTubeSearcher instance"""
    global _searcher_instance
    if _searcher_instance is None:
        _searcher_instance = YouTubeSearcher()
    return _searcher_instance
