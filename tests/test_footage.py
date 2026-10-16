import pytest
import requests

from generator import footage
from generator.footage import FootageError, choose_file, fetch_footage, pick_video


class FakeResponse:
    def __init__(self, payload=None, content=b""):
        self.payload, self.content = payload, content

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload

    def iter_content(self, chunk_size):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, results_by_query):
        self.results_by_query = results_by_query
        self.queries = []
        self.params = []

    def get(self, url, params=None, headers=None, timeout=None, stream=False):
        if url == footage.SEARCH_URL:
            self.queries.append(params["q"])
            self.params.append(params)
            return FakeResponse({"hits": self.results_by_query.get(params["q"], [])})
        return FakeResponse(content=b"video-bytes")


def rendition(vid, name, width, height, size=5_000_000):
    return {"url": f"https://cdn/{vid}-{name}.mp4", "width": width, "height": height, "size": size}


def video(vid, duration=15, videos=None):
    if videos is None:
        videos = {"large": rendition(vid, "large", 3840, 2160, 40_000_000),
                  "medium": rendition(vid, "medium", 1920, 1080),
                  "small": rendition(vid, "small", 1280, 720),
                  "tiny": rendition(vid, "tiny", 960, 540)}
    return {"id": vid, "duration": duration, "videos": videos}


def test_choose_file_prefers_large_rendition():
    assert choose_file(video(1))["url"] == "https://cdn/1-large.mp4"


def test_choose_file_falls_back_to_medium_when_large_missing_or_huge():
    missing = video(1)
    missing["videos"]["large"] = {"url": "", "width": 0, "height": 0, "size": 0}
    huge = video(2)
    huge["videos"]["large"]["size"] = 500_000_000
    assert choose_file(missing)["url"] == "https://cdn/1-medium.mp4"
    assert choose_file(huge)["url"] == "https://cdn/2-medium.mp4"


def test_choose_file_none_when_too_small():
    tiny_only = {"tiny": rendition(1, "tiny", 640, 360)}
    assert choose_file(video(1, videos=tiny_only)) is None


def test_search_sends_key_and_filters():
    session = FakeSession({})
    pick_video_safely = lambda: pick_video(["calm ocean"], "controle", set(), "the-key", session)  # noqa: E731
    with pytest.raises(FootageError):
        pick_video_safely()
    assert session.params[0]["key"] == "the-key"
    assert session.params[0]["video_type"] == "film"
    assert session.params[0]["safesearch"] == "true"


def test_pick_video_skips_excluded_and_short_clips():
    session = FakeSession({"calm ocean": [video(1), video(2, duration=5), video(3)]})
    assert pick_video(["calm ocean"], "controle", {"pixabay:1"}, "key", session) == \
        ("pixabay:3", "https://cdn/3-large.mp4")


def test_pick_video_falls_back_to_pillar_keywords():
    session = FakeSession({"mountain fog": [video(9)]})
    assert pick_video(["nothing"], "controle", set(), "key", session)[0] == "pixabay:9"
    assert session.queries == ["nothing", "calm ocean", "mountain fog"]


def test_fetch_footage_downloads(tmp_path):
    session = FakeSession({"calm ocean": [video(1)]})
    out = tmp_path / "bg.mp4"
    assert fetch_footage(["calm ocean"], "controle", set(), out, "key", session=session) == "pixabay:1"
    assert out.read_bytes() == b"video-bytes"


def test_fetch_footage_uses_local_fallback_when_pixabay_fails(tmp_path, monkeypatch):
    fallback = tmp_path / "fallback.mp4"
    fallback.write_bytes(b"fallback")
    monkeypatch.setattr(footage, "FALLBACK_VIDEO", fallback)

    class Down(FakeSession):
        def get(self, *args, **kwargs):
            raise requests.ConnectionError("down")

    out = tmp_path / "bg.mp4"
    assert fetch_footage(["x"], "controle", set(), out, "key", session=Down({})) == "fallback"
    assert out.read_bytes() == b"fallback"


@pytest.mark.parametrize("status", [400, 401, 403])
def test_rejected_api_key_is_an_error_not_a_silent_fallback(tmp_path, monkeypatch, status):
    fallback = tmp_path / "fallback.mp4"
    fallback.write_bytes(b"fallback")
    monkeypatch.setattr(footage, "FALLBACK_VIDEO", fallback)

    class Rejected(FakeSession):
        def get(self, *args, **kwargs):
            response = requests.Response()
            response.status_code = status
            raise requests.HTTPError(f"{status} Client Error for url: https://pixabay.com/api/videos/?key=SECRETKEY",
                                     response=response)

    with pytest.raises(FootageError, match="PIXABAY_API_KEY") as info:
        fetch_footage(["x"], "controle", set(), tmp_path / "bg.mp4", "SECRETKEY", session=Rejected({}))
    assert "SECRETKEY" not in str(info.value)
