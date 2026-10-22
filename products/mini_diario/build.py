"""Build the free 7-day stoic journal PDF: `python -m products.mini_diario.build`."""
import sys
from pathlib import Path

from products import journal

HERE = Path(__file__).resolve().parent
CONTENT_PATH = HERE / "content.json"
OUT_PATH = HERE.parent.parent / "site" / "mini-diario-estoico-7-dias.pdf"  # served as a free download on the bio page


def load_days(quotes: dict, path: Path = CONTENT_PATH) -> list[dict]:
    return journal.load_days(quotes, path)


def render_html(days: list[dict], path: Path = CONTENT_PATH) -> str:
    return journal.render_html(days, path)


def main() -> int:
    print(f"OK: {journal.build(CONTENT_PATH, OUT_PATH)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
