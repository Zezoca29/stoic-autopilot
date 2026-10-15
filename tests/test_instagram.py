import pytest

from publisher.instagram import BASE, InstagramClient, InstagramError


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self.payload = status, payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self, method, url, data):
        self.calls.append((method, url.removeprefix(BASE + "/"), data))
        return self.responses.pop(0)

    def post(self, url, data=None, timeout=None):
        return self._next("POST", url, data)

    def get(self, url, params=None, timeout=None):
        return self._next("GET", url, params)


def ok(payload):
    return FakeResponse(200, payload)


def make_client(responses):
    session = FakeSession(responses)
    return InstagramClient("178", "tok", session=session, sleep=lambda s: None, max_polls=3), session


def test_publish_reel_waits_for_container_then_publishes():
    client, session = make_client([ok({"id": "c1"}), ok({"status_code": "IN_PROGRESS"}),
                                   ok({"status_code": "FINISHED"}), ok({"id": "m1"})])
    assert client.publish_reel("https://x/reel.mp4", "legenda") == "m1"
    assert session.calls[0] == ("POST", "178/media", {"media_type": "REELS", "video_url": "https://x/reel.mp4",
                                                       "caption": "legenda", "share_to_feed": "true",
                                                       "access_token": "tok"})
    assert session.calls[1][:2] == ("GET", "c1")
    assert session.calls[-1] == ("POST", "178/media_publish", {"creation_id": "c1", "access_token": "tok"})


def test_publish_carousel_creates_children_then_parent():
    client, session = make_client([ok({"id": "i1"}), ok({"id": "i2"}), ok({"status_code": "FINISHED"}),
                                   ok({"status_code": "FINISHED"}), ok({"id": "car"}),
                                   ok({"status_code": "FINISHED"}), ok({"id": "m2"})])
    assert client.publish_carousel(["https://x/1.jpg", "https://x/2.jpg"], "legenda") == "m2"
    assert session.calls[0][2]["is_carousel_item"] == "true"
    assert session.calls[4][2]["media_type"] == "CAROUSEL"
    assert session.calls[4][2]["children"] == "i1,i2"


def test_container_error_status_raises():
    client, _ = make_client([ok({"id": "c1"}), ok({"status_code": "ERROR", "status": "bad video"})])
    with pytest.raises(InstagramError, match="status ERROR"):
        client.publish_reel("u", "x")


def test_container_timeout_raises():
    client, _ = make_client([ok({"id": "c1"})] + [ok({"status_code": "IN_PROGRESS"})] * 3)
    with pytest.raises(InstagramError, match="not ready"):
        client.publish_reel("u", "x")


def test_api_error_keeps_code():
    client, _ = make_client([FakeResponse(400, {"error": {"message": "Error validating access token",
                                                          "code": 190}})])
    with pytest.raises(InstagramError) as info:
        client.publish_reel("u", "x")
    assert info.value.code == 190
    assert "Error validating access token" in str(info.value)


def test_network_error_never_leaks_token():
    import requests

    class Broken(FakeSession):
        def get(self, url, params=None, timeout=None):
            raise requests.ConnectionError(f"Max retries exceeded with url: /c1?access_token={params['access_token']}")

    client = InstagramClient("178", "SECRETTOKEN", session=Broken([ok({"id": "c1"})]), sleep=lambda s: None,
                             max_polls=3)
    with pytest.raises(InstagramError) as info:
        client.publish_reel("u", "x")
    assert "SECRETTOKEN" not in str(info.value)
    assert "network error" in str(info.value)
    assert info.value.__cause__ is None and info.value.__suppress_context__
