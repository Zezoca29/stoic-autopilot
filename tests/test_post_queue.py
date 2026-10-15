from datetime import timedelta

import pytest

from factories import NOW, make_reel
from shared.post_queue import add_entries, due_entries, make_entry, mark_failed, mark_published


def reel_entry(n, when):
    return make_entry(make_reel(n, when), ["reel.mp4"])


def test_make_entry_marks_tiktok_manual_and_composes_caption():
    entry = reel_entry(1, NOW)
    assert entry["platforms"]["instagram"]["status"] == "pending"
    assert entry["platforms"]["tiktok"]["status"] == "manual"
    assert entry["caption"] == "Legenda 1\n\n#estoicismo"


def test_add_entries_sorts_and_replaces_unpublished():
    late, early = reel_entry(2, NOW + timedelta(days=1)), reel_entry(1, NOW)
    queue = add_entries([], [late, early])
    assert [e["id"] for e in queue] == [early["id"], late["id"]]
    assert add_entries(queue, [dict(early, caption="nova")])[0]["caption"] == "nova"


def test_add_entries_refuses_to_replace_published():
    entry = reel_entry(1, NOW)
    mark_published(entry, "instagram", "ig-1")
    with pytest.raises(ValueError, match="already published"):
        add_entries([entry], [reel_entry(1, NOW)])


def test_due_entries():
    past, future = reel_entry(1, NOW - timedelta(hours=1)), reel_entry(2, NOW + timedelta(hours=1))
    assert due_entries([past, future], "instagram", NOW) == [past]
    assert due_entries([past, future], "tiktok", NOW) == []


def test_mark_failed_gives_up_after_three_attempts():
    entry = reel_entry(1, NOW)
    assert mark_failed(entry, "instagram", "boom") is False
    assert mark_failed(entry, "instagram", "boom") is False
    assert mark_failed(entry, "instagram", "boom") is True
    assert entry["platforms"]["instagram"] == {"status": "failed", "attempts": 3,
                                               "published_id": None, "last_error": "boom"}
