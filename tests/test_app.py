"""app.py — the Vercel entrypoint — serves the app and answers like the local server."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock
from wsgiref.simple_server import WSGIRequestHandler, make_server

import app


class Quiet(WSGIRequestHandler):
    def log_message(self, *a):
        pass


class VercelApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server("127.0.0.1", 0, app.app, handler_class=Quiet)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def post(self, body, headers=None):
        req = urllib.request.Request(self.base + "/api/claude", data=json.dumps(body).encode(), method="POST",
                                     headers={"content-type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_entrypoint_is_named_app(self):
        self.assertTrue(callable(app.app))

    def test_serves_the_app(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertIn(b"Show Your Working", r.read())

    def test_health(self):
        with urllib.request.urlopen(self.base + "/api/health") as r:
            self.assertIn("key_set", json.loads(r.read()))

    @mock.patch("assistant.llm.ask", return_value={"text": "Here is the idea.", "truncated": False})
    def test_answers_a_doubt(self, ask):
        status, data = self.post({"messages": [{"role": "user", "content": "What is a polynomial?"}]},
                                 {"Origin": self.base})
        self.assertEqual((status, data["text"]), (200, "Here is the idea."))
        self.assertIn("Grades 6 to 10", ask.call_args.args[1])

    def test_other_websites_refused(self):
        status, data = self.post({"messages": [{"role": "user", "content": "hi"}]}, {"Origin": "https://evil.example"})
        self.assertEqual((status, data["error"]["code"]), (403, "not_granted"))

    def test_hidden_files_not_served(self):
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(self.base + "/../.env")


if __name__ == "__main__":
    unittest.main()
