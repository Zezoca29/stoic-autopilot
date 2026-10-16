from generator.captions import blocks, build_ass, caption_events, clean, format_time
from generator.tts import Word


def spoken(*specs):
    return [Word(text, start, end) for text, start, end in specs]


WORDS = spoken(("Você", 0.0, 0.4), ("sofre", 0.5, 0.9), ("mais", 1.0, 1.3), ("hoje", 1.6, 2.0),
               ("e", 2.1, 2.2), ("sempre", 2.3, 2.8))


def test_format_time():
    assert format_time(0) == "0:00:00.00"
    assert format_time(61.234) == "0:01:01.23"
    assert format_time(3725.5) == "1:02:05.50"


def test_blocks_break_on_pauses_after_three_words():
    assert [[w.text for w in block] for block in blocks(WORDS)] == [["Você", "sofre", "mais"], ["hoje", "e", "sempre"]]


def test_short_pause_inside_first_words_does_not_break():
    words = spoken(("A", 0.0, 0.2), ("vida", 0.5, 0.8), ("é", 0.9, 1.0), ("breve", 1.1, 1.5))
    assert len(blocks(words)) == 1


def test_blocks_cap_at_nine_words():
    words = [Word(f"w{i}", i * 0.3, i * 0.3 + 0.25) for i in range(20)]
    assert [len(block) for block in blocks(words)] == [9, 9, 2]


def test_each_word_highlighted_within_its_block():
    events = caption_events(WORDS)
    assert len(events) == 6
    assert events[0] == ("Dialogue: 0,0:00:00.00,0:00:00.50,Caption,,0,0,0,,"
                         "{\\c&H0037AFD4&}Você{\\c&H00FFFFFF&} sofre mais")
    assert events[3].endswith(",,{\\c&H0037AFD4&}hoje{\\c&H00FFFFFF&} e sempre")


def test_block_stays_on_screen_until_next_block():
    events = caption_events(WORDS)
    assert events[2].startswith("Dialogue: 0,0:00:01.00,0:00:01.60,Caption")  # held through the pause
    assert events[5].startswith("Dialogue: 0,0:00:02.30,0:00:02.80,Caption")  # last block ends with its word


def test_clean_strips_markup_and_emoji():
    assert clean(" {olá}\\ 🙂 ") == "olá"


def test_build_ass_reference_band_and_handle():
    ass = build_ass(WORDS, "Sêneca, Cartas a Lucílio 13.4", 3.0, handle="@fortalezainterior")
    assert "PlayResX: 1080" in ass and "PlayResY: 1920" in ass
    reference_style = next(line for line in ass.splitlines() if line.startswith("Style: Reference"))
    assert reference_style.split(",")[15] == "3"  # BorderStyle 3 = translucent box behind the text
    assert "Dialogue: 0,0:00:00.00,0:00:03.00,Reference,,0,0,0,,Sêneca, Cartas a Lucílio 13.4" in ass
    assert "Dialogue: 0,0:00:00.00,0:00:03.00,Handle,,0,0,0,,@fortalezainterior" in ass


def test_build_ass_without_handle_has_no_handle_line():
    assert ",Handle,," not in build_ass(WORDS, "Ref", 3.0)
