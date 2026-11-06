"""The Vercel functions in api/ answer the same way as the local server."""
import importlib.util
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(f"api_{name}", ROOT / "api" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.handler


class VercelFunctions(unittest.TestCase):
    def serve(self, handler):
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}"

    @mock.patch("assistant.llm.ask", return_value={"text": "Here is the idea.", "truncated": False})
    def test_claude_function(self, ask):
        base = self.serve(load("claude"))
        req = urllib.request.Request(base + "/api/claude", method="POST", headers={"content-type": "application/json"},
                                     data=json.dumps({"messages": [{"role": "user", "content": "What is a polynomial?"}]}).encode())
        with urllib.request.urlopen(req) as r:
            self.assertEqual(json.loads(r.read())["text"], "Here is the idea.")
        self.assertIn("Grades 6 to 10", ask.call_args.args[1])

    def test_health_function(self):
        base = self.serve(load("health"))
        with urllib.request.urlopen(base + "/api/health") as r:
            self.assertIn("key_set", json.loads(r.read()))

    def test_app_is_in_public(self):
        self.assertTrue((ROOT / "public" / "index.html").is_file())
        self.assertIn('"/api/claude"', (ROOT / "public" / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
