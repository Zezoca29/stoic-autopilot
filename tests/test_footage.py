import requests

from generator import footage
from generator.footage import choose_file, fetch_footage, pick_video


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

    def get(self, url, params=None, headers=None, timeout=None, stream=False):
        if url == footage.SEARCH_URL:
            self.queries.append(params["query"])
            return FakeResponse({"videos": self.results_by_query.get(params["query"], [])})
        return FakeResponse(content=b"video-bytes")


def video(vid, duration=15, files=None):
    if files is None:
        files = [{"file_type": "video/mp4", "width": 720, "height": 1280, "link": f"https://cdn/{vid}-720.mp4"},
                 {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": f"https://cdn/{vid}-1080.mp4"},
                 {"file_type": "video/mp4", "width": 1920, "height": 1080, "link": f"https://cdn/{vid}-land.mp4"}]
    return {"id": vid, "duration": duration, "video_files": files}


def test_choose_file_prefers_portrait_closest_to_1920():
    assert choose_file(video(1))["link"] == "https://cdn/1-1080.mp4"


def test_choose_file_none_without_portrait():
    landscape = [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "x"}]
    assert choose_file(video(1, files=landscape)) is None


def test_pick_video_skips_excluded_and_short_clips():
    session = FakeSession({"calm ocean": [video(1), video(2, duration=5), video(3)]})
    assert pick_video(["calm ocean"], "controle", {"pexels:1"}, "key", session) == \
        ("pexels:3", "https://cdn/3-1080.mp4")


def test_pick_video_falls_back_to_pillar_keywords():
    session = FakeSession({"mountain fog": [video(9)]})
    assert pick_video(["nothing"], "controle", set(), "key", session)[0] == "pexels:9"
    assert session.queries == ["nothing", "calm ocean", "mountain fog"]


def test_fetch_footage_downloads(tmp_path):
    session = FakeSession({"calm ocean": [video(1)]})
    out = tmp_path / "bg.mp4"
    assert fetch_footage(["calm ocean"], "controle", set(), out, "key", session=session) == "pexels:1"
    assert out.read_bytes() == b"video-bytes"


def test_fetch_footage_uses_local_fallback_when_pexels_fails(tmp_path, monkeypatch):
    fallback = tmp_path / "fallback.mp4"
    fallback.write_bytes(b"fallback")
    monkeypatch.setattr(footage, "FALLBACK_VIDEO", fallback)

    class Down(FakeSession):
        def get(self, *args, **kwargs):
            raise requests.ConnectionError("down")

    out = tmp_path / "bg.mp4"
    assert fetch_footage(["x"], "controle", set(), out, "key", session=Down({})) == "fallback"
    assert out.read_bytes() == b"fallback"
