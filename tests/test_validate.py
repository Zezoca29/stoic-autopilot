from datetime import timedelta

from PIL import Image

from factories import NOW
from generator.media_probe import MediaInfo
from generator.validate import check_media, check_plan

EMPTY = {"quotes": {}, "footage": {}}


def test_valid_week_passes(week, quotes):
    assert check_plan(week, quotes, EMPTY, NOW) == []


def test_counts(week, quotes):
    week["items"] = week["items"][1:]
    assert "batch must have 7 reels, found 6" in check_plan(week, quotes, EMPTY, NOW)


def test_unknown_quote_and_cooldown(week, quotes):
    week["items"][0]["quote_id"] = "nope"
    history = {"quotes": {"q2": {"on": "2026-09-01", "item": "old"}}, "footage": {}}
    errors = check_plan(week, quotes, history, NOW)
    assert "2026-10-19-r1: quote nope is not in content/quotes.json" in errors
    assert "2026-10-19-r2: quote q2 was used less than 60 days ago" in errors


def test_duplicate_quote_and_hook_in_batch(week, quotes):
    week["items"][1]["quote_id"] = "q1"
    week["items"][1]["hook"] = " gancho 1 "
    errors = check_plan(week, quotes, EMPTY, NOW)
    assert "2026-10-19-r2: quote q1 already used by 2026-10-19-r1 in this batch" in errors
    assert "2026-10-19-r2: hook repeats 2026-10-19-r1" in errors


def test_past_schedule_and_script_length(week, quotes):
    week["items"][0]["scheduled_at"] = (NOW - timedelta(hours=1)).isoformat()
    week["items"][1]["script"] = "curto demais"
    errors = check_plan(week, quotes, EMPTY, NOW)
    assert "2026-10-19-r1: scheduled_at is in the past" in errors
    assert "2026-10-19-r2: script has 2 words (expected 80-145)" in errors


def test_caption_hashtags_and_slides(week, quotes):
    week["items"][0]["caption"] = "x" * 2300
    week["items"][1]["hashtags"] = ["estoicismo"]
    week["items"][7]["slides"] = week["items"][7]["slides"][:3]
    week["items"][8]["slides"][0]["quote_id"] = "q5"
    errors = check_plan(week, quotes, EMPTY, NOW)
    assert any(e.startswith("2026-10-19-r1: caption has") for e in errors)
    assert "2026-10-19-r2: hashtags must be at most 30 single words starting with #" in errors
    assert "2026-10-19-c1: carousel has 3 slides (expected 6-8)" in errors
    assert "2026-10-19-c2: slide 1 quote_id must be listed in quote_ids" in errors


def write_slides(folder, count, size=(1080, 1350)):
    folder.mkdir(parents=True, exist_ok=True)
    for n in range(1, count + 1):
        Image.new("RGB", size).save(folder / f"slide-{n:02d}.jpg", "JPEG")


def render_all(week, out):
    for item in week["items"]:
        folder = out / item["id"]
        if item["type"] == "reel":
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "reel.mp4").write_bytes(b"x")
        else:
            write_slides(folder, len(item["slides"]))


def test_media_ok(tmp_path, week):
    render_all(week, tmp_path)
    assert check_media(week, tmp_path, probe=lambda path: MediaInfo(1080, 1920, 45.0, 10_000_000)) == []


def test_media_problems(tmp_path, week):
    render_all(week, tmp_path)
    (tmp_path / "2026-10-19-r1" / "reel.mp4").unlink()
    write_slides(tmp_path / "2026-10-19-c1", 6, size=(1080, 1080))
    errors = check_media(week, tmp_path, probe=lambda path: MediaInfo(1080, 1920, 20.0, 10))
    assert "2026-10-19-r1: reel.mp4 was not rendered" in errors
    assert "2026-10-19-r2: reel lasts 20.0s, expected 30-60s (adjust script length)" in errors
    assert "2026-10-19-c1: slide-01.jpg must be a 1080x1350 JPEG" in errors
