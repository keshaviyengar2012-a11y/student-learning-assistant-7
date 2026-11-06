"""The one place that talks to Gemini. Uses only the Python standard library."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from . import config

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class LLMError(Exception):
    """A failure the app knows how to explain. `code` matches the app's messages."""

    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def to_gemini(messages) -> list[dict]:
    """The app's conversation (user/assistant, text and image blocks) in Gemini's shape."""
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        blocks = [{"type": "text", "text": m["content"]}] if isinstance(m["content"], str) else m["content"]
        parts = []
        for b in blocks:
            if b.get("type") == "text" and b.get("text"):
                parts.append({"text": b["text"]})
            elif b.get("type") == "image":
                parts.append({"inlineData": {"mimeType": b["source"]["media_type"], "data": b["source"]["data"]}})
        if parts:
            contents.append({"role": role, "parts": parts})
    return contents


def ask(messages, system: str, tier: str = "default", max_tokens: int | None = None) -> dict:
    """Send a conversation to Gemini. Returns {"text": ..., "truncated": bool}."""
    if not config.API_KEY:
        raise LLMError("no_key", "GEMINI_API_KEY is missing from .env.", 500)
    model = config.QUICK_MODEL if tier == "quick" else config.MODEL
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": to_gemini(messages),
        "generationConfig": {"maxOutputTokens": max_tokens or config.MAX_TOKENS},
    }
    if config.THINKING:
        body["generationConfig"]["thinkingConfig"] = {"thinkingLevel": config.THINKING}
    req = urllib.request.Request(API_URL.format(model=model), data=json.dumps(body).encode(), method="POST", headers={
        "x-goog-api-key": config.API_KEY,
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            data = json.loads(res.read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get("error", {})
        except Exception:
            err = {}
        msg, status = err.get("message", ""), err.get("status", "")
        low = msg.lower()
        if "api key" in low or status == "UNAUTHENTICATED" or e.code == 401:
            raise LLMError("bad_key", msg or "The API key was not accepted.", 502)
        if "billing" in low or "credit" in low or "prepay" in low:
            raise LLMError("no_credit", msg or "Billing is not set up for this key.", 402)
        if e.code == 404 or status == "NOT_FOUND":
            raise LLMError("bad_model", msg or f"Model {model} was not found.", 502)
        if e.code == 403 or status == "PERMISSION_DENIED":
            raise LLMError("bad_key", msg or "This API key is not allowed to do that.", 502)
        if e.code in (429, 503) or status in ("RESOURCE_EXHAUSTED", "UNAVAILABLE"):
            raise LLMError("rate_limited", msg or "Gemini is busy or the quota ran out.", 429)
        raise LLMError("upstream_error", msg or f"Gemini returned error {e.code}.")
    except (urllib.error.URLError, TimeoutError) as e:
        raise LLMError("no_internet", f"Could not reach Gemini ({getattr(e, 'reason', e)}).")

    if (data.get("promptFeedback") or {}).get("blockReason"):
        raise LLMError("refused", "That one could not be answered.", 200)
    cand = (data.get("candidates") or [{}])[0]
    finish = cand.get("finishReason", "")
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    if not text.strip():
        if finish in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "RECITATION", "SPII"):
            raise LLMError("refused", "That one could not be answered.", 200)
        raise LLMError("empty_completion", "Gemini sent an empty reply.")
    return {"text": text, "truncated": finish == "MAX_TOKENS"}
