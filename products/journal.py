"""Shared builder for the printable stoic journals (free 7-day and paid 30-day editions).

Each edition has a content.json; quotes are always taken verbatim from the verified bank.
"""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from generator.quotes import display_reference, load_quotes
from shared.jsonio import read_json

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
HANDLE = "@fortalezainterior.br"
LINK = "zezoca29.github.io/stoic-autopilot"

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))


def load_days(quotes: dict, content_path: Path) -> list[dict]:
    """Days with the quote text taken verbatim from the verified bank (a missing id raises KeyError)."""
    days = []
    for day in read_json(content_path)["days"]:
        quote = quotes[day["quote_id"]]
        days.append({**day, "quote": quote["text_pt"], "reference": display_reference(quote)})
    return days


def render_html(days: list[dict], content_path: Path) -> str:
    content = read_json(content_path)
    by_number = {day["day"]: day for day in days}
    sections = [{**section, "days": [by_number[number] for number in section["day_numbers"]]}
                for section in content.get("sections", [])]
    return _env.get_template("journal.html").render(
        content=content, days=days, sections=sections, total=len(days), handle=HANDLE, link=LINK)


def build(content_path: Path, out_path: Path) -> Path:
    html = render_html(load_days(load_quotes(), content_path), content_path)
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
