"""The one place that talks to Claude. Uses only the Python standard library."""
import json
import urllib.error
import urllib.request

from . import config

API_URL = "https://api.anthropic.com/v1/messages"


class LLMError(Exception):
    """A failure the app knows how to explain. `code` matches the app's messages."""

    def __init__(self, code: str, message: str, status: int = 502):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def ask(messages, system: str, tier: str = "default", max_tokens: int | None = None) -> dict:
    """Send a conversation to Claude. Returns {"text": ..., "truncated": bool}."""
    if not config.API_KEY:
        raise LLMError("sampling_disabled", "ANTHROPIC_API_KEY is missing from .env.", 500)
    model = config.QUICK_MODEL if tier == "quick" else config.MODEL
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens or config.MAX_TOKENS,
        "system": system,
        "messages": messages,
    }).encode()
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "x-api-key": config.API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as res:
            data = json.loads(res.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        if e.code in (429, 529):
            raise LLMError("rate_limited", msg or "Claude is busy.", 429)
        if e.code in (401, 403):
            raise LLMError("sampling_disabled", msg or "The API key was not accepted.", 502)
        raise LLMError("upstream_error", msg or f"Claude returned error {e.code}.")
    except (urllib.error.URLError, TimeoutError):
        raise LLMError("upstream_error", "Could not reach Claude.")

    if data.get("stop_reason") == "refusal":
        raise LLMError("refused", "That one could not be answered.", 200)
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    if not text.strip():
        raise LLMError("empty_completion", "Claude sent an empty reply.")
    return {"text": text, "truncated": data.get("stop_reason") == "max_tokens"}
