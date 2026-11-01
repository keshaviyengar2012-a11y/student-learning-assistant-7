import unittest

from assistant import tutor
from assistant.llm import LLMError


class CleanMessages(unittest.TestCase):
    def test_merges_two_user_turns(self):
        out = tutor.clean_messages([{"role": "user", "content": "rules"}, {"role": "user", "content": "doubt"}])
        self.assertEqual([m["role"] for m in out], ["user"])
        self.assertEqual(len(out[0]["content"]), 2)

    def test_keeps_conversation_order(self):
        out = tutor.clean_messages([{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}, {"role": "user", "content": "c"}])
        self.assertEqual([m["role"] for m in out], ["user", "assistant", "user"])

    def test_refuses_empty(self):
        with self.assertRaises(LLMError):
            tutor.clean_messages([])

    def test_drops_unknown_blocks(self):
        out = tutor.clean_content([{"type": "text", "text": "hi"}, {"type": "tool_use"},
                                   {"type": "image", "source": {"type": "base64", "media_type": "image/svg+xml", "data": "x"}}])
        self.assertEqual(out, [{"type": "text", "text": "hi"}])


class Limits(unittest.TestCase):
    def test_per_student_limit(self):
        lim = tutor.RateLimiter(3)
        self.assertEqual([lim.allow("a") for _ in range(4)], [True, True, True, False])
        self.assertTrue(lim.allow("b"))


if __name__ == "__main__":
    unittest.main()
