import pytest

from factories import make_quotes
from generator.quotes import check_quotes, display_reference, load_quotes
from shared.jsonio import write_json


def test_valid_bank_loads_by_id(tmp_path):
    path = tmp_path / "quotes.json"
    write_json(path, make_quotes(3))
    assert sorted(load_quotes(path)) == ["q1", "q2", "q3"]


def test_missing_field_and_bad_url():
    data = make_quotes(2)
    data[0]["reference"] = " "
    data[1]["source_url"] = "http://example.com"
    errors = check_quotes(data)
    assert "q1: missing reference" in errors
    assert "q2: source_url must be an https URL" in errors


def test_duplicate_id():
    data = make_quotes(2)
    data[1]["id"] = "q1"
    assert "q1: duplicate id" in check_quotes(data)


def test_invalid_bank_raises(tmp_path):
    path = tmp_path / "quotes.json"
    write_json(path, [{"id": "x"}])
    with pytest.raises(ValueError, match="x: missing author"):
        load_quotes(path)


def test_display_reference():
    assert display_reference(make_quotes(1)[0]) == "Sêneca, Cartas a Lucílio 1.1"
