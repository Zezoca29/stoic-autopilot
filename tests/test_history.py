from datetime import date

from generator.history import load_history, quote_on_cooldown, recent_footage, record_use


def empty():
    return {"quotes": {}, "footage": {}}


def test_missing_history_is_empty(tmp_path):
    assert load_history(tmp_path / "none.json") == empty()


def test_quote_cooldown_is_60_days():
    history = empty()
    record_use(history, item_id="a", quote_ids=["q1"], footage_ids=[], on=date(2026, 10, 1))
    assert quote_on_cooldown(history, "q1", date(2026, 11, 29), "b")      # 59 days later
    assert not quote_on_cooldown(history, "q1", date(2026, 11, 30), "b")  # 60 days later
    assert not quote_on_cooldown(history, "q2", date(2026, 10, 2), "b")


def test_same_item_can_reuse_its_quote():
    history = empty()
    record_use(history, item_id="a", quote_ids=["q1"], footage_ids=[], on=date(2026, 10, 1))
    assert not quote_on_cooldown(history, "q1", date(2026, 10, 1), "a")


def test_recent_footage_window():
    history = empty()
    record_use(history, item_id="a", quote_ids=[], footage_ids=["pexels:1"], on=date(2026, 10, 1))
    record_use(history, item_id="b", quote_ids=[], footage_ids=["pexels:2"], on=date(2026, 10, 10))
    assert recent_footage(history, date(2026, 10, 7)) == {"pexels:1", "pexels:2"}
    assert recent_footage(history, date(2026, 10, 8)) == {"pexels:2"}
