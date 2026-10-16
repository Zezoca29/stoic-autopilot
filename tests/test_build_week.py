from datetime import timedelta

import pytest

from factories import NOW, SETTINGS, make_quotes
from generator.build_week import build_week, preview_item
from shared.jsonio import read_json, write_json


def fake_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage, handle):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(b"mp4")
    assert handle == "@estoico"
    return [f"pixabay:{item['id']}-a", f"pixabay:{item['id']}-b"]


def fake_carousel(item, quotes, out_dir, handle):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for number in range(1, len(item["slides"]) + 1):
        path = out_dir / f"slide-{number:02d}.jpg"
        path.write_bytes(b"jpg")
        paths.append(path)
    return paths


def no_media_problems(batch, output_dir):
    return []


@pytest.fixture
def paths(tmp_path, week):
    batch = tmp_path / "batch.json"
    write_json(batch, week)
    quotes = tmp_path / "quotes.json"
    write_json(quotes, make_quotes())
    return {"batch": batch, "quotes_path": quotes, "queue_path": tmp_path / "queue.json",
            "history_path": tmp_path / "history.json", "output_dir": tmp_path / "output"}


def run_build(paths, now=NOW, **overrides):
    kwargs = dict(now=now, settings=SETTINGS, quotes_path=paths["quotes_path"], queue_path=paths["queue_path"],
                  history_path=paths["history_path"], output_dir=paths["output_dir"],
                  reel_renderer=fake_reel, carousel_renderer=fake_carousel, media_checker=no_media_problems)
    kwargs.update(overrides)
    return build_week(paths["batch"], **kwargs)


def test_successful_build_queues_everything_and_records_history(paths):
    assert run_build(paths) == []
    queue = read_json(paths["queue_path"])
    assert len(queue) == 10
    assert queue[0]["id"] == "2026-10-19-r1" and queue[0]["media"] == ["reel.mp4"]
    carousel = next(e for e in queue if e["id"] == "2026-10-19-c1")
    assert carousel["media"] == [f"slide-{n:02d}.jpg" for n in range(1, 7)]
    history = read_json(paths["history_path"])
    assert history["quotes"]["q1"] == {"on": "2026-10-19", "item": "2026-10-19-r1"}
    assert history["footage"]["pixabay:2026-10-19-r1-b"]["item"] == "2026-10-19-r1"


def test_plan_errors_stop_before_rendering(paths):
    def explode(*args, **kwargs):
        raise AssertionError("renderer must not run")

    errors = run_build(paths, now=NOW + timedelta(days=30), reel_renderer=explode, carousel_renderer=explode)
    assert errors and all("in the past" in error for error in errors)
    assert not paths["queue_path"].exists()


def test_render_failure_reports_item_and_writes_nothing(paths):
    def flaky_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage, handle):
        if item["id"] == "2026-10-19-r3":
            raise RuntimeError("ffmpeg failed: boom")
        return fake_reel(item, quote, work_dir, out_path, api_key=api_key, exclude_footage=exclude_footage, handle=handle)

    assert run_build(paths, reel_renderer=flaky_reel) == ["2026-10-19-r3: render failed: ffmpeg failed: boom"]
    assert not paths["queue_path"].exists() and not paths["history_path"].exists()


def test_media_check_failure_writes_nothing(paths):
    errors = run_build(paths, media_checker=lambda batch, out: ["2026-10-19-r1: reel lasts 20.0s"])
    assert errors == ["2026-10-19-r1: reel lasts 20.0s"]
    assert not paths["queue_path"].exists()


def test_rebuilding_same_batch_is_allowed(paths):
    assert run_build(paths) == []
    assert run_build(paths) == []
    assert len(read_json(paths["queue_path"])) == 10


def test_footage_is_not_repeated_within_batch(paths):
    seen = []

    def recording_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage, handle):
        seen.append(set(exclude_footage))
        return fake_reel(item, quote, work_dir, out_path, api_key=api_key, exclude_footage=exclude_footage, handle=handle)

    run_build(paths, reel_renderer=recording_reel)
    assert seen[0] == set() and {"pixabay:2026-10-19-r1-a", "pixabay:2026-10-19-r1-b"} <= seen[1]


def test_preview_renders_one_item_and_can_enqueue(paths):
    errors = preview_item(paths["batch"], "2026-10-19-r1", settings=SETTINGS, quotes_path=paths["quotes_path"],
                          queue_path=paths["queue_path"], output_dir=paths["output_dir"], enqueue=True,
                          reel_renderer=fake_reel, carousel_renderer=fake_carousel,
                          media_checker=no_media_problems)
    assert errors == []
    assert [e["id"] for e in read_json(paths["queue_path"])] == ["2026-10-19-r1"]


def test_preview_unknown_item(paths):
    assert preview_item(paths["batch"], "nope", settings=SETTINGS, quotes_path=paths["quotes_path"]) == \
        [f"nope: not found in {paths['batch']}"]
