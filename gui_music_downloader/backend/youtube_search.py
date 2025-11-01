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
    ranking_score: float = 0.0  # Higher is better
    
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
            
            # Rank results by quality (official > high views > avoid live)
            self._rank_results(search_results)
            
            # Sort by ranking score (highest first)
            search_results.sort(key=lambda x: x.ranking_score, reverse=True)
            
            logger.info(f"Found {len(search_results)} results (ranked by quality)")
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
    
    def _rank_results(self, results: List[SearchResult]):
        """
        Rank search results based on quality indicators.
        
        Scoring criteria:
        - Higher view count = better (normalized)
        - "Official" in title = big bonus
        - "Live" in title = penalty
        - Official artist channels = bonus
        - "Audio" or "Video" = slight bonus
        - "Lyrics" = slight penalty (lyric videos are often lower quality)
        """
        if not results:
            return
        
        # Find max views for normalization
        max_views = max((r.view_count for r in results), default=1)
        
        for result in results:
            score = 0.0
            
            title_lower = result.title.lower()
            channel_lower = result.channel.lower()
            
            # 1. View count (0-40 points, normalized)
            if max_views > 0:
                view_score = (result.view_count / max_views) * 40
                score += view_score
            
            # 2. "Official" indicators (+30 points)
            if 'official' in title_lower:
                score += 30
                logger.debug(f"  +30: Official in title: {result.title}")
            
            if 'official' in channel_lower or 'vevo' in channel_lower:
                score += 20
                logger.debug(f"  +20: Official channel: {result.channel}")
            
            # 3. Content type bonuses
            if 'official video' in title_lower:
                score += 15
            elif 'official audio' in title_lower:
                score += 12
            elif 'music video' in title_lower:
                score += 8
            
            # 4. Penalties for unwanted content
            if 'live' in title_lower:
                score -= 25
                logger.debug(f"  -25: Live performance: {result.title}")
            
            if 'cover' in title_lower:
                score -= 15
                logger.debug(f"  -15: Cover version")
            
            if 'lyrics' in title_lower and 'official' not in title_lower:
                score -= 10
                logger.debug(f"  -10: Lyric video (unofficial)")
            
            if 'karaoke' in title_lower:
                score -= 20
            
            if 'instrumental' in title_lower:
                score -= 15
            
            if 'remix' in title_lower and 'official' not in title_lower:
                score -= 10
            
            # 5. Duration penalty for very long or very short videos
            # Most songs are 2-6 minutes (120-360 seconds)
            if result.duration_sec > 0:
                if result.duration_sec < 60:  # Too short
                    score -= 15
                elif result.duration_sec > 600:  # Too long (10+ minutes)
                    score -= 10
            
            result.ranking_score = score
            logger.debug(f"Result score: {score:.1f} - {result.title} ({result.view_count:,} views)")
    
    def _parse_views(self, views_str: str) -> int:
        """
        Parse view count string to integer.
        
        Examples: 
        - "1,234,567 views" -> 1234567
        - "152M views" -> 152000000
        - "876K views" -> 876000
        - "1.5B views" -> 1500000000
        """
        if not views_str:
            return 0
        
        try:
            views_str = views_str.upper()
            
            # Check for multipliers
            multiplier = 1
            if 'B' in views_str:  # Billions
                multiplier = 1_000_000_000
                views_str = views_str.replace('B', '')
            elif 'M' in views_str:  # Millions
                multiplier = 1_000_000
                views_str = views_str.replace('M', '')
            elif 'K' in views_str:  # Thousands
                multiplier = 1_000
                views_str = views_str.replace('K', '')
            
            # Remove non-numeric characters except periods
            cleaned = re.sub(r'[^\d.]', '', views_str)
            
            if not cleaned:
                return 0
            
            # Convert to number and apply multiplier
            return int(float(cleaned) * multiplier)
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
