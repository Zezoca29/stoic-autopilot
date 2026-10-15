"""Batch rules: check_plan runs before rendering (cheap), check_media after (output specs)."""
from datetime import datetime
from pathlib import Path

from PIL import Image

from generator.batch import quote_ids_of
from generator.history import QUOTE_COOLDOWN_DAYS, quote_on_cooldown
from generator.media_probe import probe as ffprobe
from shared.post_queue import compose_caption
from shared.timeutil import parse_time

REELS_PER_BATCH = 7
CAROUSELS_PER_BATCH = 3
SCRIPT_MIN_WORDS, SCRIPT_MAX_WORDS = 80, 145
SLIDES_MIN, SLIDES_MAX = 6, 8
CAPTION_MAX_CHARS = 2200
HASHTAGS_MAX = 30
REEL_SIZE = (1080, 1920)
SLIDE_SIZE = (1080, 1350)
REEL_MIN_SECONDS, REEL_MAX_SECONDS = 30.0, 60.0
REEL_MAX_BYTES = 100 * 1024 * 1024


def check_plan(batch: dict, quotes: dict, history: dict, now: datetime) -> list[str]:
    items = batch["items"]
    errors = []
    reels = sum(1 for item in items if item["type"] == "reel")
    carousels = sum(1 for item in items if item["type"] == "carousel")
    if reels != REELS_PER_BATCH:
        errors.append(f"batch must have {REELS_PER_BATCH} reels, found {reels}")
    if carousels != CAROUSELS_PER_BATCH:
        errors.append(f"batch must have {CAROUSELS_PER_BATCH} carousels, found {carousels}")
    used_quotes, hooks = {}, {}
    for item in items:
        errors.extend(_check_item(item, quotes, history, now, used_quotes, hooks))
    return errors


def _check_item(item, quotes, history, now, used_quotes, hooks) -> list[str]:
    label = item["id"]
    errors = []
    when = parse_time(item["scheduled_at"])
    if when <= now:
        errors.append(f"{label}: scheduled_at is in the past")
    for quote_id in quote_ids_of(item):
        if quote_id not in quotes:
            errors.append(f"{label}: quote {quote_id} is not in content/quotes.json")
        elif quote_on_cooldown(history, quote_id, when.date(), label):
            errors.append(f"{label}: quote {quote_id} was used less than {QUOTE_COOLDOWN_DAYS} days ago")
        if quote_id in used_quotes:
            errors.append(f"{label}: quote {quote_id} already used by {used_quotes[quote_id]} in this batch")
        used_quotes.setdefault(quote_id, label)
    caption = compose_caption(item)
    if len(caption) > CAPTION_MAX_CHARS:
        errors.append(f"{label}: caption has {len(caption)} chars (max {CAPTION_MAX_CHARS})")
    tags = item["hashtags"]
    if len(tags) > HASHTAGS_MAX or any(not tag.startswith("#") or " " in tag for tag in tags):
        errors.append(f"{label}: hashtags must be at most {HASHTAGS_MAX} single words starting with #")
    if item["type"] == "reel":
        words = len(item["script"].split())
        if not SCRIPT_MIN_WORDS <= words <= SCRIPT_MAX_WORDS:
            errors.append(f"{label}: script has {words} words (expected {SCRIPT_MIN_WORDS}-{SCRIPT_MAX_WORDS})")
        hook = item["hook"].strip().lower()
        if hook in hooks:
            errors.append(f"{label}: hook repeats {hooks[hook]}")
        hooks.setdefault(hook, label)
    else:
        slides = item["slides"]
        if not SLIDES_MIN <= len(slides) <= SLIDES_MAX:
            errors.append(f"{label}: carousel has {len(slides)} slides (expected {SLIDES_MIN}-{SLIDES_MAX})")
        for number, slide in enumerate(slides, start=1):
            if not str(slide.get("title", "")).strip():
                errors.append(f"{label}: slide {number} has no title")
            if slide.get("quote_id") and slide["quote_id"] not in item["quote_ids"]:
                errors.append(f"{label}: slide {number} quote_id must be listed in quote_ids")
    return errors


def check_media(batch: dict, output_dir: Path, probe=ffprobe) -> list[str]:
    errors = []
    for item in batch["items"]:
        item_dir = Path(output_dir) / item["id"]
        if item["type"] == "reel":
            errors.extend(_check_reel(item["id"], item_dir / "reel.mp4", probe))
        else:
            errors.extend(_check_slides(item["id"], item_dir, len(item["slides"])))
    return errors


def _check_reel(label, path, probe) -> list[str]:
    if not path.exists():
        return [f"{label}: {path.name} was not rendered"]
    info = probe(path)
    errors = []
    if (info.width, info.height) != REEL_SIZE:
        errors.append(f"{label}: reel is {info.width}x{info.height}, expected 1080x1920")
    if not REEL_MIN_SECONDS <= info.duration <= REEL_MAX_SECONDS:
        errors.append(f"{label}: reel lasts {info.duration:.1f}s, expected 30-60s (adjust script length)")
    if info.size_bytes > REEL_MAX_BYTES:
        errors.append(f"{label}: reel has {info.size_bytes // (1024 * 1024)} MB (max 100 MB)")
    return errors


def _check_slides(label, item_dir, expected) -> list[str]:
    paths = sorted(item_dir.glob("slide-*.jpg"))
    if len(paths) != expected:
        return [f"{label}: expected {expected} slides, found {len(paths)}"]
    errors = []
    for path in paths:
        with Image.open(path) as image:
            if image.format != "JPEG" or image.size != SLIDE_SIZE:
                errors.append(f"{label}: {path.name} must be a 1080x1350 JPEG")
    return errors
