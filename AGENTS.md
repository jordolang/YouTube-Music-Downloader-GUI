# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `gui_music_downloader/`. `main.py` bootstraps the CustomTkinter GUI defined in `gui/main_window.py`. Backend logic sits under `backend/`: `queue_manager.py` handles downloads, `sync_orchestrator.py` coordinates streaming sync, and `music_services/` hosts the Spotify and Apple scaffolding with shared `models.py`. Support modules include `config_manager.py`, `library_manager.py`, `service_factory.py`, `youtube_search.py`, and `downloader.py`. Assets stay in `assets/`, helpers in `utils/`, and the CLI entry is `backend/cli.py`. Tests live in `tests/backend/`. Use `config.json.example`; runtime configs persist to `~/Library/Application Support/YouTubeMusicDownloader/`.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate`: create and enter the Python 3.12 environment.
- `pip install -r requirements.txt`: install GUI and backend dependencies.
- `pip install -e ~/Repos/CLI-Music-Downloader`: link the shared CLI downloader backend.
- `python launcher.py`: launch the GUI; `python -m gui_music_downloader.main` helps debug imports.
- `python -m gui_music_downloader.backend.cli sync spotify --watch`: exercise the sync pipeline with console progress.
- `pytest`: run the backend test suite; add `-k orchestrator -vv` when iterating on queue behavior.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation, snake_case functions, and PascalCase classes. Prefer dataclasses for transport objects (see `backend/music_services/models.py`). Centralize constants in `utils/constants.py`, use `pathlib.Path` for file operations, and log via Loguru (`logger` from `main.py`). Type hints are expected; keep `from __future__ import annotations` in new modules for forward references. Run `ruff check` or your formatter before opening a PR.

## Testing Guidelines
Pytest drives the suite in `tests/backend/`. Mirror module names (`test_library_manager.py`, `test_sync_orchestrator.py`) and isolate external effects by reusing fixtures in `tests/conftest.py` (fake `yt_dlp`, stubbed HTTP). Cover queue edge cases with synchronous execution (`get_queue_manager(synchronous=True)`) to avoid thread hangs. Document new fixtures and assert on progress callbacks when extending `SyncOrchestrator` or service syncing.

## Commit & Pull Request Guidelines
Use Conventional Commit prefixes (`feat:`, `fix:`, `docs:`) as seen in `git log`, keeping subject lines under 72 characters. Branch per feature (`feature/spotify-auth`, `bugfix/queue-deadlock`). Each PR should outline scope, testing evidence, config migrations, and include screenshots or short videos for GUI tweaks. Link issues, call out TODO follow-ups, and request reviews from owners of touched subsystems (GUI, backend, services).

## Configuration & Security Tips
Never commit real tokens or library exports. Extend `config.json.example` when new keys are required and document how to obtain them. The CLI sync command reads credentials from `tokens.json`; keep secrets in the macOS config directory or a vault. Scrub logs before sharing—avoid printing OAuth payloads or refresh tokens.
