"""Usage history that keeps quotes and background footage from repeating too soon."""
from datetime import date
from pathlib import Path

from shared.config import ROOT
from shared.jsonio import read_json, write_json

HISTORY_PATH = ROOT / "content" / "history.json"
QUOTE_COOLDOWN_DAYS = 60
FOOTAGE_COOLDOWN_DAYS = 7


def load_history(path: Path = HISTORY_PATH) -> dict:
    if not Path(path).exists():
        return {"quotes": {}, "footage": {}}
    return read_json(path)


def save_history(path: Path, history: dict) -> None:
    write_json(path, history)


def _within(used_on: str, on: date, days: int) -> bool:
    return abs((on - date.fromisoformat(used_on)).days) < days


def quote_on_cooldown(history: dict, quote_id: str, on: date, item_id: str) -> bool:
    use = history["quotes"].get(quote_id)
    return use is not None and use["item"] != item_id and _within(use["on"], on, QUOTE_COOLDOWN_DAYS)


def recent_footage(history: dict, on: date) -> set[str]:
    return {footage_id for footage_id, use in history["footage"].items()
            if _within(use["on"], on, FOOTAGE_COOLDOWN_DAYS)}


def record_use(history: dict, *, item_id: str, quote_ids: list[str], footage_ids: list[str], on: date) -> None:
    for quote_id in quote_ids:
        history["quotes"][quote_id] = {"on": on.isoformat(), "item": item_id}
    for footage_id in footage_ids:
        history["footage"][footage_id] = {"on": on.isoformat(), "item": item_id}
