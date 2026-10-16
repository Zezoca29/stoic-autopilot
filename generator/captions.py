"""Animated captions as an ASS subtitle file burned in by ffmpeg.

Words are grouped into blocks of 2–3 lines that break at the narrator's pauses; the spoken word is
highlighted in gold. The quote reference sits on a translucent band at the top and the handle at the bottom.
"""
from pathlib import Path

from generator.tts import Word

WORDS_PER_BLOCK = 9
MIN_BLOCK_WORDS = 3
PAUSE_SECONDS = 0.2  # edge-tts leaves ~0.2–0.3 s at commas and ~0.9 s at full stops
HOLD_GAP_SECONDS = 1.0  # keep a block on screen through pauses shorter than this
HIGHLIGHT = "&H0037AFD4&"  # #D4AF37 gold, ASS uses &HAABBGGRR
WHITE = "&H00FFFFFF&"

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Georgia,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,4,2,5,90,90,0,1
Style: Reference,Georgia,44,&H00F0E6D7,&H00FFFFFF,&H5A000000,&H5A000000,0,1,0,0,100,100,0,0,3,18,0,8,80,80,170,1
Style: Handle,Georgia,36,&H40FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,2,1,2,80,80,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""


def format_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, rest = divmod(centiseconds, 360000)
    minutes, rest = divmod(rest, 6000)
    secs, centiseconds = divmod(rest, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def clean(text: str) -> str:
    """Strip characters that break ASS markup or have no glyph in the caption font (emoji)."""
    text = "".join(ch for ch in text if ord(ch) <= 0xFFFF)
    return text.replace("{", "").replace("}", "").replace("\\", "").strip()


def blocks(words: list[Word]) -> list[list[Word]]:
    result, current = [], []
    for word in words:
        paused = current and word.start - current[-1].end >= PAUSE_SECONDS
        if current and (len(current) >= WORDS_PER_BLOCK or (paused and len(current) >= MIN_BLOCK_WORDS)):
            result.append(current)
            current = []
        current.append(word)
    if current:
        result.append(current)
    return result


def caption_events(words: list[Word]) -> list[str]:
    events = []
    groups = blocks(words)
    for group_index, block in enumerate(groups):
        next_start = groups[group_index + 1][0].start if group_index + 1 < len(groups) else None
        for index, word in enumerate(block):
            if index + 1 < len(block):
                end = block[index + 1].start
            elif next_start is not None and next_start - word.end <= HOLD_GAP_SECONDS:
                end = next_start
            else:
                end = word.end
            parts = [f"{{\\c{HIGHLIGHT}}}{clean(w.text)}{{\\c{WHITE}}}" if j == index else clean(w.text)
                     for j, w in enumerate(block)]
            events.append(f"Dialogue: 0,{format_time(word.start)},{format_time(end)},Caption,,0,0,0,,"
                          f"{' '.join(parts)}")
    return events


def build_ass(words: list[Word], reference: str, total_duration: float, handle: str = "") -> str:
    whole = f"{format_time(0)},{format_time(total_duration)}"
    lines = [HEADER, f"Dialogue: 0,{whole},Reference,,0,0,0,,{clean(reference)}"]
    if clean(handle):
        lines.append(f"Dialogue: 0,{whole},Handle,,0,0,0,,{clean(handle)}")
    lines.extend(caption_events(words))
    return "\n".join(lines) + "\n"


def write_ass(path: Path, words: list[Word], reference: str, total_duration: float, handle: str = "") -> None:
    Path(path).write_text(build_ass(words, reference, total_duration, handle), encoding="utf-8")
