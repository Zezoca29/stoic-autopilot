"""Compose a narrated vertical reel with ffmpeg."""
import random
import subprocess
from pathlib import Path

from generator import footage, tts
from generator.captions import write_ass
from generator.quotes import display_reference
from shared.config import ROOT

WIDTH, HEIGHT, FPS = 1080, 1920, 30
TAIL_SECONDS = 1.0
MUSIC_VOLUME = 0.1  # about -20 dB under the narration
MUSIC_DIR = ROOT / "generator" / "music"
SUBTITLES_NAME = "subs.ass"  # relative: ffmpeg runs inside work_dir so Windows paths never reach the filter graph


class RenderError(RuntimeError):
    """ffmpeg could not produce the reel."""


def pick_music(item_id: str, music_dir: Path | None = None) -> Path | None:
    tracks = sorted(Path(music_dir or MUSIC_DIR).glob("*.mp3"))
    return random.Random(item_id).choice(tracks) if tracks else None


def build_ffmpeg_cmd(background, narration, music, subtitles_name, duration, out_path) -> list[str]:
    cmd = ["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", str(background), "-i", str(narration)]
    video = (f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
             f"fps={FPS},eq=brightness=-0.12,ass={subtitles_name}[v]")
    if music is not None:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        audio = f"[2:a]volume={MUSIC_VOLUME}[m];[1:a][m]amix=inputs=2:duration=longest:normalize=0[a]"
    else:
        audio = "[1:a]apad[a]"
    return cmd + ["-filter_complex", f"{video};{audio}", "-map", "[v]", "-map", "[a]",
                  "-t", f"{duration:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                  str(out_path)]


def render_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage,
                synthesize=tts.synthesize, fetch=footage.fetch_footage, run=subprocess.run) -> str:
    """Render item to out_path; returns the footage id used."""
    work_dir, out_path = Path(work_dir), Path(out_path).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    narration = work_dir / "narration.mp3"
    words = synthesize(item["script"], narration)
    duration = words[-1].end + TAIL_SECONDS
    write_ass(work_dir / SUBTITLES_NAME, words, display_reference(quote), duration)
    background = work_dir / "background.mp4"
    footage_id = fetch(item["footage_keywords"], item["pillar"], exclude_footage, background, api_key)
    cmd = build_ffmpeg_cmd(background.resolve(), narration.resolve(), pick_music(item["id"]),
                           SUBTITLES_NAME, duration, out_path)
    result = run(cmd, cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise RenderError(f"ffmpeg failed: {result.stderr[-800:]}")
    return footage_id
