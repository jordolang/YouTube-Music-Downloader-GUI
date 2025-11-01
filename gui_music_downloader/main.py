"""
Main application entry point
"""
import sys
import logging
from pathlib import Path

# Setup logging
from loguru import logger
from .utils import constants

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    constants.LOG_FILE,
    rotation="10 MB",
    retention="1 week",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)
logger.add(sys.stderr, level="INFO")


def main():
    """Main application entry point"""
    logger.info(f"Starting {constants.APP_NAME} v{constants.APP_VERSION}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Config directory: {constants.CONFIG_DIR}")
    
    try:
        # Import GUI components
        import customtkinter as ctk
        from .backend.config_manager import get_config
        
        # Initialize configuration
        config = get_config()
        logger.info("Configuration loaded successfully")
        
        # Set appearance mode
        theme = config.get("general.theme", "System")
        if theme == "Dark":
            ctk.set_appearance_mode("dark")
        elif theme == "Light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("system")
        
        # Set default color theme
        ctk.set_default_color_theme("blue")
        
        logger.info("Creating main window...")
        
        # Import and create the main window
        from .gui.main_window import MainWindow
        
        app = MainWindow()
        
        logger.info("Application window created successfully")
        
        # Run the application
        app.mainloop()
        
    except ImportError as e:
        logger.error(f"Failed to import required dependencies: {e}")
        logger.error("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        logger.info("Application shutting down")


if __name__ == "__main__":
    main()
