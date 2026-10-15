"""Word-by-word animated captions as an ASS subtitle file burned in by ffmpeg."""
from pathlib import Path

from generator.tts import Word

WORDS_PER_CHUNK = 3
HIGHLIGHT = "&H0037AFD4&"  # #D4AF37 gold, ASS uses &HAABBGGRR
WHITE = "&H00FFFFFF&"

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Georgia,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,2,5,80,80,0,1
Style: Reference,Georgia,46,&H00F0E6D7,&H00FFFFFF,&H00000000,&H64000000,0,1,0,0,100,100,0,0,1,3,1,8,80,80,220,1

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


def caption_events(words: list[Word]) -> list[str]:
    events = []
    for first in range(0, len(words), WORDS_PER_CHUNK):
        chunk = words[first:first + WORDS_PER_CHUNK]
        for index, word in enumerate(chunk):
            end = chunk[index + 1].start if index + 1 < len(chunk) else word.end
            parts = [f"{{\\c{HIGHLIGHT}}}{clean(w.text)}{{\\c{WHITE}}}" if j == index else clean(w.text)
                     for j, w in enumerate(chunk)]
            events.append(f"Dialogue: 0,{format_time(word.start)},{format_time(end)},Caption,,0,0,0,,"
                          f"{' '.join(parts)}")
    return events


def build_ass(words: list[Word], reference: str, total_duration: float) -> str:
    lines = [HEADER,
             f"Dialogue: 0,{format_time(0)},{format_time(total_duration)},Reference,,0,0,0,,{clean(reference)}",
             *caption_events(words)]
    return "\n".join(lines) + "\n"


def write_ass(path: Path, words: list[Word], reference: str, total_duration: float) -> None:
    Path(path).write_text(build_ass(words, reference, total_duration), encoding="utf-8")
