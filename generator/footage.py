"""Background footage from the Pexels API, with a local fallback clip."""
import shutil
from pathlib import Path

import requests

from shared.config import ROOT

SEARCH_URL = "https://api.pexels.com/videos/search"
MIN_CLIP_SECONDS = 8
TARGET_HEIGHT = 1920
FALLBACK_VIDEO = ROOT / "generator" / "assets" / "fallback.mp4"
FALLBACK_KEYWORDS = {
    "controle": ["calm ocean", "mountain fog"],
    "adversidade": ["storm waves", "rain window"],
    "disciplina": ["running sunrise", "ancient columns"],
    "emocoes": ["candle flame", "clouds timelapse"],
    "memento_mori": ["marble statue", "hourglass"],
}


class FootageError(RuntimeError):
    """No usable background video could be obtained."""


def choose_file(video: dict) -> dict | None:
    portrait = [f for f in video.get("video_files", [])
                if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")
                and f["height"] > f["width"]]
    return min(portrait, key=lambda f: abs(f["height"] - TARGET_HEIGHT), default=None)


def search(keyword: str, api_key: str, session) -> list[dict]:
    response = session.get(SEARCH_URL, params={"query": keyword, "orientation": "portrait", "per_page": 15},
                           headers={"Authorization": api_key}, timeout=30)
    response.raise_for_status()
    return response.json().get("videos", [])


def pick_video(keywords, pillar, exclude_ids, api_key, session) -> tuple[str, str]:
    for keyword in [*keywords, *FALLBACK_KEYWORDS[pillar]]:
        for video in search(keyword, api_key, session):
            footage_id = f"pexels:{video['id']}"
            if footage_id in exclude_ids or video.get("duration", 0) < MIN_CLIP_SECONDS:
                continue
            chosen = choose_file(video)
            if chosen:
                return footage_id, chosen["link"]
    raise FootageError(f"no portrait Pexels video for {keywords} or pillar {pillar}")


def download(url: str, out_path: Path, session) -> None:
    with session.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(out_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1 << 20):
                file.write(chunk)


def fetch_footage(keywords, pillar, exclude_ids, out_path, api_key, session=None) -> str:
    """Save a background clip to out_path; returns 'pexels:<id>' or 'fallback'."""
    session = session or requests.Session()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        footage_id, url = pick_video(keywords, pillar, exclude_ids, api_key, session)
        download(url, out_path, session)
        return footage_id
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status in (401, 403):  # a bad key would otherwise silently give every reel the fallback clip
            raise FootageError(f"Pexels rejected the API key (HTTP {status}); check PEXELS_API_KEY") from None
        return _use_fallback(out_path)
    except (FootageError, requests.RequestException):
        return _use_fallback(out_path)


def _use_fallback(out_path: Path) -> str:
    if not FALLBACK_VIDEO.exists():
        raise FootageError(f"Pexels unavailable and {FALLBACK_VIDEO} is missing")
    shutil.copyfile(FALLBACK_VIDEO, out_path)
    return "fallback"
