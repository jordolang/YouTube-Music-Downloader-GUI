"""
Setup configuration for YouTube Music Downloader GUI
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="youtube-music-downloader-gui",
    version="0.1.0",
    author="Jordan Lang",
    author_email="",
    description="A modern macOS GUI for downloading music from YouTube with Spotify and Apple Music integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jordolang/YouTube-Music-Downloader-GUI",
    project_urls={
        "Bug Tracker": "https://github.com/jordolang/YouTube-Music-Downloader-GUI/issues",
        "Documentation": "https://github.com/jordolang/YouTube-Music-Downloader-GUI#readme",
        "Source Code": "https://github.com/jordolang/YouTube-Music-Downloader-GUI",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS :: MacOS X",
        "Environment :: MacOS X :: Cocoa",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "youtube-music-downloader=gui_music_downloader.main:main",
        ],
        "gui_scripts": [
            "YouTube-Music-Downloader=gui_music_downloader.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gui_music_downloader": [
            "assets/**/*",
            "assets/icons/*",
            "assets/themes/*",
        ],
    },
    keywords="youtube music downloader gui spotify apple-music mp3 yt-dlp",
    license="MIT",
    platforms=["MacOS"],
)
