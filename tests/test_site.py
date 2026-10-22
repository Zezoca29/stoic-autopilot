import re

from shared.config import ROOT

SITE = ROOT / "site"


def test_index_links_policies_and_books():
    index = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'href="privacy.html"' in index and 'href="terms.html"' in index
    assert "amazon.com.br" in index


def test_policy_pages_are_complete():
    for page in ("privacy.html", "terms.html"):
        html = (SITE / page).read_text(encoding="utf-8")
        assert html.lower().startswith("<!doctype html>")
        assert "CONTATO@EXEMPLO.COM" not in html
        assert "mailto:" in html


def test_book_links_carry_affiliate_tag_and_disclosure():
    index = (SITE / "index.html").read_text(encoding="utf-8")
    book_links = [line for line in index.splitlines() if 'class="book"' in line]
    assert len(book_links) == 6
    assert all(re.search(r'href="https://www\.amazon\.com\.br/dp/[0-9A-Z]{10}\?tag=fortalezain08-20"', line)
               for line in book_links)
    assert "Como Associado da Amazon, recebo por compras qualificadas." in index
