"""Render carousel slides from an HTML template to 1080x1350 JPEGs (the only image format the Instagram API accepts)."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from generator.quotes import display_reference
from shared.config import ROOT

TEMPLATES_DIR = ROOT / "generator" / "templates"
SLIDE_WIDTH, SLIDE_HEIGHT = 1080, 1350
JPEG_QUALITY = 92

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))


def render_html(slide: dict, index: int, total: int, handle: str, quotes: dict) -> str:
    quote = quotes.get(slide["quote_id"]) if slide.get("quote_id") else None
    return _env.get_template("carousel.html").render(
        slide=slide, index=index, total=total, handle=handle, is_cover=index == 1,
        reference=display_reference(quote) if quote else None)


def render_carousel(item: dict, quotes: dict, out_dir: Path, handle: str) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(item["slides"])
    paths = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT})
            for index, slide in enumerate(item["slides"], start=1):
                page.set_content(render_html(slide, index, total, handle, quotes), wait_until="networkidle")
                path = out_dir / f"slide-{index:02d}.jpg"
                page.screenshot(path=str(path), type="jpeg", quality=JPEG_QUALITY)
                paths.append(path)
        finally:
            browser.close()
    return paths
