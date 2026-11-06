"""Vercel entrypoint. Vercel looks for `app` in app.py and runs it.

Serves the app (public/index.html) and the tutor API:
  GET  /             the app
  POST /api/tutor    doubts and question papers (uses GEMINI_API_KEY)
  GET  /api/health   shows whether the key is set

On your computer, use  python -m assistant.web  instead.
"""
import json
from urllib.parse import unquote

from assistant import web


def _client(environ) -> str:
    fwd = environ.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[0].strip() if fwd else environ.get("REMOTE_ADDR", "unknown")


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = unquote(environ.get("PATH_INFO", "/"))
    origin = environ.get("HTTP_ORIGIN")
    cors = web.cors_headers(origin)

    def send_json(status_payload):
        status, payload = status_payload
        body = json.dumps(payload).encode()
        start_response(f"{status} {_REASON.get(status, 'OK')}",
                       [("Content-Type", "application/json"), ("Content-Length", str(len(body)))] + cors)
        return [body]

    if method == "OPTIONS":
        start_response("204 No Content", cors)
        return [b""]
    if path in ("/api/health", "/health") and method == "GET":
        return send_json(web.health())
    if path in ("/api/tutor", "/api/claude"):
        if method != "POST":
            return send_json((405, {"error": {"code": "invalid_request", "message": "Use POST."}}))
        hosts = [environ.get("HTTP_HOST"), environ.get("HTTP_X_FORWARDED_HOST")]
        length = int(environ.get("CONTENT_LENGTH") or 0)
        return send_json(web.answer(origin, hosts, length, environ["wsgi.input"].read, _client(environ)))
    if method == "GET":
        found = web.static_file(path)
        if found:
            ctype, data = found
            start_response("200 OK", [("Content-Type", ctype), ("Content-Length", str(len(data)))])
            return [data]
    return send_json((404, {"error": {"code": "not_found", "message": "Not found."}}))


_REASON = {200: "OK", 400: "Bad Request", 402: "Payment Required", 403: "Forbidden", 404: "Not Found",
           405: "Method Not Allowed", 413: "Payload Too Large", 429: "Too Many Requests",
           500: "Internal Server Error", 502: "Bad Gateway"}
