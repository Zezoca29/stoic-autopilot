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
