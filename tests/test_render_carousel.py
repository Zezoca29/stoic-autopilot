from PIL import Image

from factories import NOW, make_carousel
from generator.render_carousel import render_carousel, render_html


def test_render_html_escapes_text_and_shows_reference(quotes):
    html = render_html({"title": "<b>Tempo</b>", "body": "Corpo", "quote_id": "q1"}, 2, 6, "@estoico", quotes)
    assert "&lt;b&gt;Tempo&lt;/b&gt;" in html
    assert "Sêneca, Cartas a Lucílio 1.1" in html
    assert "2/6" in html and "@estoico" in html


def test_cover_uses_bigger_title(quotes):
    assert "font-size:96px" in render_html({"title": "Capa"}, 1, 6, "", quotes)
    assert "font-size:72px" in render_html({"title": "Miolo"}, 2, 6, "", quotes)


def test_render_carousel_writes_jpeg_slides(tmp_path, quotes):
    paths = render_carousel(make_carousel(1, NOW), quotes, tmp_path, "@estoico")
    assert [p.name for p in paths] == [f"slide-{n:02d}.jpg" for n in range(1, 7)]
    with Image.open(paths[0]) as image:
        assert image.format == "JPEG" and image.size == (1080, 1350)


def test_slides_carry_brand_label_and_quote_ornament(quotes):
    quote_slide = render_html({"title": "T", "body": "B", "quote_id": "q1"}, 2, 6, "@estoico", quotes)
    plain_slide = render_html({"title": "T", "body": "B"}, 2, 6, "@estoico", quotes)
    assert 'class="brand"' in quote_slide and "Fortaleza Interior" in quote_slide
    assert 'class="ornament"' in quote_slide
    assert 'class="ornament"' not in plain_slide
