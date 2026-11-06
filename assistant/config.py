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

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")
QUICK_MODEL = os.environ.get("QUICK_MODEL", "claude-haiku-5-5")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4000"))
PER_STUDENT_PER_HOUR = int(os.environ.get("PER_STUDENT_PER_HOUR", "40"))
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))
# Other websites allowed to call /api/claude. The app's own site is always allowed.
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

APP_DIR = ROOT / "public"
DATA_DIR = ROOT / "data"
STUDENTS_DIR = ROOT / "students"
