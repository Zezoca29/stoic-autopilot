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


def test_ffmpeg_cmd_with_music_mixes_two_audio_inputs(tmp_path):
    cmd = rr.build_ffmpeg_cmd(tmp_path / "bg.mp4", tmp_path / "n.mp3", tmp_path / "m.mp3", "subs.ass", 42.5,
                              tmp_path / "out.mp4")
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert "ass=subs.ass" in graph
    assert "[2:a]volume=0.1[m];[1:a][m]amix=inputs=2:duration=longest:normalize=0[a]" in graph
    assert cmd[cmd.index("-t") + 1] == "42.50"
    assert cmd.count("-stream_loop") == 2


def test_ffmpeg_cmd_without_music_pads_narration(tmp_path):
    cmd = rr.build_ffmpeg_cmd(tmp_path / "bg.mp4", tmp_path / "n.mp3", None, "subs.ass", 30.0,
                              tmp_path / "out.mp4")
    assert cmd[cmd.index("-filter_complex") + 1].endswith("[1:a]apad[a]")
    assert cmd.count("-stream_loop") == 1


def test_pick_music_is_deterministic(tmp_path):
    for name in ("a.mp3", "b.mp3", "c.mp3"):
        (tmp_path / name).write_bytes(b"")
    assert rr.pick_music("id-1", tmp_path) == rr.pick_music("id-1", tmp_path)
    assert rr.pick_music("id-1", tmp_path / "empty") is None


def test_render_reel_reports_ffmpeg_stderr(tmp_path):
    def fake_synth(text, out_path):
        out_path.write_bytes(b"")
        return [Word("a", 0.0, 1.0)]

    def fake_fetch(keywords, pillar, exclude, out_path, api_key):
        return "pexels:1"

    def failing_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, "", "Invalid data found")

    with pytest.raises(rr.RenderError, match="Invalid data found"):
        rr.render_reel(make_reel(1, NOW), make_quotes(1)[0], tmp_path / "work", tmp_path / "reel.mp4",
                       api_key="k", exclude_footage=set(), synthesize=fake_synth, fetch=fake_fetch,
                       run=failing_run)


@needs_ffmpeg
def test_render_reel_produces_vertical_video(tmp_path, monkeypatch):
    monkeypatch.setattr(rr, "MUSIC_DIR", tmp_path / "no-music")
    source = tmp_path / "source.mp4"
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=720x1280:rate=30:duration=3", "-pix_fmt", "yuv420p", str(source))

    def fake_synth(text, out_path):
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=4", str(out_path))
        return [Word("Você", 0.0, 0.5), Word("sofre", 0.6, 1.2), Word("mais", 1.3, 4.0)]

    def fake_fetch(keywords, pillar, exclude, out_path, api_key):
        shutil.copyfile(source, out_path)
        return "pexels:1"

    out = tmp_path / "reel.mp4"
    footage_id = rr.render_reel(make_reel(1, NOW), make_quotes(1)[0], tmp_path / "work", out, api_key="k",
                                exclude_footage=set(), synthesize=fake_synth, fetch=fake_fetch)
    info = probe(out)
    assert footage_id == "pexels:1"
    assert (info.width, info.height) == (1080, 1920)
    assert info.duration == pytest.approx(5.0, abs=0.2)
