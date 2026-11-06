"""llm.py speaks Gemini's REST format and explains its errors."""
import io
import json
import unittest
import urllib.error
from unittest import mock

from assistant import config, llm


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def reply(payload):
    return mock.patch("urllib.request.urlopen", return_value=FakeResponse(json.dumps(payload).encode()))


def http_error(code, message, status=""):
    body = json.dumps({"error": {"code": code, "message": message, "status": status}}).encode()
    return mock.patch("urllib.request.urlopen",
                      side_effect=urllib.error.HTTPError("u", code, message, {}, io.BytesIO(body)))


class Gemini(unittest.TestCase):
    def setUp(self):
        self.key = mock.patch.object(config, "API_KEY", "test-key")
        self.key.start()
        self.addCleanup(self.key.stop)

    def test_request_shape(self):
        with reply({"candidates": [{"content": {"parts": [{"text": "Hi"}]}, "finishReason": "STOP"}]}) as op:
            llm.ask([{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"},
                     {"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "AAA"}},
                                                  {"type": "text", "text": "this?"}]}], "rules")
        req = op.call_args.args[0]
        body = json.loads(req.data)
        self.assertIn(":generateContent", req.full_url)
        self.assertIn(config.MODEL, req.full_url)
        self.assertEqual(req.get_header("X-goog-api-key"), "test-key")
        self.assertEqual(body["systemInstruction"], {"parts": [{"text": "rules"}]})
        self.assertEqual([c["role"] for c in body["contents"]], ["user", "model", "user"])
        self.assertEqual(body["contents"][2]["parts"][0], {"inlineData": {"mimeType": "image/png", "data": "AAA"}})
        self.assertEqual(body["generationConfig"]["thinkingConfig"], {"thinkingLevel": config.THINKING})

    def test_quick_tier_uses_quick_model(self):
        with reply({"candidates": [{"content": {"parts": [{"text": "Hi"}]}}]}) as op:
            llm.ask([{"role": "user", "content": "q"}], "s", tier="quick")
        self.assertIn(config.QUICK_MODEL, op.call_args.args[0].full_url)

    def test_thoughts_are_left_out(self):
        with reply({"candidates": [{"content": {"parts": [{"text": "thinking...", "thought": True}, {"text": "Answer"}]},
                                    "finishReason": "MAX_TOKENS"}]}):
            self.assertEqual(llm.ask([{"role": "user", "content": "q"}], "s"), {"text": "Answer", "truncated": True})

    def test_blocked(self):
        with reply({"promptFeedback": {"blockReason": "SAFETY"}}):
            with self.assertRaises(llm.LLMError) as e:
                llm.ask([{"role": "user", "content": "q"}], "s")
        self.assertEqual(e.exception.code, "refused")

    def test_errors_explained(self):
        cases = [((400, "API key not valid. Please pass a valid API key.", "INVALID_ARGUMENT"), "bad_key"),
                 ((404, "models/x is not found for API version v1beta", "NOT_FOUND"), "bad_model"),
                 ((429, "You exceeded your current quota", "RESOURCE_EXHAUSTED"), "rate_limited"),
                 ((403, "Permission denied", "PERMISSION_DENIED"), "bad_key"),
                 ((400, "Billing is required for this model", "FAILED_PRECONDITION"), "no_credit")]
        for args, code in cases:
            with http_error(*args), self.subTest(code=code):
                with self.assertRaises(llm.LLMError) as e:
                    llm.ask([{"role": "user", "content": "q"}], "s")
                self.assertEqual(e.exception.code, code)

    def test_no_key(self):
        with mock.patch.object(config, "API_KEY", ""):
            with self.assertRaises(llm.LLMError) as e:
                llm.ask([{"role": "user", "content": "q"}], "s")
        self.assertEqual(e.exception.code, "no_key")


if __name__ == "__main__":
    unittest.main()
