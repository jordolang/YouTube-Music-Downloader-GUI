"""
Configuration Manager
Handles app settings persistence and retrieval
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from ..utils import constants

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to config file (defaults to constants.CONFIG_FILE)
        """
        self.config_file = config_file or constants.CONFIG_FILE
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self.config = self._get_default_config()
        else:
            self.config = self._get_default_config()
            self.save()
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (can use dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "general": {
                "default_quality": constants.DEFAULT_QUALITY,
                "save_location": str(constants.DEFAULT_MUSIC_DIR),
                "filename_pattern": constants.DEFAULT_FILENAME_PATTERN,
                "folder_structure": constants.DEFAULT_FOLDER_STRUCTURE,
                "theme": constants.DEFAULT_THEME,
                "search_history": [],
                "favorites": [],
                "duplicate_handling": "rename"  # skip, overwrite, rename
            },
            "metadata": {
                "api_keys": {
                    "genius": "",
                    "lastfm": "",
                    "discogs": ""
                },
                "source_priority": constants.DEFAULT_METADATA_PRIORITY,
                "auto_metadata": True,
                "force_refresh": False,
                "fetch_lyrics": True,
                "album_art_source": "itunes",
                "album_art_size": constants.DEFAULT_ALBUM_ART_SIZE
            },
            "advanced": {
                "concurrent_downloads": constants.DEFAULT_CONCURRENT_DOWNLOADS,
                "retry_attempts": constants.DEFAULT_RETRY_ATTEMPTS,
                "timeout": constants.DEFAULT_TIMEOUT_SECONDS,
                "download_engine": constants.DEFAULT_DOWNLOAD_ENGINE,
                "logging_level": "INFO",
                "enable_notifications": True
            },
            "about": {
                "version": constants.APP_VERSION,
                "last_updated": None
            }
        }
    
    def export_config(self, file_path: Path) -> bool:
        """
        Export configuration to a file.
        
        Args:
            file_path: Path to export to
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Exported configuration to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: Path) -> bool:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to import from
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r') as f:
                imported = json.load(f)
            
            # Validate imported config
            if isinstance(imported, dict):
                self.config = imported
                self.save()
                logger.info(f"Imported configuration from {file_path}")
                return True
            else:
                logger.error("Invalid configuration format")
                return False
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = self._get_default_config()
        self.save()
        logger.info("Reset configuration to defaults")


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
