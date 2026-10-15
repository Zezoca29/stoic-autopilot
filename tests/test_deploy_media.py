from datetime import timedelta

from factories import NOW, make_reel
from generator.deploy_media import assemble, prune_output, push_pages
from shared.post_queue import make_entry, mark_published


def reel_entry(n, when):
    return make_entry(make_reel(n, when), ["reel.mp4"])


def setup_output(tmp_path, entry):
    folder = tmp_path / "output" / entry["id"]
    folder.mkdir(parents=True)
    for name in entry["media"]:
        (folder / name).write_bytes(b"media")


def make_site(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("<h1>links</h1>", encoding="utf-8")
    return site


def test_assemble_copies_site_and_pending_media_only(tmp_path):
    pending, done = reel_entry(1, NOW), reel_entry(2, NOW)
    mark_published(done, "instagram", "ig-1")
    for entry in (pending, done):
        setup_output(tmp_path, entry)
    dest = tmp_path / "pages"
    assert assemble([pending, done], tmp_path / "output", make_site(tmp_path), dest) == []
    assert (dest / "index.html").exists() and (dest / ".nojekyll").exists()
    assert (dest / "media" / pending["id"] / "reel.mp4").read_bytes() == b"media"
    assert not (dest / "media" / done["id"]).exists()


def test_assemble_reports_missing_media(tmp_path):
    entry = reel_entry(1, NOW)
    missing = assemble([entry], tmp_path / "output", make_site(tmp_path), tmp_path / "pages")
    assert missing == [str(tmp_path / "output" / entry["id"] / "reel.mp4")]


def test_push_pages_force_pushes_a_single_commit(tmp_path):
    calls = []
    push_pages(tmp_path, "https://github.com/u/stoic-autopilot.git", run=lambda cmd, **kwargs: calls.append(cmd))
    assert calls[0] == ["git", "init", "-q", "-b", "gh-pages"]
    assert calls[-1] == ["git", "push", "-f", "https://github.com/u/stoic-autopilot.git", "gh-pages"]


def test_prune_output_keeps_recent_and_pending(tmp_path):
    old_done, recent_done = reel_entry(1, NOW - timedelta(days=20)), reel_entry(2, NOW - timedelta(days=3))
    old_pending = reel_entry(3, NOW - timedelta(days=20))
    mark_published(old_done, "instagram", "1")
    mark_published(recent_done, "instagram", "2")
    for entry in (old_done, recent_done, old_pending):
        setup_output(tmp_path, entry)
    removed = prune_output([old_done, recent_done, old_pending], tmp_path / "output", NOW)
    assert removed == [old_done["id"]]
    assert (tmp_path / "output" / recent_done["id"]).exists()
    assert (tmp_path / "output" / old_pending["id"]).exists()
