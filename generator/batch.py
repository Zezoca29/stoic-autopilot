"""Load and structurally check a weekly content batch written by the Claude routine."""
from pathlib import Path

from shared.jsonio import read_json
from shared.timeutil import parse_time

PILLARS = {"controle", "adversidade", "disciplina", "emocoes", "memento_mori"}
PLATFORMS = {"instagram", "tiktok"}
CTAS = {"follow", "save", "affiliate", "freebie"}  # freebie: points to the free journal on the bio page
REQUIRED_FIELDS = {
    "reel": {"id", "type", "scheduled_at", "pillar", "hook", "quote_id", "script",
             "footage_keywords", "caption", "hashtags", "cta", "platforms"},
    "carousel": {"id", "type", "scheduled_at", "pillar", "slides", "quote_ids",
                 "caption", "hashtags", "platforms"},
}


class BatchError(ValueError):
    """The batch file is malformed and cannot be rendered."""


def load_batch(path: Path) -> dict:
    data = read_json(path)
    errors = check_structure(data)
    if errors:
        raise BatchError("; ".join(errors))
    return data


def check_structure(data) -> list[str]:
    if not isinstance(data, dict):
        return ["batch must be a JSON object"]
    errors = []
    if not isinstance(data.get("week"), str) or not data["week"]:
        errors.append("week must be a non-empty string")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["items must be a non-empty list"]
    seen = set()
    for index, item in enumerate(items):
        errors.extend(_check_item(item, index, seen))
    return errors


def _check_item(item, index, seen) -> list[str]:
    if not isinstance(item, dict):
        return [f"items[{index}]: must be an object"]
    label = item.get("id") or f"items[{index}]"
    required = REQUIRED_FIELDS.get(item.get("type"))
    if required is None:
        return [f"{label}: unknown type {item.get('type')!r}"]
    errors = []
    missing = sorted(required - item.keys())
    if missing:
        errors.append(f"{label}: missing fields {missing}")
    if label in seen:
        errors.append(f"{label}: duplicate id")
    seen.add(label)
    if item.get("pillar") not in PILLARS:
        errors.append(f"{label}: pillar must be one of {sorted(PILLARS)}")
    try:
        parse_time(item.get("scheduled_at"))
    except (TypeError, ValueError):
        errors.append(f"{label}: scheduled_at must be ISO 8601 with UTC offset")
    platforms = item.get("platforms")
    if not isinstance(platforms, list) or not platforms or not set(platforms) <= PLATFORMS:
        errors.append(f"{label}: platforms must be a non-empty subset of {sorted(PLATFORMS)}")
    elif "instagram" not in platforms:
        errors.append(f"{label}: instagram is required")
    elif item["type"] == "carousel" and platforms != ["instagram"]:
        errors.append(f"{label}: carousels are Instagram-only")
    if item["type"] == "reel" and item.get("cta") not in CTAS:
        errors.append(f"{label}: cta must be one of {sorted(CTAS)}")
    return errors


def quote_ids_of(item: dict) -> list[str]:
    return [item["quote_id"]] if item["type"] == "reel" else list(item["quote_ids"])
