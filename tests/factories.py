"""Plain builders shared by tests (import with `from factories import ...`)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from shared.config import Settings

TZ = ZoneInfo("America/Sao_Paulo")
NOW = datetime(2026, 10, 19, 8, 0, tzinfo=TZ)  # Monday 08:00, when the weekly routine runs
SCRIPT = " ".join(["palavra"] * 100)
SETTINGS = Settings(pixabay_api_key="pixabay-key", ig_user_id="17840000", ig_access_token="token",
                    pages_base_url="https://user.github.io/stoic-autopilot", handle="@estoico")


def make_quotes(count=20):
    return [{"id": f"q{n}", "author": "Sêneca", "work": "Cartas a Lucílio", "reference": f"{n}.1",
             "text_pt": f"Citação {n}", "text_source": f"Quote {n}",
             "source_url": "https://en.wikisource.org/wiki/Moral_letters_to_Lucilius"}
            for n in range(1, count + 1)]


def make_reel(n, when):
    return {"id": f"2026-10-19-r{n}", "type": "reel", "scheduled_at": when.isoformat(),
            "pillar": "controle", "hook": f"Gancho {n}", "quote_id": f"q{n}", "script": SCRIPT,
            "footage_keywords": ["calm ocean"], "caption": f"Legenda {n}", "hashtags": ["#estoicismo"],
            "cta": "follow", "platforms": ["instagram", "tiktok"]}


def make_carousel(n, when):
    return {"id": f"2026-10-19-c{n}", "type": "carousel", "scheduled_at": when.isoformat(),
            "pillar": "disciplina",
            "slides": [{"title": f"Slide {s}", "body": "Texto"} for s in range(1, 7)],
            "quote_ids": [f"q{10 + n}"], "caption": f"Carrossel {n}", "hashtags": ["#filosofia"],
            "platforms": ["instagram"]}


def make_week(now=NOW):
    noon = now.replace(hour=12, minute=0)
    evening = now.replace(hour=19, minute=0)
    reels = [make_reel(n, noon + timedelta(days=n - 1)) for n in range(1, 8)]
    carousels = [make_carousel(n, evening + timedelta(days=offset))
                 for n, offset in zip(range(1, 4), (1, 3, 5))]
    return {"week": "2026-10-19", "items": reels + carousels}
