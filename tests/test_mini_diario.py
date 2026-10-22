from generator.quotes import load_quotes
from products.mini_diario.build import load_days, render_html


def test_seven_days_use_verified_quotes_with_reference():
    days = load_days(load_quotes())
    assert [day["day"] for day in days] == list(range(1, 8))
    assert all(day["quote"] and day["reference"] for day in days)
    assert all(len(day["prompts"]) == 3 for day in days)


def test_html_has_cover_how_to_seven_days_and_closing():
    html = render_html(load_days(load_quotes()))
    assert html.count('class="page day"') == 7
    assert 'class="page cover"' in html and 'class="page closing"' in html
    assert "Mini Diário Estoico" in html and "@fortalezainterior.br" in html
    assert "Marco Aurélio, Meditações 4.7" in html
