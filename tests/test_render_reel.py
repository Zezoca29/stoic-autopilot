import shutil
import subprocess

import pytest

from factories import NOW, make_quotes, make_reel
from generator import render_reel as rr
from generator.media_probe import probe
from generator.tts import Word

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def graph_of(cmd):
    return cmd[cmd.index("-filter_complex") + 1]


def test_scene_count():
    assert rr.scene_count(42.6) == 3
    assert rr.scene_count(30.0) == 2
    assert rr.scene_count(5.0) == 2


def test_ffmpeg_cmd_crossfades_three_scenes_and_mixes_music(tmp_path):
    backgrounds = [tmp_path / f"bg{i}.mp4" for i in range(3)]
    cmd = rr.build_ffmpeg_cmd(backgrounds, tmp_path / "n.mp3", tmp_path / "m.mp3", "subs.ass", 42.5,
                              tmp_path / "out.mp4")
    graph = graph_of(cmd)
    assert "[0:v]trim=duration=14.500," in graph and "[2:v]trim=duration=14.500," in graph
    assert "[s0][s1]xfade=transition=fade:duration=0.5:offset=14.000[x1]" in graph
    assert "[x1][s2]xfade=transition=fade:duration=0.5:offset=28.000[x2]" in graph
    assert "[x2]eq=brightness=-0.12,ass=subs.ass[v]" in graph
    assert "[4:a]volume=0.1[m];[3:a][m]amix=inputs=2:duration=longest:normalize=0[a]" in graph
    assert cmd[cmd.index("-t") + 1] == "42.50"
    assert cmd.count("-stream_loop") == 4


def test_ffmpeg_cmd_single_scene_without_music(tmp_path):
    cmd = rr.build_ffmpeg_cmd([tmp_path / "bg.mp4"], tmp_path / "n.mp3", None, "subs.ass", 30.0,
                              tmp_path / "out.mp4")
    graph = graph_of(cmd)
    assert "xfade" not in graph
    assert "[s0]eq=brightness=-0.12,ass=subs.ass[v]" in graph
    assert graph.endswith("[1:a]apad[a]")
    assert cmd.count("-stream_loop") == 1


def test_pick_music_is_deterministic(tmp_path):
    for name in ("a.mp3", "b.mp3", "c.mp3"):
        (tmp_path / name).write_bytes(b"")
    assert rr.pick_music("id-1", tmp_path) == rr.pick_music("id-1", tmp_path)
    assert rr.pick_music("id-1", tmp_path / "empty") is None


def test_render_reel_reports_ffmpeg_stderr(tmp_path):
    def fake_synth(text, out_path):
        out_path.write_bytes(b"")
        return [Word("a", 0.0, 30.0)]

    def fake_fetch(keywords, pillar, exclude, out_path, api_key):
        return "pixabay:1"

    def failing_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, "", "Invalid data found")

    with pytest.raises(rr.RenderError, match="Invalid data found"):
        rr.render_reel(make_reel(1, NOW), make_quotes(1)[0], tmp_path / "work", tmp_path / "reel.mp4",
                       api_key="k", exclude_footage=set(), synthesize=fake_synth, fetch=fake_fetch,
                       run=failing_run)


def test_render_reel_fetches_distinct_scenes_with_rotated_keywords(tmp_path):
    calls = []

    def fake_synth(text, out_path):
        out_path.write_bytes(b"")
        return [Word("a", 0.0, 41.0)]

    def fake_fetch(keywords, pillar, exclude, out_path, api_key):
        calls.append((list(keywords), set(exclude)))
        return f"pixabay:{len(calls)}"

    item = dict(make_reel(1, NOW), footage_keywords=["sea", "stone", "fog"])
    ids = rr.render_reel(item, make_quotes(1)[0], tmp_path / "work", tmp_path / "reel.mp4", api_key="k",
                         exclude_footage={"pixabay:old"}, synthesize=fake_synth, fetch=fake_fetch,
                         run=lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, "", ""))
    assert ids == ["pixabay:1", "pixabay:2", "pixabay:3"]
    assert [keywords[0] for keywords, _ in calls] == ["sea", "stone", "fog"]
    assert calls[2][1] == {"pixabay:old", "pixabay:1", "pixabay:2"}


@needs_ffmpeg
def test_render_reel_produces_vertical_video(tmp_path, monkeypatch):
    monkeypatch.setattr(rr, "MUSIC_DIR", tmp_path / "no-music")
    source = tmp_path / "source.mp4"
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30:duration=3", "-pix_fmt", "yuv420p", str(source))

    def fake_synth(text, out_path):
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=4", str(out_path))
        return [Word("Você", 0.0, 0.5), Word("sofre", 0.6, 1.2), Word("mais", 1.3, 4.0)]

    def fake_fetch(keywords, pillar, exclude, out_path, api_key):
        shutil.copyfile(source, out_path)
        return f"pixabay:{len(exclude)}"

    out = tmp_path / "reel.mp4"
    ids = rr.render_reel(make_reel(1, NOW), make_quotes(1)[0], tmp_path / "work", out, api_key="k",
                         exclude_footage=set(), handle="@fortalezainterior", synthesize=fake_synth,
                         fetch=fake_fetch)
    info = probe(out)
    assert ids == ["pixabay:0", "pixabay:1"]
    assert (info.width, info.height) == (1080, 1920)
    assert info.duration == pytest.approx(5.0, abs=0.2)
    assert "@fortalezainterior" in (tmp_path / "work" / "subs.ass").read_text(encoding="utf-8")
