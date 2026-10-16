import pytest

from generator.tts import TTSError, synthesize


class FakeCommunicate:
    def __init__(self, text, voice):
        self.text, self.voice = text, voice

    async def stream(self):
        yield {"type": "audio", "data": b"ID3"}
        yield {"type": "WordBoundary", "offset": 1_000_000, "duration": 5_000_000, "text": "Você"}
        yield {"type": "audio", "data": b"more"}
        yield {"type": "WordBoundary", "offset": 7_000_000, "duration": 3_000_000, "text": "sofre"}


class SilentCommunicate(FakeCommunicate):
    async def stream(self):
        yield {"type": "audio", "data": b"ID3"}


def no_sleep(seconds):
    pass


def test_synthesize_writes_audio_and_word_timings(tmp_path):
    out = tmp_path / "narration.mp3"
    words = synthesize("Você sofre", out, communicate_factory=FakeCommunicate, sleep=no_sleep)
    assert out.read_bytes() == b"ID3more"
    assert [w.text for w in words] == ["Você", "sofre"]
    assert words[0].start == pytest.approx(0.1) and words[0].end == pytest.approx(0.6)
    assert words[1].start == pytest.approx(0.7) and words[1].end == pytest.approx(1.0)


def test_synthesize_retries_then_succeeds(tmp_path):
    calls = []

    def flaky(text, voice):
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("boom")
        return FakeCommunicate(text, voice)

    words = synthesize("x", tmp_path / "n.mp3", communicate_factory=flaky, sleep=no_sleep)
    assert len(calls) == 3 and len(words) == 2


def test_synthesize_gives_up_after_six_attempts_with_growing_waits(tmp_path):
    def broken(text, voice):
        raise ConnectionError("down")

    waits = []
    with pytest.raises(TTSError, match="after 6 attempts"):
        synthesize("x", tmp_path / "n.mp3", communicate_factory=broken, sleep=waits.append)
    assert waits == [2, 4, 8, 16, 30]  # the TTS endpoint drops connections in short bursts


def test_no_word_boundaries_is_an_error(tmp_path):
    with pytest.raises(TTSError, match="no word timings"):
        synthesize("x", tmp_path / "n.mp3", communicate_factory=SilentCommunicate, sleep=no_sleep)


@pytest.mark.network
def test_real_edge_tts(tmp_path):
    words = synthesize("Você sofre mais na imaginação do que na realidade.", tmp_path / "n.mp3")
    assert len(words) >= 6
    assert (tmp_path / "n.mp3").stat().st_size > 1000
