"""Background footage from the Pixabay video API, with a local fallback clip."""
import shutil
from pathlib import Path

import requests

from shared.config import ROOT

SEARCH_URL = "https://pixabay.com/api/videos/"
MIN_CLIP_SECONDS = 8
MIN_HEIGHT = 720  # ffmpeg crops the landscape frame to 9:16, so smaller sources look blurry
MAX_DOWNLOAD_BYTES = 80 * 1024 * 1024
RENDITION_PREFERENCE = ("large", "medium", "small")
FALLBACK_VIDEO = ROOT / "generator" / "assets" / "fallback.mp4"
FALLBACK_KEYWORDS = {
    "controle": ["calm ocean", "mountain fog"],
    "adversidade": ["storm waves", "rain window"],
    "disciplina": ["running sunrise", "ancient columns"],
    "emocoes": ["candle flame", "clouds timelapse"],
    "memento_mori": ["marble statue", "hourglass"],
}
KEY_REJECTED_STATUSES = (400, 401, 403)  # Pixabay answers an invalid key with 400


class FootageError(RuntimeError):
    """No usable background video could be obtained."""


def choose_file(video: dict) -> dict | None:
    renditions = video.get("videos", {})
    for name in RENDITION_PREFERENCE:
        rendition = renditions.get(name) or {}
        if (rendition.get("url") and rendition.get("height", 0) >= MIN_HEIGHT
                and rendition.get("size", 0) <= MAX_DOWNLOAD_BYTES):
            return rendition
    return None


def search(keyword: str, api_key: str, session) -> list[dict]:
    response = session.get(SEARCH_URL, params={"key": api_key, "q": keyword, "video_type": "film",
                                               "safesearch": "true", "per_page": 20}, timeout=30)
    response.raise_for_status()
    return response.json().get("hits", [])


def pick_video(keywords, pillar, exclude_ids, api_key, session) -> tuple[str, str]:
    for keyword in [*keywords, *FALLBACK_KEYWORDS[pillar]]:
        for video in search(keyword, api_key, session):
            footage_id = f"pixabay:{video['id']}"
            if footage_id in exclude_ids or video.get("duration", 0) < MIN_CLIP_SECONDS:
                continue
            chosen = choose_file(video)
            if chosen:
                return footage_id, chosen["url"]
    raise FootageError(f"no usable Pixabay video for {keywords} or pillar {pillar}")


def download(url: str, out_path: Path, session) -> None:
    with session.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(out_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1 << 20):
                file.write(chunk)


def fetch_footage(keywords, pillar, exclude_ids, out_path, api_key, session=None) -> str:
    """Save a background clip to out_path; returns 'pixabay:<id>' or 'fallback'."""
    session = session or requests.Session()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        footage_id, url = pick_video(keywords, pillar, exclude_ids, api_key, session)
        download(url, out_path, session)
        return footage_id
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in KEY_REJECTED_STATUSES:  # a bad key would otherwise silently give every reel the fallback clip
            # the request URL carries the key, so the original message is deliberately not included
            raise FootageError(f"Pixabay rejected the request (HTTP {status}); check PIXABAY_API_KEY") from None
        return _use_fallback(out_path)
    except (FootageError, requests.RequestException):
        return _use_fallback(out_path)


def _use_fallback(out_path: Path) -> str:
    if not FALLBACK_VIDEO.exists():
        raise FootageError(f"Pixabay unavailable and {FALLBACK_VIDEO} is missing")
    shutil.copyfile(FALLBACK_VIDEO, out_path)
    return "fallback"
