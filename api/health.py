"""Vercel function: GET /api/health — shows whether the API key is set."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.web import ApiHandler  # noqa: E402


class handler(ApiHandler):
    def do_GET(self):
        self.handle_health()
