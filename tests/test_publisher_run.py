from datetime import timedelta

import pytest
import requests

from factories import NOW, make_carousel, make_reel
from publisher.instagram import InstagramError
from publisher.run import media_urls, publish_due
from shared.post_queue import make_entry

BASE_URL = "https://user.github.io/stoic-autopilot"


def quiet(message):
    pass


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def publish_reel(self, url, caption):
        self.calls.append(("reel", url))
        if self.error:
            raise self.error
        return "ig-reel"

    def publish_carousel(self, urls, caption):
        self.calls.append(("carousel", urls))
        if self.error:
            raise self.error
        return "ig-carousel"


def due_reel():
    return make_entry(make_reel(1, NOW - timedelta(minutes=5)), ["reel.mp4"])


def test_media_urls():
    entry = make_entry(make_carousel(1, NOW), ["slide-01.jpg", "slide-02.jpg"])
    assert media_urls(entry, BASE_URL) == [f"{BASE_URL}/media/2026-10-19-c1/slide-01.jpg",
                                           f"{BASE_URL}/media/2026-10-19-c1/slide-02.jpg"]


def test_publishes_due_entries_only():
    due, later = due_reel(), make_entry(make_reel(2, NOW + timedelta(hours=1)), ["reel.mp4"])
    client = FakeClient()
    result = publish_due([due, later], client, BASE_URL, NOW, log=quiet)
    assert result.published == [due["id"]]
    assert client.calls == [("reel", f"{BASE_URL}/media/{due['id']}/reel.mp4")]
    assert due["platforms"]["instagram"]["published_id"] == "ig-reel"
    assert later["platforms"]["instagram"]["status"] == "pending"


def test_dry_run_does_not_call_client_or_change_queue():
    entry = due_reel()
    result = publish_due([entry], None, BASE_URL, NOW, dry_run=True, log=quiet)
    assert result.published == []
    assert entry["platforms"]["instagram"]["status"] == "pending"


def test_failures_retry_then_give_up():
    entry = due_reel()
    client = FakeClient(InstagramError("HTTP 400: Media download failed", code=9004))
    for _ in range(2):
        result = publish_due([entry], client, BASE_URL, NOW, log=quiet)
        assert result.retrying and not result.failed
    result = publish_due([entry], client, BASE_URL, NOW, log=quiet)
    assert result.failed == [f"{entry['id']}: HTTP 400: Media download failed"]
    assert entry["platforms"]["instagram"]["status"] == "failed"


def test_network_error_counts_as_attempt():
    entry = due_reel()
    result = publish_due([entry], FakeClient(requests.ConnectionError("reset")), BASE_URL, NOW, log=quiet)
    assert result.retrying == [f"{entry['id']}: network error: reset"]
    assert entry["platforms"]["instagram"]["attempts"] == 1


def test_expired_token_aborts_without_spending_attempts():
    entry = due_reel()
    with pytest.raises(InstagramError):
        publish_due([entry], FakeClient(InstagramError("expired", code=190)), BASE_URL, NOW, log=quiet)
    assert entry["platforms"]["instagram"]["attempts"] == 0


def test_only_publishes_a_future_entry_immediately():
    future = make_entry(make_reel(1, NOW + timedelta(days=2)), ["reel.mp4"])
    result = publish_due([future], FakeClient(), BASE_URL, NOW, only=future["id"], log=quiet)
    assert result.published == [future["id"]]


def test_queue_is_saved_after_each_entry():
    entries = [due_reel(), make_entry(make_reel(2, NOW - timedelta(minutes=1)), ["reel.mp4"])]
    saves = []
    publish_due(entries, FakeClient(), BASE_URL, NOW, log=quiet,
                on_change=lambda: saves.append([e["platforms"]["instagram"]["status"] for e in entries]))
    assert saves == [["published", "pending"], ["published", "published"]]
