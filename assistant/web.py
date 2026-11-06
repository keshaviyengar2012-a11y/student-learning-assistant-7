"""The web server: hosts the app and passes its questions to Claude.

On your computer:  python -m assistant.web     then open http://127.0.0.1:8000
On Vercel:         app.py (in the main folder) uses the same functions.
"""
from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from . import config, tutor
from .llm import LLMError

MAX_BODY = 4_000_000  # bytes; room for a photo of working (Vercel's limit is 4.5 MB)


def origin_allowed(origin: str | None, hosts) -> bool:
    """Only the app's own website (plus ALLOWED_ORIGINS) may use the tutor."""
    if not origin:
        return True
    own = {f"{scheme}://{h}" for h in hosts if h for scheme in ("http", "https")}
    return origin in own or origin in config.ALLOWED_ORIGINS


def cors_headers(origin: str | None) -> list[tuple[str, str]]:
    if origin and origin in config.ALLOWED_ORIGINS:
        return [("Access-Control-Allow-Origin", origin), ("Access-Control-Allow-Methods", "POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "content-type"), ("Vary", "Origin")]
    return []


def health() -> tuple[int, dict]:
    return 200, {"ok": True, "key_set": bool(config.API_KEY)}


def answer(origin, hosts, length: int, read, client: str) -> tuple[int, dict]:
    """POST /api/claude — shared by the local server and app.py on Vercel."""
    if not origin_allowed(origin, hosts):
        return 403, {"error": {"code": "not_granted", "message": "This site is not allowed to use the tutor."}}
    if length > MAX_BODY:
        return 413, {"error": {"code": "prompt_too_large", "message": "That request is too big."}}
    try:
        body = json.loads(read(length) or b"{}")
    except json.JSONDecodeError:
        return 400, {"error": {"code": "invalid_request", "message": "Bad JSON."}}
    try:
        return 200, tutor.handle(body, client)
    except LLMError as e:
        print(f"  ✗ Claude problem: {e.code} — {e.message}")
        return e.status, {"error": {"code": e.code, "message": e.message}}


def static_file(path: str):
    """A file from public/, or None. "/" is the app."""
    if path in ("/", ""):
        path = "/index.html"
    file = (config.APP_DIR / path.lstrip("/")).resolve()
    if config.APP_DIR.resolve() not in file.parents or not file.is_file():
        return None
    ctype = (mimetypes.guess_type(file.name)[0] or "application/octet-stream") + ("; charset=utf-8" if file.suffix == ".html" else "")
    return ctype, file.read_bytes()


class Handler(BaseHTTPRequestHandler):
    """Local server: the app from public/ plus the API, all on one address."""
    server_version = "ShowYourWorking/1.0"

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in cors_headers(self.headers.get("Origin")):
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _client(self) -> str:
        fwd = self.headers.get("X-Forwarded-For")
        return fwd.split(",")[0].strip() if fwd else self.client_address[0]

    def log_message(self, fmt, *args):  # keep the terminal tidy
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in cors_headers(self.headers.get("Origin")):
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/health", "/api/health"):
            return self._json(*health())
        found = static_file(path)
        if not found:
            return self._json(404, {"error": {"code": "not_found", "message": "Not found."}})
        ctype, data = found
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if urlparse(self.path).path != "/api/claude":
            return self._json(404, {"error": {"code": "not_found", "message": "Not found."}})
        hosts = [self.headers.get("Host"), self.headers.get("X-Forwarded-Host")]
        self._json(*answer(self.headers.get("Origin"), hosts, int(self.headers.get("Content-Length") or 0),
                           self.rfile.read, self._client()))


FIXES = {
    "no_key": "Put ANTHROPIC_API_KEY=sk-ant-... in a file named exactly .env next to README.md, then restart.",
    "bad_key": "The key was rejected. Copy it again from console.anthropic.com → API keys (no spaces), or make a new one.",
    "no_credit": "Add credit at console.anthropic.com → Billing. New keys do not work until there is credit.",
    "bad_model": "Your account cannot use that model. Set MODEL=claude-haiku-5-5 in .env and restart.",
    "no_internet": "This computer could not reach api.anthropic.com. Check your internet / firewall / VPN.",
    "rate_limited": "Claude is busy or your account's limit was hit. Wait a minute and try again.",
}


def check_claude():
    """One tiny request at start-up, so problems show here instead of in the app."""
    from . import llm
    try:
        llm.ask([{"role": "user", "content": "Reply with the word OK."}], "Reply with one word.", max_tokens=5)
        print("  ✓ Claude is connected. Doubts and papers will work.")
    except LLMError as e:
        print(f"  ✗ Claude is NOT working: {e.message}")
        print(f"    Fix: {FIXES.get(e.code, 'Send this message to whoever set the app up.')}")


def main():
    server = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    print(f"Show Your Working is running at http://{'127.0.0.1' if config.HOST == '0.0.0.0' else config.HOST}:{config.PORT}")
    print(f"  Key from .env: {'found (' + config.API_KEY[:10] + '…)' if config.API_KEY else 'NOT FOUND'}")
    check_claude()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
