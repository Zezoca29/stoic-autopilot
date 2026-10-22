import pytest

from generator.quotes import load_quotes
from products.diario_30.build import CONTENT_PATH, load_days, render_html

pytestmark = pytest.mark.skipif(not CONTENT_PATH.exists(), reason="paid journal content lives only on the author's PC")


def test_thirty_days_with_distinct_verified_quotes():
    days = load_days(load_quotes())
    assert [day["day"] for day in days] == list(range(1, 31))
    assert len({day["quote_id"] for day in days}) == 30
    assert all(day["quote"] and day["reference"] and len(day["prompts"]) == 3 for day in days)


def test_html_has_sections_reviews_and_every_day_once():
    html = render_html(load_days(load_quotes()))
    assert html.count('class="page day"') == 30
    assert html.count('class="page section"') == 5
    assert html.count('class="page review"') == 5
    assert "Dia 30 de 30" in html and "Diário Estoico" in html
