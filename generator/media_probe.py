"""Read media properties with ffprobe."""
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaInfo:
    width: int | None
    height: int | None
    duration: float
    size_bytes: int


def probe(path: Path) -> MediaInfo:
    path = Path(path)
    output = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    data = json.loads(output)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    return MediaInfo(video.get("width"), video.get("height"),
                     float(data.get("format", {}).get("duration") or 0), path.stat().st_size)
