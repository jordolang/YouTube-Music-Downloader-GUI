"""
Utility helper functions
"""
import re
import unicodedata
from pathlib import Path
from typing import Optional
from datetime import timedelta


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize filename by removing/replacing invalid characters.
    
    Args:
        filename: The filename to sanitize
        replacement: Character to use for invalid chars
        
    Returns:
        Sanitized filename
    """
    # Normalize unicode
    filename = unicodedata.normalize('NFKD', filename)
    
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, replacement, filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length (macOS max is 255)
    if len(filename) > 200:
        name, ext = Path(filename).stem, Path(filename).suffix
        filename = name[:200-len(ext)] + ext
    
    return filename or "untitled"


def format_bytes(bytes_val: int) -> str:
    """
    Format bytes into human-readable format.
    
    Args:
        bytes_val: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to MM:SS or HH:MM:SS.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 0:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_speed(bytes_per_sec: float) -> str:
    """
    Format download speed.
    
    Args:
        bytes_per_sec: Speed in bytes per second
        
    Returns:
        Formatted speed string (e.g., "1.5 MB/s")
    """
    return f"{format_bytes(int(bytes_per_sec))}/s"


def calculate_eta(bytes_remaining: int, bytes_per_sec: float) -> str:
    """
    Calculate estimated time remaining.
    
    Args:
        bytes_remaining: Bytes left to download
        bytes_per_sec: Current download speed
        
    Returns:
        Formatted ETA string
    """
    if bytes_per_sec <= 0:
        return "Unknown"
    
    seconds_remaining = int(bytes_remaining / bytes_per_sec)
    
    if seconds_remaining < 60:
        return f"{seconds_remaining}s"
    elif seconds_remaining < 3600:
        minutes = seconds_remaining // 60
        return f"{minutes}m"
    else:
        hours = seconds_remaining // 3600
        minutes = (seconds_remaining % 3600) // 60
        return f"{hours}h {minutes}m"


def estimate_file_size(duration_sec: int, bitrate_kbps: int) -> int:
    """
    Estimate file size based on duration and bitrate.
    
    Args:
        duration_sec: Duration in seconds
        bitrate_kbps: Bitrate in kbps
        
    Returns:
        Estimated file size in bytes
    """
    # Formula: (bitrate in kbps * duration in seconds * 1000) / 8
    return int((bitrate_kbps * duration_sec * 1000) / 8)


def resolve_duplicate_path(file_path: Path, strategy: str = "rename") -> Path:
    """
    Resolve duplicate file paths.
    
    Args:
        file_path: Original file path
        strategy: How to handle duplicates ("skip", "overwrite", "rename")
        
    Returns:
        Resolved file path
    """
    if strategy == "skip" or strategy == "overwrite":
        return file_path
    
    # Rename strategy
    if not file_path.exists():
        return file_path
    
    stem = file_path.stem
    suffix = file_path.suffix
    parent = file_path.parent
    counter = 1
    
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
        if counter > 1000:  # Safety limit
            return file_path


def parse_artist_title(text: str) -> tuple[str, str]:
    """
    Parse artist and title from a string.
    
    Common patterns:
    - "Artist - Title"
    - "Artist: Title"
    - "Title by Artist"
    
    Args:
        text: String to parse
        
    Returns:
        Tuple of (artist, title)
    """
    # Try "Artist - Title" pattern
    if " - " in text:
        parts = text.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    
    # Try "Artist: Title" pattern
    if ": " in text:
        parts = text.split(": ", 1)
        return parts[0].strip(), parts[1].strip()
    
    # Try "Title by Artist" pattern
    if " by " in text.lower():
        match = re.search(r'(.+?)\s+by\s+(.+)', text, re.IGNORECASE)
        if match:
            return match.group(2).strip(), match.group(1).strip()
    
    # Default: use entire string as title
    return "", text.strip()


def clean_metadata_text(text: str) -> str:
    """
    Clean metadata text by removing common noise patterns.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Patterns to remove
    patterns = [
        r'\(official\s+video\)',
        r'\(official\s+audio\)',
        r'\(lyrics?\)',
        r'\[official\s+video\]',
        r'\[official\s+audio\]',
        r'\[lyrics?\]',
        r'\(hd\)',
        r'\[hd\]',
        r'\(hq\)',
        r'\[hq\]',
    ]
    
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra spaces
    cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()


def expand_path(path: str) -> Path:
    """
    Expand path with environment variables and user home.
    
    Args:
        path: Path string
        
    Returns:
        Expanded Path object
    """
    return Path(path).expanduser().resolve()
