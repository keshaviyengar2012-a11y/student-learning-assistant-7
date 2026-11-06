"""Settings, read from the .env file (or real environment variables)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(ROOT / ".env")

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
MODEL = os.environ.get("MODEL", "gemini-3.8-flash")
QUICK_MODEL = os.environ.get("QUICK_MODEL", "gemini-3.5-flash-lite")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "8192"))
# How much Gemini thinks before answering: minimal, low, medium or high. Low keeps replies quick.
THINKING = os.environ.get("THINKING", "low")
PER_STUDENT_PER_HOUR = int(os.environ.get("PER_STUDENT_PER_HOUR", "40"))
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
# Other websites allowed to call /api/tutor. The app's own site is always allowed.
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

APP_DIR = ROOT / "public"
DATA_DIR = ROOT / "data"
STUDENTS_DIR = ROOT / "students"
