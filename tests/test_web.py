import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

from assistant import web


class Web(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def post(self, body, headers=None):
        req = urllib.request.Request(self.base + "/api/claude", data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json", **(headers or {})}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_serves_the_app(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertIn(b"Show Your Working", r.read())

    def test_blocks_folder_escape(self):
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(self.base + "/../.env")

    @mock.patch("assistant.llm.ask", return_value={"text": "Here is the idea.", "truncated": False})
    def test_answers_a_doubt(self, ask):
        status, data = self.post({"messages": [{"role": "user", "content": "What is a polynomial?"}]})
        self.assertEqual((status, data["text"]), (200, "Here is the idea."))
        self.assertIn("Grades 6 to 10", ask.call_args.args[1])  # safety rules always sent

    def test_other_websites_refused(self):
        status, data = self.post({"messages": [{"role": "user", "content": "hi"}]}, {"Origin": "https://evil.example"})
        self.assertEqual((status, data["error"]["code"]), (403, "not_granted"))


if __name__ == "__main__":
    unittest.main()
