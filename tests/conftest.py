import sys
from pathlib import Path
import types

# Ensure project root is on sys.path for imports when running tests without installation.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Provide a lightweight stub for yt_dlp when the dependency is not installed in test environments.
if "yt_dlp" not in sys.modules:
    sys.modules["yt_dlp"] = types.ModuleType("yt_dlp")

# Provide a minimal stub for requests if it is unavailable.
if "requests" not in sys.modules:
    requests_stub = types.ModuleType("requests")

    class HTTPError(Exception):
        pass

    class Response:
        def __init__(self, status_code: int = 200, json_data=None, text: str = ""):
            self.status_code = status_code
            self._json_data = json_data or {}
            self.text = text

        def raise_for_status(self):
            if self.status_code >= 400:
                raise HTTPError(self.text)

        def json(self):
            return self._json_data

    class Session:
        def get(self, *args, **kwargs):
            raise NotImplementedError("requests stub does not implement network calls")

        def post(self, *args, **kwargs):
            raise NotImplementedError("requests stub does not implement network calls")

    requests_stub.Session = Session
    requests_stub.Response = Response
    requests_stub.HTTPError = HTTPError

    sys.modules["requests"] = requests_stub
