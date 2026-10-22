"""Build the free 7-day stoic journal PDF: `python -m products.mini_diario.build`."""
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from generator.quotes import display_reference, load_quotes
from shared.jsonio import read_json

HERE = Path(__file__).resolve().parent
CONTENT_PATH = HERE / "content.json"
OUT_PATH = HERE / "dist" / "mini-diario-estoico-7-dias.pdf"
HANDLE = "@fortalezainterior.br"
LINK = "zezoca29.github.io/stoic-autopilot"

_env = Environment(loader=FileSystemLoader(HERE), autoescape=select_autoescape(["html"]))


def load_days(quotes: dict, path: Path = CONTENT_PATH) -> list[dict]:
    """Days with the quote text taken verbatim from the verified bank (a missing id raises KeyError)."""
    days = []
    for day in read_json(path)["days"]:
        quote = quotes[day["quote_id"]]
        days.append({**day, "quote": quote["text_pt"], "reference": display_reference(quote)})
    return days


def render_html(days: list[dict], path: Path = CONTENT_PATH) -> str:
    content = read_json(path)
    return _env.get_template("template.html").render(
        title=content["title"], subtitle=content["subtitle"], how_to=content["how_to"], days=days,
        closing=content["closing"], sources_note=content["sources_note"], disclaimer=content["disclaimer"],
        handle=HANDLE, link=LINK)


def build(out_path: Path = OUT_PATH) -> Path:
    html = render_html(load_days(load_quotes()))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(path=str(out_path), format="A4", print_background=True,
                     margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        finally:
            browser.close()
    return out_path


def main() -> int:
    print(f"OK: {build()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
