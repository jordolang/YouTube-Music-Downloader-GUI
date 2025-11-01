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
        
        # Create a simple window for now (will be replaced with full GUI)
        app = ctk.CTk()
        app.title(f"{constants.APP_NAME} v{constants.APP_VERSION}")
        app.geometry("1000x700")
        
        # Center window on screen
        app.update_idletasks()
        width = app.winfo_width()
        height = app.winfo_height()
        x = (app.winfo_screenwidth() // 2) - (width // 2)
        y = (app.winfo_screenheight() // 2) - (height // 2)
        app.geometry(f'{width}x{height}+{x}+{y}')
        
        # Create a welcome frame
        welcome_frame = ctk.CTkFrame(app)
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Welcome message
        title_label = ctk.CTkLabel(
            welcome_frame,
            text=f"🎵 {constants.APP_NAME}",
            font=("SF Pro Display", 32, "bold")
        )
        title_label.pack(pady=(40, 10))
        
        subtitle_label = ctk.CTkLabel(
            welcome_frame,
            text=f"Version {constants.APP_VERSION}",
            font=("SF Pro Display", 16)
        )
        subtitle_label.pack(pady=(0, 40))
        
        info_label = ctk.CTkLabel(
            welcome_frame,
            text="🚧 Application is under development\n\n"
                 "The GUI implementation is in progress.\n"
                 "Check the README.md for development status and roadmap.",
            font=("SF Pro Display", 14),
            justify="center"
        )
        info_label.pack(pady=20)
        
        # Status info
        status_frame = ctk.CTkFrame(welcome_frame)
        status_frame.pack(pady=20, padx=40, fill="x")
        
        status_items = [
            ("✅", "Project structure initialized"),
            ("✅", "Configuration system ready"),
            ("✅", "Utilities implemented"),
            ("🔄", "YouTube search - In Progress"),
            ("🔄", "Download engine - In Progress"),
            ("🔄", "Main GUI - In Progress"),
        ]
        
        for icon, text in status_items:
            status_label = ctk.CTkLabel(
                status_frame,
                text=f"{icon}  {text}",
                font=("SF Pro Display", 12),
                anchor="w"
            )
            status_label.pack(pady=5, padx=20, anchor="w")
        
        # Config info
        config_label = ctk.CTkLabel(
            welcome_frame,
            text=f"Configuration: {config.config_file}\n"
                 f"Logs: {constants.LOG_FILE}",
            font=("SF Pro Display", 10),
            text_color="gray"
        )
        config_label.pack(side="bottom", pady=20)
        
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
