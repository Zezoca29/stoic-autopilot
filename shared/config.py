"""Runtime configuration: constants plus settings from .env locally or GitHub Secrets in CI."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
TIMEZONE = "America/Sao_Paulo"
VOICE = "pt-BR-AntonioNeural"


@dataclass(frozen=True)
class Settings:
    pixabay_api_key: str | None
    ig_user_id: str | None
    ig_access_token: str | None
    pages_base_url: str | None
    handle: str


def load_settings(env_file: Path | None = ROOT / ".env") -> Settings:
    if env_file is not None and Path(env_file).exists():
        load_dotenv(env_file, override=False)
    return Settings(
        pixabay_api_key=os.getenv("PIXABAY_API_KEY") or None,
        ig_user_id=os.getenv("IG_USER_ID") or None,
        ig_access_token=os.getenv("IG_ACCESS_TOKEN") or None,
        pages_base_url=(os.getenv("PAGES_BASE_URL") or "").rstrip("/") or None,
        handle=os.getenv("IG_HANDLE", ""),
    )


def require(value: str | None, name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required setting {name}; set it in .env or GitHub Secrets")
    return value
