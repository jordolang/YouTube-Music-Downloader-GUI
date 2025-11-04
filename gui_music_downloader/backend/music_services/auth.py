"""
Token persistence helpers.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import TokenStore
from .models import AuthTokens


class FileTokenStore(TokenStore):
    """
    Simple file-based token store.

    Tokens are serialized per service inside the application config directory.
    In the future this can be swapped with macOS Keychain storage.
    """

    def __init__(self, store_path: Path):
        self._store_path = store_path
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def load(self, service: str) -> Optional[AuthTokens]:
        data = self._read_store().get(service)
        if not data:
            return None
        expires_at = (
            datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )
        return AuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            scope=data.get("scope"),
            token_type=data.get("token_type", "Bearer"),
            raw=data.get("raw", {}),
        )

    def save(self, service: str, tokens: AuthTokens) -> None:
        payload = {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
            "scope": tokens.scope,
            "token_type": tokens.token_type,
            "raw": tokens.raw,
        }
        with self._lock:
            data = self._read_store()
            data[service] = payload
            self._write_store(data)

    def delete(self, service: str) -> None:
        with self._lock:
            data = self._read_store()
            if service in data:
                data.pop(service)
                self._write_store(data)

    def _read_store(self) -> dict:
        if not self._store_path.exists():
            return {}
        try:
            with self._store_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError:
            return {}

    def _write_store(self, data: dict) -> None:
        with self._store_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
