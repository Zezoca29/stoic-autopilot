import pytest

from shared.config import load_settings, require
from shared.jsonio import read_json, write_json
from shared.timeutil import parse_time


def test_load_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("PIXABAY_API_KEY", "pixabay-key")
    monkeypatch.setenv("PAGES_BASE_URL", "https://user.github.io/stoic-autopilot/")
    monkeypatch.setenv("IG_HANDLE", "@estoico")
    settings = load_settings(env_file=None)
    assert settings.pixabay_api_key == "pixabay-key"
    assert settings.pages_base_url == "https://user.github.io/stoic-autopilot"
    assert settings.handle == "@estoico"


def test_load_settings_missing_values(monkeypatch):
    for name in ("PIXABAY_API_KEY", "IG_USER_ID", "IG_ACCESS_TOKEN", "PAGES_BASE_URL", "IG_HANDLE"):
        monkeypatch.delenv(name, raising=False)
    settings = load_settings(env_file=None)
    assert settings.ig_user_id is None
    assert settings.pages_base_url is None
    assert settings.handle == ""


def test_require_names_the_missing_setting():
    with pytest.raises(RuntimeError, match="IG_USER_ID"):
        require(None, "IG_USER_ID")
    assert require("x", "IG_USER_ID") == "x"


def test_json_roundtrip_keeps_accents_readable(tmp_path):
    path = tmp_path / "nested" / "data.json"
    write_json(path, {"autor": "Sêneca"})
    assert "Sêneca" in path.read_text(encoding="utf-8")
    assert read_json(path) == {"autor": "Sêneca"}


def test_parse_time_requires_offset():
    assert parse_time("2026-10-19T12:00:00-03:00").utcoffset().total_seconds() == -3 * 3600
    with pytest.raises(ValueError):
        parse_time("2026-10-19T12:00:00")
