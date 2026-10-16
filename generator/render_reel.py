"""Compose a narrated vertical reel with ffmpeg: 2–3 background scenes joined by crossfades."""
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
SCENE_SECONDS = 14
MIN_SCENES, MAX_SCENES = 2, 3
CROSSFADE_SECONDS = 0.5
MUSIC_DIR = ROOT / "generator" / "music"
SUBTITLES_NAME = "subs.ass"  # relative: ffmpeg runs inside work_dir so Windows paths never reach the filter graph


class RenderError(RuntimeError):
    """ffmpeg could not produce the reel."""


def pick_music(item_id: str, music_dir: Path | None = None) -> Path | None:
    tracks = sorted(Path(music_dir or MUSIC_DIR).glob("*.mp3"))
    return random.Random(item_id).choice(tracks) if tracks else None


def scene_count(duration: float) -> int:
    return min(MAX_SCENES, max(MIN_SCENES, round(duration / SCENE_SECONDS)))


def _video_graph(scenes: int, duration: float, subtitles_name: str) -> str:
    # Each scene is long enough that, after overlapping by the crossfade, they add up to the duration.
    length = (duration + (scenes - 1) * CROSSFADE_SECONDS) / scenes
    parts = [f"[{i}:v]trim=duration={length:.3f},setpts=PTS-STARTPTS,"
             f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
             f"fps={FPS},format=yuv420p[s{i}]" for i in range(scenes)]
    previous = "s0"
    for k in range(1, scenes):
        offset = k * (length - CROSSFADE_SECONDS)
        parts.append(f"[{previous}][s{k}]xfade=transition=fade:duration={CROSSFADE_SECONDS}:"
                     f"offset={offset:.3f}[x{k}]")
        previous = f"x{k}"
    parts.append(f"[{previous}]eq=brightness=-0.12,ass={subtitles_name}[v]")
    return ";".join(parts)


def build_ffmpeg_cmd(backgrounds, narration, music, subtitles_name, duration, out_path) -> list[str]:
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for background in backgrounds:
        cmd += ["-stream_loop", "-1", "-i", str(background)]
    narration_index = len(backgrounds)
    cmd += ["-i", str(narration)]
    if music is not None:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        audio = (f"[{narration_index + 1}:a]volume={MUSIC_VOLUME}[m];"
                 f"[{narration_index}:a][m]amix=inputs=2:duration=longest:normalize=0[a]")
    else:
        audio = f"[{narration_index}:a]apad[a]"
    graph = f"{_video_graph(len(backgrounds), duration, subtitles_name)};{audio}"
    return cmd + ["-filter_complex", graph, "-map", "[v]", "-map", "[a]",
                  "-t", f"{duration:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                  str(out_path)]


def _rotated(keywords: list[str], shift: int) -> list[str]:
    if not keywords:
        return []
    shift %= len(keywords)
    return keywords[shift:] + keywords[:shift]


def render_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage, handle="",
                synthesize=tts.synthesize, fetch=footage.fetch_footage, run=subprocess.run) -> list[str]:
    """Render item to out_path; returns the footage ids used, one per scene."""
    work_dir, out_path = Path(work_dir), Path(out_path).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    narration = work_dir / "narration.mp3"
    words = synthesize(item["script"], narration)
    duration = words[-1].end + TAIL_SECONDS
    write_ass(work_dir / SUBTITLES_NAME, words, display_reference(quote), duration, handle)
    backgrounds, footage_ids, exclude = [], [], set(exclude_footage)
    for scene in range(scene_count(duration)):
        background = work_dir / f"background-{scene}.mp4"
        footage_id = fetch(_rotated(item["footage_keywords"], scene), item["pillar"], exclude, background, api_key)
        exclude.add(footage_id)
        footage_ids.append(footage_id)
        backgrounds.append(background.resolve())
    cmd = build_ffmpeg_cmd(backgrounds, narration.resolve(), pick_music(item["id"]), SUBTITLES_NAME, duration,
                           out_path)
    result = run(cmd, cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise RenderError(f"ffmpeg failed: {result.stderr[-800:]}")
    return footage_ids
