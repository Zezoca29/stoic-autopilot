from generator.captions import build_ass, caption_events, clean, format_time
from generator.tts import Word

WORDS = [Word("Você", 0.0, 0.4), Word("sofre", 0.5, 0.9), Word("mais", 1.0, 1.3), Word("hoje", 1.5, 2.0)]


def test_format_time():
    assert format_time(0) == "0:00:00.00"
    assert format_time(61.234) == "0:01:01.23"
    assert format_time(3725.5) == "1:02:05.50"


def test_each_word_is_highlighted_within_its_chunk():
    events = caption_events(WORDS)
    assert len(events) == 4
    assert events[0] == ("Dialogue: 0,0:00:00.00,0:00:00.50,Caption,,0,0,0,,"
                         "{\\c&H0037AFD4&}Você{\\c&H00FFFFFF&} sofre mais")
    assert events[2].startswith("Dialogue: 0,0:00:01.00,0:00:01.30,Caption")
    assert events[3] == ("Dialogue: 0,0:00:01.50,0:00:02.00,Caption,,0,0,0,,"
                         "{\\c&H0037AFD4&}hoje{\\c&H00FFFFFF&}")


def test_clean_strips_markup_and_emoji():
    assert clean(" {olá}\\ 🙂 ") == "olá"


def test_build_ass_shows_reference_for_whole_video():
    ass = build_ass(WORDS, "Sêneca, Cartas a Lucílio 13.4", 3.0)
    assert "PlayResX: 1080" in ass and "PlayResY: 1920" in ass
    assert "Dialogue: 0,0:00:00.00,0:00:03.00,Reference,,0,0,0,,Sêneca, Cartas a Lucílio 13.4" in ass
