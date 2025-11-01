#!/usr/bin/env python3
"""
YouTube Music Downloader GUI Launcher
Simple launcher script to start the application
"""
import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Check Python version
if sys.version_info < (3, 12):
    print("Error: Python 3.12 or higher is required")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# Check virtual environment
if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("Warning: Not running in a virtual environment")
    print("It's recommended to use a virtual environment (.venv)")
    response = input("Continue anyway? (y/n): ")
    if response.lower() != 'y':
        sys.exit(0)

try:
    # Import and run the main application
    from gui_music_downloader.main import main
    
    print("Starting YouTube Music Downloader GUI...")
    print("Press Ctrl+C to quit\n")
    
    main()
    
except KeyboardInterrupt:
    print("\nApplication terminated by user")
    sys.exit(0)
except ImportError as e:
    print(f"\nError: Failed to import required modules: {e}")
    print("\nPlease ensure all dependencies are installed:")
    print("  1. Activate your virtual environment: source .venv/bin/activate")
    print("  2. Install dependencies: pip install -r requirements.txt")
    print("  3. Install CLI backend: pip install -e ~/Repos/CLI-Music-Downloader")
    sys.exit(1)
except Exception as e:
    print(f"\nUnexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
