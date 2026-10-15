"""Verified quote bank: the only source of quotes the pipeline may publish."""
import sys
from pathlib import Path

from shared.config import ROOT
from shared.jsonio import read_json

QUOTES_PATH = ROOT / "content" / "quotes.json"
QUOTE_FIELDS = ("id", "author", "work", "reference", "text_pt", "text_source", "source_url")


def check_quotes(data) -> list[str]:
    if not isinstance(data, list):
        return ["quotes.json must be a JSON list"]
    errors, seen = [], set()
    for index, quote in enumerate(data):
        label = quote.get("id") or f"quotes[{index}]"
        for field in QUOTE_FIELDS:
            value = quote.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: missing {field}")
        if not str(quote.get("source_url", "")).startswith("https://"):
            errors.append(f"{label}: source_url must be an https URL")
        if label in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(label)
    return errors


def load_quotes(path: Path = QUOTES_PATH) -> dict[str, dict]:
    data = read_json(path)
    errors = check_quotes(data)
    if errors:
        raise ValueError("; ".join(errors))
    return {quote["id"]: quote for quote in data}


def display_reference(quote: dict) -> str:
    return f"{quote['author']}, {quote['work']} {quote['reference']}"


def main() -> int:
    data = read_json(QUOTES_PATH)
    errors = check_quotes(data)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"{len(data)} quotes, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
