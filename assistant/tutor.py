"""Rules every request follows before it reaches Claude."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from . import config, llm

# Always sent to Claude, whatever the page asks. The users are school students.
SAFETY = "\n".join([
    "You are the tutor inside Show Your Working, a study app for school students in Grades 6 to 10 (roughly ages 11 to 16).",
    "Only help with school study: explaining topics, clearing doubts, and writing practice questions.",
    "Keep everything age-appropriate. Politely decline anything unrelated to studying or not suitable for children, and steer back to the subject.",
    "Never ask for or encourage sharing personal details such as full name, address, school, phone number or photos of people.",
    "If a student seems upset or mentions being hurt or unsafe, respond kindly and tell them to talk to a parent, teacher or another trusted adult.",
])

IMAGE_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


def clean_content(content):
    """Keep only text and image blocks, in the shape Claude expects."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    out = []
    for b in content:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text":
            out.append({"type": "text", "text": str(b.get("text", ""))})
        elif b.get("type") == "image":
            src = b.get("source") or {}
            if src.get("type") == "base64" and src.get("media_type") in IMAGE_TYPES:
                out.append({"type": "image", "source": {"type": "base64", "media_type": src["media_type"], "data": str(src.get("data", ""))}})
    return out


def clean_messages(messages):
    """Claude needs turns to alternate user / assistant, starting with the user."""
    def blocks(x):
        return [{"type": "text", "text": x}] if isinstance(x, str) else x

    merged = []
    for m in messages if isinstance(messages, list) else []:
        role = "assistant" if isinstance(m, dict) and m.get("role") == "assistant" else "user"
        content = clean_content(m.get("content") if isinstance(m, dict) else None)
        if not content:
            continue
        if merged and merged[-1]["role"] == role:
            merged[-1]["content"] = blocks(merged[-1]["content"]) + blocks(content)
        else:
            merged.append({"role": role, "content": content})
    if not merged or merged[0]["role"] != "user":
        raise llm.LLMError("invalid_request", "No question was sent.", 400)
    return merged


class RateLimiter:
    """Allows each student (by IP address) a number of requests per hour."""

    def __init__(self, per_hour: int):
        self.per_hour = per_hour
        self.hits = defaultdict(deque)

    def allow(self, who: str) -> bool:
        now, q = time.time(), self.hits[who]
        while q and now - q[0] > 3600:
            q.popleft()
        if len(q) >= self.per_hour:
            return False
        q.append(now)
        if len(self.hits) > 5000:
            self.hits.clear()
        return True


limiter = RateLimiter(config.PER_STUDENT_PER_HOUR)


def handle(body: dict, who: str) -> dict:
    """One request from the app: {"messages": [...], "tier": "default" | "quick"}."""
    if not limiter.allow(who):
        raise llm.LLMError("rate_limited", "Too many requests. Try again later.", 429)
    messages = clean_messages(body.get("messages"))
    return llm.ask(messages, SAFETY, tier=body.get("tier", "default"))
