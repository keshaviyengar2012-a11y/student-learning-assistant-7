"""Vercel function: POST /api/claude — the app's doubts and papers go through here."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant.web import ApiHandler  # noqa: E402


class handler(ApiHandler):
    def do_POST(self):
        self.handle_claude()
