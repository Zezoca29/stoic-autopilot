import json

import pytest

from generator.batch import BatchError, check_structure, load_batch, quote_ids_of


def test_valid_week_has_no_errors(week):
    assert check_structure(week) == []


def test_load_batch_reports_missing_fields(tmp_path, week):
    del week["items"][0]["script"]
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(week), encoding="utf-8")
    with pytest.raises(BatchError, match=r"2026-10-19-r1: missing fields \['script'\]"):
        load_batch(path)


def test_unknown_type_and_duplicate_id(week):
    week["items"][1]["type"] = "story"
    week["items"][2]["id"] = week["items"][0]["id"]
    errors = check_structure(week)
    assert "2026-10-19-r2: unknown type 'story'" in errors
    assert "2026-10-19-r1: duplicate id" in errors


def test_scheduled_at_needs_offset(week):
    week["items"][0]["scheduled_at"] = "2026-10-19T12:00:00"
    assert "2026-10-19-r1: scheduled_at must be ISO 8601 with UTC offset" in check_structure(week)


def test_platform_rules(week):
    week["items"][0]["platforms"] = ["tiktok"]
    week["items"][7]["platforms"] = ["instagram", "tiktok"]
    errors = check_structure(week)
    assert "2026-10-19-r1: instagram is required" in errors
    assert "2026-10-19-c1: carousels are Instagram-only" in errors


def test_bad_pillar_and_cta(week):
    week["items"][0]["pillar"] = "felicidade"
    week["items"][1]["cta"] = "buy"
    errors = check_structure(week)
    assert any(e.startswith("2026-10-19-r1: pillar must be one of") for e in errors)
    assert any(e.startswith("2026-10-19-r2: cta must be one of") for e in errors)


def test_empty_items_rejected():
    assert check_structure({"week": "x", "items": []}) == ["items must be a non-empty list"]


def test_quote_ids_of(week):
    assert quote_ids_of(week["items"][0]) == ["q1"]
    assert quote_ids_of(week["items"][7]) == ["q11"]
