"""
Utilities for launching a MusicKit-based authentication flow to mint user tokens.
"""
from __future__ import annotations

import json
import logging
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class MusicKitAuthenticator:
    """
    Launches a temporary HTTP server and MusicKit JS page to retrieve a Music User Token.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        browser_opener: Callable[[str], bool | None] = webbrowser.open,
    ):
        self._host = host
        self._port = port
        self._browser_opener = browser_opener

    def request_user_token(self, developer_token: str, timeout: int = 300) -> str:
        """
        Start the MusicKit flow and return the issued Music User Token.
        """
        if not developer_token:
            raise ValueError("Developer token is required for MusicKit authentication")

        port = self._port or self._find_available_port()
        result: dict[str, Optional[str]] = {"token": None, "error": None}
        event = threading.Event()

        html = self._build_html_page(developer_token, self._host, port)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # type: ignore[override]
                if self.path not in {"/", "/index.html"}:
                    self.send_error(404)
                    return
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):  # type: ignore[override]
                if self.path != "/token":
                    self.send_error(404)
                    return
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length)
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    self.send_error(400, "Invalid JSON payload")
                    return

                token = payload.get("token")
                if token:
                    result["token"] = token
                    response = {"status": "received"}
                    event.set()
                else:
                    result["error"] = payload.get("error") or "Token missing"
                    response = {"status": "error"}

                body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args) -> None:  # noqa: A003
                return  # Suppress default logging

        server = HTTPServer((self._host, port), Handler)

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        auth_url = f"http://{self._host}:{port}/"
        logger.info("Opening browser for MusicKit authentication at %s", auth_url)
        opened = False
        try:
            opened = bool(self._browser_opener(auth_url))
        except Exception as exc:
            logger.warning("Failed to open browser automatically: %s", exc)

        if not opened:
            logger.info("Please open %s manually to complete authentication", auth_url)

        try:
            completed = event.wait(timeout=timeout)
            if not completed:
                raise TimeoutError("MusicKit authentication timed out")
            if result["error"]:
                raise RuntimeError(result["error"])
            if not result["token"]:
                raise RuntimeError("MusicKit authentication failed to deliver a token")
            return result["token"]  # type: ignore[return-value]
        finally:
            server.shutdown()
            server.server_close()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _find_available_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    @staticmethod
    def _build_html_page(developer_token: str, host: str, port: int) -> str:
        """
        Render the inline MusicKit authorization page served by the local HTTP server.
        """
        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Apple Music Authorization</title>
    <script src="https://js-cdn.music.apple.com/musickit/v3/musickit.js"></script>
    <style>
      body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        margin: 40px;
        color: #222;
      }}
      .container {{
        max-width: 520px;
        margin: 0 auto;
        text-align: center;
      }}
      button {{
        border: none;
        background: #fc3c44;
        color: white;
        font-size: 16px;
        padding: 12px 24px;
        border-radius: 8px;
        cursor: pointer;
      }}
      button:disabled {{
        background: #ccc;
        cursor: not-allowed;
      }}
      #status {{
        margin-top: 24px;
        font-size: 15px;
      }}
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Authorize Apple Music</h1>
      <p>Sign in with your Apple ID to allow the downloader to access your library.</p>
      <button id="auth-btn">Sign in to Apple Music</button>
      <div id="status">Waiting for authorization…</div>
    </div>
    <script>
      async function authorize() {{
        const status = document.getElementById('status');
        const button = document.getElementById('auth-btn');
        status.textContent = 'Loading MusicKit…';
        button.disabled = true;
        try {{
          await MusicKit.configure({{
            developerToken: "{developer_token}",
            app: {{
              name: "YouTube Music Downloader",
              build: "1.0"
            }}
          }});
          const music = MusicKit.getInstance();
          status.textContent = 'Waiting for Apple sign-in…';
          const token = await music.authorize();
          status.textContent = 'Delivering token to the app…';
          await fetch('http://{host}:{port}/token', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ token }})
          }});
          status.textContent = 'Authorization complete. You may close this window.';
        }} catch (error) {{
          console.error(error);
          status.textContent = 'Authorization failed. Please close this window and try again.';
          await fetch('http://{host}:{port}/token', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ error: error && error.message ? error.message : 'Authorization failed' }})
          }});
        }}
      }}
      document.getElementById('auth-btn').addEventListener('click', authorize);
    </script>
  </body>
</html>
"""
