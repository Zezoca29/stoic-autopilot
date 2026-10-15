from datetime import timedelta

from factories import NOW, make_reel
from generator.schedule import next_slots
from shared.post_queue import make_entry


def entry_at(when):
    return make_entry(make_reel(1, when), ["reel.mp4"])


def test_empty_queue_starts_today_at_noon():
    slots = next_slots([], NOW)
    assert slots["skip"] is False
    assert slots["batch"] == "2026-10-19"
    assert slots["reels"][0] == "2026-10-19T12:00:00-03:00"
    assert slots["reels"][-1] == "2026-10-25T12:00:00-03:00"
    assert slots["carousels"] == ["2026-10-20T19:00:00-03:00", "2026-10-22T19:00:00-03:00",
                                  "2026-10-24T19:00:00-03:00"]


def test_after_noon_starts_tomorrow():
    assert next_slots([], NOW.replace(hour=13))["reels"][0] == "2026-10-20T12:00:00-03:00"


def test_continues_after_last_queued_item():
    queue = [entry_at(NOW.replace(hour=13))]  # Monday 13:00 still queued
    assert next_slots(queue, NOW)["reels"][0] == "2026-10-20T12:00:00-03:00"


def test_late_run_never_schedules_in_the_past():
    tuesday_10am = NOW + timedelta(days=1, hours=2)
    assert next_slots([entry_at(NOW - timedelta(days=1))], tuesday_10am)["reels"][0] == "2026-10-20T12:00:00-03:00"


def test_skips_when_queue_is_already_full():
    slots = next_slots([entry_at(NOW + timedelta(days=3))], NOW)
    assert slots["skip"] is True
    assert "2026-10-22" in slots["reason"]


def test_slot_too_close_to_now_moves_to_tomorrow():
    assert next_slots([], NOW.replace(hour=10, minute=45))["reels"][0] == "2026-10-20T12:00:00-03:00"
