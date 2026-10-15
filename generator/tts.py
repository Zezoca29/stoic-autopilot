"""Narration with edge-tts (free Microsoft neural voices), keeping per-word timings for captions."""
import asyncio
import time
from dataclasses import dataclass
from pathlib import Path

import edge_tts

from shared.config import VOICE

TICKS_PER_SECOND = 10_000_000  # edge-tts offsets and durations come in 100 ns ticks


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


class TTSError(RuntimeError):
    """Narration could not be synthesized."""


def _default_factory(text: str, voice: str):
    return edge_tts.Communicate(text, voice, boundary="WordBoundary")


async def _synthesize(text, voice, out_path, communicate_factory) -> list[Word]:
    communicate = communicate_factory(text, voice)
    words = []
    with open(out_path, "wb") as audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / TICKS_PER_SECOND
                words.append(Word(chunk["text"], start, start + chunk["duration"] / TICKS_PER_SECOND))
    if not words:
        raise TTSError("edge-tts returned no word timings")
    return words


def synthesize(text: str, out_path: Path, voice: str = VOICE, retries: int = 3, wait_seconds: float = 5.0,
               communicate_factory=_default_factory, sleep=time.sleep) -> list[Word]:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return asyncio.run(_synthesize(text, voice, Path(out_path), communicate_factory))
        except Exception as exc:  # edge-tts surfaces network failures as varied exception types
            last_error = exc
            if attempt < retries:
                sleep(wait_seconds)
    raise TTSError(f"edge-tts failed after {retries} attempts: {last_error}") from last_error
