"""Build the paid 30-day stoic journal PDF: `python -m products.diario_30.build`.

content.json is kept out of git on purpose: the repository is public and this is a paid product.
"""
import sys
from pathlib import Path

from products import journal

HERE = Path(__file__).resolve().parent
CONTENT_PATH = HERE / "content.json"
OUT_PATH = HERE / "dist" / "diario-estoico-30-dias.pdf"


def load_days(quotes: dict, path: Path = CONTENT_PATH) -> list[dict]:
    return journal.load_days(quotes, path)


def render_html(days: list[dict], path: Path = CONTENT_PATH) -> str:
    return journal.render_html(days, path)


def main() -> int:
    print(f"OK: {journal.build(CONTENT_PATH, OUT_PATH)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
