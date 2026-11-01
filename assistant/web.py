"""The web server: hosts the app and passes its questions to Claude.

Run:  python -m assistant.web     then open http://127.0.0.1:8000
"""
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from . import config, tutor
from .llm import LLMError

MAX_BODY = 6_000_000  # bytes; room for a photo of working


class Handler(BaseHTTPRequestHandler):
    server_version = "ShowYourWorking/1.0"

    # ---------- helpers ----------
    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        own = {f"http://{self.headers.get('Host')}", f"https://{self.headers.get('Host')}"}
        return origin in own or origin in config.ALLOWED_ORIGINS

    def _cors(self):
        origin = self.headers.get("Origin")
        if origin and origin in config.ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "content-type")
            self.send_header("Vary", "Origin")

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _client(self) -> str:
        fwd = self.headers.get("X-Forwarded-For")  # set by hosts like Render
        return fwd.split(",")[0].strip() if fwd else self.client_address[0]

    def log_message(self, fmt, *args):  # keep the terminal tidy
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)

    # ---------- routes ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/health":
            return self._json(200, {"ok": True, "key_set": bool(config.API_KEY)})
        if path in ("/", ""):
            path = "/index.html"
        file = (config.APP_DIR / path.lstrip("/")).resolve()
        if config.APP_DIR.resolve() not in file.parents or not file.is_file():
            return self._json(404, {"error": {"code": "not_found", "message": "Not found."}})
        data = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", (mimetypes.guess_type(file.name)[0] or "application/octet-stream") + ("; charset=utf-8" if file.suffix == ".html" else ""))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlparse(self.path).path != "/api/claude":
            return self._json(404, {"error": {"code": "not_found", "message": "Not found."}})
        if not self._origin_ok():
            return self._json(403, {"error": {"code": "not_granted", "message": "This site is not allowed to use the tutor."}})
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self._json(413, {"error": {"code": "prompt_too_large", "message": "That request is too big."}})
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": {"code": "invalid_request", "message": "Bad JSON."}})
        try:
            return self._json(200, tutor.handle(body, self._client()))
        except LLMError as e:
            return self._json(e.status, {"error": {"code": e.code, "message": e.message}})


def main():
    server = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    print(f"Show Your Working is running at http://{config.HOST}:{config.PORT}")
    if not config.API_KEY:
        print("Warning: ANTHROPIC_API_KEY is not set in .env — doubts and new papers will not work.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
