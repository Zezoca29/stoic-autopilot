# Stoic Autopilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pipeline que gera toda semana 7 reels narrados + 3 carrosséis de estoicismo em pt-BR e publica sozinho no Instagram (TikTok em modo manual até a auditoria), a custo zero.

**Architecture:** Repositório Python com três pacotes: `generator/` (roda no PC: TTS → legendas → vídeo de fundo → ffmpeg; carrosséis via HTML → JPEG), `publisher/` (roda no GitHub Actions de hora em hora: lê `queue.json` e publica via Instagram API with Instagram Login) e `shared/` (configuração, fila, tempo). A mídia pendente é servida por GitHub Pages (branch `gh-pages`, reescrito a cada deploy). Uma tarefa agendada do Claude escreve o lote semanal seguindo `ROUTINE.md`.

**Tech Stack:** Python ≥ 3.11, edge-tts ≥ 7.0, ffmpeg ≥ 6 (com libass), Playwright (Chromium), Jinja2, requests, Pillow, pytest, GitHub Actions, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-10-14-stoic-autopilot-design.md`

## Global Constraints

- Python ≥ 3.11 local (Windows, venv em `.venv/`; rodar com `.venv/Scripts/python`), Python 3.12 no Actions.
- ffmpeg ≥ 6 com libass no PATH local (Windows: build Gyan). git ≥ 2.28.
- Fuso: `America/Sao_Paulo`. Todo timestamp é ISO 8601 **com offset** (ex.: `2026-10-19T12:00:00-03:00`).
- Voz TTS fixa: `pt-BR-AntonioNeural`.
- Reel: 1080x1920, 30 fps, H.264 + AAC, 30–60 s, < 100 MB. Trilha a `volume=0.1` (≈ −20 dB).
- Carrossel: 6–8 slides, 1080x1350, **JPEG** (a API do Instagram só aceita JPEG — desvio aprovado do "PNG" do spec).
- Lote: 7 reels às 12:00 + 3 carrosséis às 19:00; slots calculados por `generator.schedule`; lote nomeado pela data do primeiro dia (`YYYY-MM-DD`, desvio do `YYYY-Www` do spec para lidar com rotina atrasada).
- Citações só de `content/quotes.json`; cooldown de citação 60 dias; vídeo de fundo não se repete em 7 dias.
- Pilares válidos: `controle`, `adversidade`, `disciplina`, `emocoes`, `memento_mori`.
- Mídia publicada sai do `gh-pages` no próximo deploy semanal (force-push), não na hora (desvio do spec).
- TikTok automático fica fora deste plano (Fase 5): entradas TikTok nascem com status `manual`.
- Segredos: nunca ler, imprimir ou commitar `.env`, tokens ou chaves. O usuário preenche `.env` e GitHub Secrets.
- Código, identificadores, nomes de arquivo e commits em inglês; textos para o público e docs em pt-BR.
- Toda mensagem de commit termina com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Músicas do Pixabay ficam só locais (`generator/music/*.mp3` no `.gitignore`); a licença proíbe redistribuí-las soltas num repo público.

## Review Focus

1. **Rotina atrasada ou executada duas vezes** (PC desligado na segunda, execução manual extra) → nunca agenda no passado nem duplica semana. Teste: Task 12 (`test_late_run_never_schedules_in_the_past`, `test_skips_when_queue_is_already_full`).
2. **Roteiro/legenda com `{}`, `\` ou emoji** → legenda ASS não quebra nem mostra quadrados. Teste: Task 7 (`test_clean_strips_markup_and_emoji`).
3. **Container do Instagram em `ERROR` ou processando demais** → vira tentativa falha, não trava o workflow. Teste: Task 16 (`test_container_error_status_raises`, `test_container_timeout_raises`) e Task 17 (`test_failures_retry_then_give_up`).
4. **Token da Meta expirado** → falha clara sem gastar as 3 tentativas dos posts. Teste: Task 17 (`test_expired_token_aborts_without_spending_attempts`).
5. **Rodar `build_week` de novo no mesmo lote** (correção após erro) → aceita se nada foi publicado, recusa sobrescrever post publicado. Teste: Task 11 (`test_add_entries_refuses_to_replace_published`) e Task 14 (`test_rebuilding_same_batch_is_allowed`).

---

## File Structure

```
docs/setup/accounts.md          guia da Fase 0 (contas, tokens, segredos)
ROUTINE.md                      instruções da rotina semanal do Claude
README.md                       como instalar e rodar
requirements.txt                dependências locais
requirements-publisher.txt      dependências do Actions
pytest.ini  .gitignore  .env.example
shared/config.py                Settings, constantes globais, caminhos
shared/jsonio.py                read_json / write_json UTF-8
shared/timeutil.py              parse_time / now_local
shared/post_queue.py            fila de publicação (queue.json)
generator/batch.py              carrega e valida estrutura do lote
generator/quotes.py             banco de citações verificadas
generator/history.py            histórico anti-repetição
generator/tts.py                edge-tts → mp3 + tempos por palavra
generator/captions.py           tempos → legendas .ass
generator/footage.py            Pexels + fallback local
generator/media_probe.py        ffprobe
generator/render_reel.py        ffmpeg → reel
generator/render_carousel.py    Jinja2 + Playwright → JPEGs
generator/templates/carousel.html
generator/assets/fallback.mp4   fundo escuro gerado por ffmpeg
generator/music/README.md       como obter trilhas
generator/schedule.py           slots do próximo lote
generator/validate.py           regras pré e pós renderização
generator/build_week.py         orquestra render → valida → fila (+ --preview)
generator/deploy_media.py       monta e publica gh-pages; limpa output/
publisher/instagram.py          cliente da API
publisher/run.py                publica itens vencidos
publisher/refresh_token.py      renova token (nome evita conflito com o módulo stdlib `token`)
site/index.html privacy.html terms.html
.github/workflows/publish.yml  refresh-token.yml
content/quotes.json  content/history.json  content/weeks/*.json  queue.json
tests/factories.py  tests/conftest.py  tests/test_*.py
```

---

### Task 1: Guia de contas (Fase 0)

O usuário começa a criar e "aquecer" as contas enquanto o código é construído.

**Files:**
- Create: `docs/setup/accounts.md`

**Interfaces:**
- Consumes: nada.
- Produces: seção `## 5. Token do Instagram` referenciada pela mensagem de erro de `publisher/run.py` (Task 17).

- [ ] **Step 1: Escrever o guia**

````markdown
# Configuração das contas (Fase 0)

Você executa estes passos; o Claude não cria contas, não digita senhas e não lê tokens.
Comece pelo Instagram hoje: a conta precisa de 5–7 dias de uso manual antes da automação.
As telas da Meta e do TikTok mudam com frequência — se um nome de menu não bater, procure pelo termo equivalente.

## 1. Instagram
1. Crie uma conta nova (e-mail dedicado ao projeto).
2. Foto, nome e bio. Bio sugerida: "Estoicismo para a vida real. Sêneca, Marco Aurélio, Epicteto. Narração com voz sintética. 📚 Livros ↓"
3. Configurações → Tipo de conta → **Mudar para conta profissional → Criador**. Categoria: "Educação" ou "Autor".
4. Aquecimento (5–7 dias): siga ~30 perfis do nicho, curta e comente de verdade, poste 2–3 vezes manualmente.

## 2. TikTok
1. Crie a conta com o mesmo nome do Instagram, foto e bio iguais.
2. Até a Fase 5 os reels são enviados por você: eles ficam em `output/<id>/reel.mp4`. Dá para agendar até 10 dias à frente pelo TikTok Studio na web.

## 3. GitHub
1. Crie uma conta em github.com (se ainda não tiver).
2. O repositório público `stoic-autopilot` é criado na Task 21, com sua aprovação.

## 4. Pexels
1. Crie conta em https://www.pexels.com e peça a chave em https://www.pexels.com/api/ (gratuita).
2. Guarde para colocar no `.env` (seção 7).

## 5. Token do Instagram
1. Em https://developers.facebook.com crie um app (tipo **Business**) e adicione o produto/caso de uso de **Instagram** com **"API setup with Instagram login"** (Instagram API com login do Instagram — não precisa de Página do Facebook).
2. Permissões necessárias: `instagram_business_basic` e `instagram_business_content_publish`.
3. Em "Generate access tokens", clique em **Add account** e entre com a conta do projeto. Se pedir, adicione a conta em Funções do app → Testadores do Instagram e aceite o convite no app do Instagram (Configurações → Apps e sites).
4. Copie o **token** (vale 60 dias; a renovação automática roda toda segunda) e o **ID da conta Instagram** mostrado ao lado.
5. Mantenha o app em modo Desenvolvimento: como a conta é sua e tem função no app, não precisa de App Review.
6. Se o workflow `publish` falhar com "token invalid or expired": repita os passos 3–4 e atualize o secret `IG_ACCESS_TOKEN` (seção 7).

## 6. Token do GitHub para renovar o segredo
1. github.com → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate.
2. Repository access: só `stoic-autopilot`. Permissions → Repository → **Secrets: Read and write**. Validade: 1 ano.

## 7. Onde colocar cada valor
- Arquivo local `.env` (copie de `.env.example`): `PEXELS_API_KEY`, `IG_USER_ID`, `IG_ACCESS_TOKEN`, `PAGES_BASE_URL`, `IG_HANDLE`.
- GitHub → repositório → Settings → Secrets and variables → Actions:
  - **Secrets:** `IG_USER_ID`, `IG_ACCESS_TOKEN`, `GH_SECRETS_PAT` (token da seção 6).
  - **Variables:** `PAGES_BASE_URL` = `https://SEU_USUARIO.github.io/stoic-autopilot`.

## 8. Músicas
Baixe 3–5 trilhas calmas (ex.: busque "ambient piano", "cinematic calm") em https://pixabay.com/music/ e salve como `.mp3` em `generator/music/`. Elas ficam só no seu PC.

## 9. App do TikTok (depois que o site estiver no ar — Task 21)
1. Em https://developers.tiktok.com crie um app e adicione **Content Posting API** (Direct Post).
2. Use as páginas `.../privacy.html` e `.../terms.html` do seu GitHub Pages.
3. Envie para auditoria. Aviso honesto: o TikTok exige uma interface onde o criador escolhe privacidade e confirma o post; automação sem interface costuma ser recusada. Se for recusada, o upload manual continua sendo o caminho.
````

- [ ] **Step 2: Commit**

```bash
git add docs/setup/accounts.md
git commit -m "docs: add account setup guide"
```

---

### Task 2: Scaffold e módulo `shared`

**Files:**
- Create: `requirements.txt`, `requirements-publisher.txt`, `pytest.ini`, `.gitignore`, `.env.example`, `README.md`
- Create: `shared/__init__.py`, `shared/config.py`, `shared/jsonio.py`, `shared/timeutil.py`, `generator/__init__.py`, `publisher/__init__.py`
- Test: `tests/test_shared.py`

**Interfaces:**
- Produces:
  - `shared.config`: `ROOT: Path`, `OUTPUT_DIR: Path`, `TIMEZONE = "America/Sao_Paulo"`, `VOICE = "pt-BR-AntonioNeural"`, `Settings(pexels_api_key, ig_user_id, ig_access_token, pages_base_url, handle)`, `load_settings(env_file: Path | None = ROOT / ".env") -> Settings`, `require(value: str | None, name: str) -> str`
  - `shared.jsonio`: `read_json(path) -> Any`, `write_json(path, data) -> None`
  - `shared.timeutil`: `parse_time(value: str) -> datetime`, `now_local() -> datetime`

- [ ] **Step 1: Arquivos de projeto**

`requirements.txt`:
```
edge-tts>=7.0
requests>=2.32
jinja2>=3.1
playwright>=1.45
python-dotenv>=1.0
pillow>=10.0
tzdata>=2024.1
pytest>=8.0
```

`requirements-publisher.txt`:
```
requests>=2.32
python-dotenv>=1.0
tzdata>=2024.1
```

`pytest.ini`:
```ini
[pytest]
testpaths = tests
pythonpath = .
addopts = -m "not network"
markers =
    network: calls real external services (edge-tts); run with -m network
```

`.gitignore`:
```
.env
.venv/
output/
__pycache__/
.pytest_cache/
*.pyc
generator/music/*.mp3
```

`.env.example`:
```
# Copie para .env e preencha você mesmo. Nunca commite o .env.
PEXELS_API_KEY=
IG_USER_ID=
IG_ACCESS_TOKEN=
PAGES_BASE_URL=https://SEU_USUARIO.github.io/stoic-autopilot
IG_HANDLE=@seu_perfil
```

`README.md`:
````markdown
# Stoic Autopilot

Gera e publica automaticamente reels e carrosséis de estoicismo. Design: `docs/superpowers/specs/2026-10-14-stoic-autopilot-design.md`. Contas: `docs/setup/accounts.md`. Rotina semanal: `ROUTINE.md`.

## Instalação (Windows, Git Bash)
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m playwright install chromium
```
ffmpeg precisa estar no PATH (`winget install --id Gyan.FFmpeg -e`).

## Comandos
- Testes: `.venv/Scripts/python -m pytest`
- Slots do próximo lote: `.venv/Scripts/python -m generator.schedule`
- Renderizar e enfileirar lote: `.venv/Scripts/python -m generator.build_week content/weeks/<lote>.json`
- Pré-visualizar um item: `... -m generator.build_week <lote.json> --preview <id>`
- Publicar mídia no GitHub Pages: `.venv/Scripts/python -m generator.deploy_media`
- Simular publicação: `.venv/Scripts/python -m publisher.run --dry-run --now 2026-10-25T23:00:00-03:00`
````

Arquivos `__init__.py` vazios em `shared/`, `generator/`, `publisher/`.

- [ ] **Step 2: Instalar ambiente**

Run: `python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt && .venv/Scripts/python -m playwright install chromium`
Run: `ffmpeg -version` — se não existir, **pedir ao usuário** para rodar `winget install --id Gyan.FFmpeg -e` (instalação no sistema) e reabrir o terminal.

- [ ] **Step 3: Escrever o teste que falha**

`tests/test_shared.py`:
```python
import pytest

from shared.config import load_settings, require
from shared.jsonio import read_json, write_json
from shared.timeutil import parse_time


def test_load_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("PEXELS_API_KEY", "pexels-key")
    monkeypatch.setenv("PAGES_BASE_URL", "https://user.github.io/stoic-autopilot/")
    monkeypatch.setenv("IG_HANDLE", "@estoico")
    settings = load_settings(env_file=None)
    assert settings.pexels_api_key == "pexels-key"
    assert settings.pages_base_url == "https://user.github.io/stoic-autopilot"
    assert settings.handle == "@estoico"


def test_load_settings_missing_values(monkeypatch):
    for name in ("PEXELS_API_KEY", "IG_USER_ID", "IG_ACCESS_TOKEN", "PAGES_BASE_URL", "IG_HANDLE"):
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
```

- [ ] **Step 4: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_shared.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'shared.config'`

- [ ] **Step 5: Implementar**

`shared/config.py`:
```python
"""Runtime configuration: constants plus settings from .env locally or GitHub Secrets in CI."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
TIMEZONE = "America/Sao_Paulo"
VOICE = "pt-BR-AntonioNeural"


@dataclass(frozen=True)
class Settings:
    pexels_api_key: str | None
    ig_user_id: str | None
    ig_access_token: str | None
    pages_base_url: str | None
    handle: str


def load_settings(env_file: Path | None = ROOT / ".env") -> Settings:
    if env_file is not None and Path(env_file).exists():
        load_dotenv(env_file, override=False)
    return Settings(
        pexels_api_key=os.getenv("PEXELS_API_KEY") or None,
        ig_user_id=os.getenv("IG_USER_ID") or None,
        ig_access_token=os.getenv("IG_ACCESS_TOKEN") or None,
        pages_base_url=(os.getenv("PAGES_BASE_URL") or "").rstrip("/") or None,
        handle=os.getenv("IG_HANDLE", ""),
    )


def require(value: str | None, name: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required setting {name}; set it in .env or GitHub Secrets")
    return value
```

`shared/jsonio.py`:
```python
"""UTF-8 JSON helpers that keep accents readable in committed files."""
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

`shared/timeutil.py`:
```python
"""Timezone-aware time helpers; every timestamp in the project carries a UTC offset."""
from datetime import datetime
from zoneinfo import ZoneInfo

from shared.config import TIMEZONE


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp without UTC offset: {value}")
    return parsed


def now_local() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))
```

- [ ] **Step 6: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_shared.py -v`
Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "chore: scaffold project and shared config"
```

---

### Task 3: Lote semanal (`generator/batch.py`) + fixtures de teste

**Files:**
- Create: `generator/batch.py`, `tests/factories.py`, `tests/conftest.py`
- Test: `tests/test_batch.py`

**Interfaces:**
- Consumes: `shared.jsonio.read_json`, `shared.timeutil.parse_time`, `shared.config.Settings`
- Produces:
  - `generator.batch`: `PILLARS: set[str]`, `BatchError(ValueError)`, `load_batch(path) -> dict`, `check_structure(data) -> list[str]`, `quote_ids_of(item: dict) -> list[str]`
  - `tests/factories.py`: `TZ`, `NOW` (segunda 2026-10-19 08:00 −03:00), `SCRIPT` (100 palavras), `SETTINGS`, `make_quotes(count=20) -> list[dict]` (ids `q1`…), `make_reel(n, when) -> dict` (id `2026-10-19-r{n}`, `quote_id` `q{n}`), `make_carousel(n, when) -> dict` (id `2026-10-19-c{n}`, `quote_ids` `[q{10+n}]`, 6 slides), `make_week(now=NOW) -> dict` (7 reels Seg–Dom 12:00; 3 carrosséis 19:00 em Ter/Qui/Sáb)
  - `tests/conftest.py`: fixtures `week`, `quotes` (dict id → quote)

- [ ] **Step 1: Fixtures**

`tests/factories.py`:
```python
"""Plain builders shared by tests (import with `from factories import ...`)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from shared.config import Settings

TZ = ZoneInfo("America/Sao_Paulo")
NOW = datetime(2026, 10, 19, 8, 0, tzinfo=TZ)  # Monday 08:00, when the weekly routine runs
SCRIPT = " ".join(["palavra"] * 100)
SETTINGS = Settings(pexels_api_key="pexels-key", ig_user_id="17840000", ig_access_token="token",
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
```

`tests/conftest.py`:
```python
import pytest

from factories import make_quotes, make_week


@pytest.fixture
def week():
    return make_week()


@pytest.fixture
def quotes():
    return {quote["id"]: quote for quote in make_quotes()}
```

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_batch.py`:
```python
import json

import pytest

from generator.batch import BatchError, check_structure, load_batch, quote_ids_of


def test_valid_week_has_no_errors(week):
    assert check_structure(week) == []


def test_load_batch_reports_missing_fields(tmp_path, week):
    del week["items"][0]["script"]
    path = tmp_path / "batch.json"
    path.write_text(json.dumps(week), encoding="utf-8")
    with pytest.raises(BatchError, match=r"2026-10-19-r1: missing fields \['script'\]"):
        load_batch(path)


def test_unknown_type_and_duplicate_id(week):
    week["items"][1]["type"] = "story"
    week["items"][2]["id"] = week["items"][0]["id"]
    errors = check_structure(week)
    assert "2026-10-19-r2: unknown type 'story'" in errors
    assert "2026-10-19-r1: duplicate id" in errors


def test_scheduled_at_needs_offset(week):
    week["items"][0]["scheduled_at"] = "2026-10-19T12:00:00"
    assert "2026-10-19-r1: scheduled_at must be ISO 8601 with UTC offset" in check_structure(week)


def test_platform_rules(week):
    week["items"][0]["platforms"] = ["tiktok"]
    week["items"][7]["platforms"] = ["instagram", "tiktok"]
    errors = check_structure(week)
    assert "2026-10-19-r1: instagram is required" in errors
    assert "2026-10-19-c1: carousels are Instagram-only" in errors


def test_bad_pillar_and_cta(week):
    week["items"][0]["pillar"] = "felicidade"
    week["items"][1]["cta"] = "buy"
    errors = check_structure(week)
    assert any(e.startswith("2026-10-19-r1: pillar must be one of") for e in errors)
    assert any(e.startswith("2026-10-19-r2: cta must be one of") for e in errors)


def test_empty_items_rejected():
    assert check_structure({"week": "x", "items": []}) == ["items must be a non-empty list"]


def test_quote_ids_of(week):
    assert quote_ids_of(week["items"][0]) == ["q1"]
    assert quote_ids_of(week["items"][7]) == ["q11"]
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_batch.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.batch'`

- [ ] **Step 4: Implementar**

`generator/batch.py`:
```python
"""Load and structurally check a weekly content batch written by the Claude routine."""
from pathlib import Path

from shared.jsonio import read_json
from shared.timeutil import parse_time

PILLARS = {"controle", "adversidade", "disciplina", "emocoes", "memento_mori"}
PLATFORMS = {"instagram", "tiktok"}
CTAS = {"follow", "save", "affiliate"}
REQUIRED_FIELDS = {
    "reel": {"id", "type", "scheduled_at", "pillar", "hook", "quote_id", "script",
             "footage_keywords", "caption", "hashtags", "cta", "platforms"},
    "carousel": {"id", "type", "scheduled_at", "pillar", "slides", "quote_ids",
                 "caption", "hashtags", "platforms"},
}


class BatchError(ValueError):
    """The batch file is malformed and cannot be rendered."""


def load_batch(path: Path) -> dict:
    data = read_json(path)
    errors = check_structure(data)
    if errors:
        raise BatchError("; ".join(errors))
    return data


def check_structure(data) -> list[str]:
    if not isinstance(data, dict):
        return ["batch must be a JSON object"]
    errors = []
    if not isinstance(data.get("week"), str) or not data["week"]:
        errors.append("week must be a non-empty string")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["items must be a non-empty list"]
    seen = set()
    for index, item in enumerate(items):
        errors.extend(_check_item(item, index, seen))
    return errors


def _check_item(item, index, seen) -> list[str]:
    if not isinstance(item, dict):
        return [f"items[{index}]: must be an object"]
    label = item.get("id") or f"items[{index}]"
    required = REQUIRED_FIELDS.get(item.get("type"))
    if required is None:
        return [f"{label}: unknown type {item.get('type')!r}"]
    errors = []
    missing = sorted(required - item.keys())
    if missing:
        errors.append(f"{label}: missing fields {missing}")
    if label in seen:
        errors.append(f"{label}: duplicate id")
    seen.add(label)
    if item.get("pillar") not in PILLARS:
        errors.append(f"{label}: pillar must be one of {sorted(PILLARS)}")
    try:
        parse_time(item.get("scheduled_at"))
    except (TypeError, ValueError):
        errors.append(f"{label}: scheduled_at must be ISO 8601 with UTC offset")
    platforms = item.get("platforms")
    if not isinstance(platforms, list) or not platforms or not set(platforms) <= PLATFORMS:
        errors.append(f"{label}: platforms must be a non-empty subset of {sorted(PLATFORMS)}")
    elif "instagram" not in platforms:
        errors.append(f"{label}: instagram is required")
    elif item["type"] == "carousel" and platforms != ["instagram"]:
        errors.append(f"{label}: carousels are Instagram-only")
    if item["type"] == "reel" and item.get("cta") not in CTAS:
        errors.append(f"{label}: cta must be one of {sorted(CTAS)}")
    return errors


def quote_ids_of(item: dict) -> list[str]:
    return [item["quote_id"]] if item["type"] == "reel" else list(item["quote_ids"])
```

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_batch.py -v`
Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
git add generator/batch.py tests/
git commit -m "feat: load and check weekly batch structure"
```

---

### Task 4: Banco de citações (`generator/quotes.py`)

**Files:**
- Create: `generator/quotes.py`, `content/quotes.json` (conteúdo inicial `[]`; populado na Task 20)
- Test: `tests/test_quotes.py`

**Interfaces:**
- Consumes: `shared.config.ROOT`, `shared.jsonio`
- Produces: `QUOTES_PATH`, `QUOTE_FIELDS`, `check_quotes(data) -> list[str]`, `load_quotes(path=QUOTES_PATH) -> dict[str, dict]`, `display_reference(quote) -> str` (ex.: `"Sêneca, Cartas a Lucílio 13.4"`), CLI `python -m generator.quotes`

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_quotes.py`:
```python
import pytest

from factories import make_quotes
from generator.quotes import check_quotes, display_reference, load_quotes
from shared.jsonio import write_json


def test_valid_bank_loads_by_id(tmp_path):
    path = tmp_path / "quotes.json"
    write_json(path, make_quotes(3))
    assert sorted(load_quotes(path)) == ["q1", "q2", "q3"]


def test_missing_field_and_bad_url():
    data = make_quotes(2)
    data[0]["reference"] = " "
    data[1]["source_url"] = "http://example.com"
    errors = check_quotes(data)
    assert "q1: missing reference" in errors
    assert "q2: source_url must be an https URL" in errors


def test_duplicate_id():
    data = make_quotes(2)
    data[1]["id"] = "q1"
    assert "q1: duplicate id" in check_quotes(data)


def test_invalid_bank_raises(tmp_path):
    path = tmp_path / "quotes.json"
    write_json(path, [{"id": "x"}])
    with pytest.raises(ValueError, match="x: missing author"):
        load_quotes(path)


def test_display_reference():
    assert display_reference(make_quotes(1)[0]) == "Sêneca, Cartas a Lucílio 1.1"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_quotes.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.quotes'`

- [ ] **Step 3: Implementar**

`generator/quotes.py`:
```python
"""Verified quote bank: the only source of quotes the pipeline may publish."""
import sys
from pathlib import Path

from shared.config import ROOT
from shared.jsonio import read_json

QUOTES_PATH = ROOT / "content" / "quotes.json"
QUOTE_FIELDS = ("id", "author", "work", "reference", "text_pt", "text_source", "source_url")


def check_quotes(data) -> list[str]:
    if not isinstance(data, list):
        return ["quotes.json must be a JSON list"]
    errors, seen = [], set()
    for index, quote in enumerate(data):
        label = quote.get("id") or f"quotes[{index}]"
        for field in QUOTE_FIELDS:
            value = quote.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}: missing {field}")
        if not str(quote.get("source_url", "")).startswith("https://"):
            errors.append(f"{label}: source_url must be an https URL")
        if label in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(label)
    return errors


def load_quotes(path: Path = QUOTES_PATH) -> dict[str, dict]:
    data = read_json(path)
    errors = check_quotes(data)
    if errors:
        raise ValueError("; ".join(errors))
    return {quote["id"]: quote for quote in data}


def display_reference(quote: dict) -> str:
    return f"{quote['author']}, {quote['work']} {quote['reference']}"


def main() -> int:
    data = read_json(QUOTES_PATH)
    errors = check_quotes(data)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"{len(data)} quotes, {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

`content/quotes.json`:
```json
[]
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_quotes.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add generator/quotes.py content/quotes.json tests/test_quotes.py
git commit -m "feat: add verified quote bank loader"
```

---

### Task 5: Histórico anti-repetição (`generator/history.py`)

**Files:**
- Create: `generator/history.py`
- Test: `tests/test_history.py`

**Interfaces:**
- Produces: `HISTORY_PATH`, `QUOTE_COOLDOWN_DAYS = 60`, `FOOTAGE_COOLDOWN_DAYS = 7`, `load_history(path=HISTORY_PATH) -> dict`, `save_history(path, history)`, `quote_on_cooldown(history, quote_id, on: date, item_id: str) -> bool`, `recent_footage(history, on: date) -> set[str]`, `record_use(history, *, item_id, quote_ids, footage_ids, on: date) -> None`
- Formato: `{"quotes": {"q1": {"on": "2026-10-19", "item": "2026-10-19-r1"}}, "footage": {"pexels:123": {"on": "...", "item": "..."}}}`. Guardar o `item` permite re-renderizar o mesmo lote sem acusar cooldown.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_history.py`:
```python
from datetime import date

from generator.history import load_history, quote_on_cooldown, recent_footage, record_use


def empty():
    return {"quotes": {}, "footage": {}}


def test_missing_history_is_empty(tmp_path):
    assert load_history(tmp_path / "none.json") == empty()


def test_quote_cooldown_is_60_days():
    history = empty()
    record_use(history, item_id="a", quote_ids=["q1"], footage_ids=[], on=date(2026, 10, 1))
    assert quote_on_cooldown(history, "q1", date(2026, 11, 29), "b")      # 59 days later
    assert not quote_on_cooldown(history, "q1", date(2026, 11, 30), "b")  # 60 days later
    assert not quote_on_cooldown(history, "q2", date(2026, 10, 2), "b")


def test_same_item_can_reuse_its_quote():
    history = empty()
    record_use(history, item_id="a", quote_ids=["q1"], footage_ids=[], on=date(2026, 10, 1))
    assert not quote_on_cooldown(history, "q1", date(2026, 10, 1), "a")


def test_recent_footage_window():
    history = empty()
    record_use(history, item_id="a", quote_ids=[], footage_ids=["pexels:1"], on=date(2026, 10, 1))
    record_use(history, item_id="b", quote_ids=[], footage_ids=["pexels:2"], on=date(2026, 10, 10))
    assert recent_footage(history, date(2026, 10, 7)) == {"pexels:1", "pexels:2"}
    assert recent_footage(history, date(2026, 10, 8)) == {"pexels:2"}
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_history.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.history'`

- [ ] **Step 3: Implementar**

`generator/history.py`:
```python
"""Usage history that keeps quotes and background footage from repeating too soon."""
from datetime import date
from pathlib import Path

from shared.config import ROOT
from shared.jsonio import read_json, write_json

HISTORY_PATH = ROOT / "content" / "history.json"
QUOTE_COOLDOWN_DAYS = 60
FOOTAGE_COOLDOWN_DAYS = 7


def load_history(path: Path = HISTORY_PATH) -> dict:
    if not Path(path).exists():
        return {"quotes": {}, "footage": {}}
    return read_json(path)


def save_history(path: Path, history: dict) -> None:
    write_json(path, history)


def _within(used_on: str, on: date, days: int) -> bool:
    return abs((on - date.fromisoformat(used_on)).days) < days


def quote_on_cooldown(history: dict, quote_id: str, on: date, item_id: str) -> bool:
    use = history["quotes"].get(quote_id)
    return use is not None and use["item"] != item_id and _within(use["on"], on, QUOTE_COOLDOWN_DAYS)


def recent_footage(history: dict, on: date) -> set[str]:
    return {footage_id for footage_id, use in history["footage"].items()
            if _within(use["on"], on, FOOTAGE_COOLDOWN_DAYS)}


def record_use(history: dict, *, item_id: str, quote_ids: list[str], footage_ids: list[str], on: date) -> None:
    for quote_id in quote_ids:
        history["quotes"][quote_id] = {"on": on.isoformat(), "item": item_id}
    for footage_id in footage_ids:
        history["footage"][footage_id] = {"on": on.isoformat(), "item": item_id}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_history.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add generator/history.py tests/test_history.py
git commit -m "feat: track quote and footage usage history"
```

---

### Task 6: Narração (`generator/tts.py`)

**Files:**
- Create: `generator/tts.py`
- Test: `tests/test_tts.py`

**Interfaces:**
- Consumes: `shared.config.VOICE`
- Produces: `Word(text: str, start: float, end: float)` (segundos, frozen dataclass), `TTSError(RuntimeError)`, `synthesize(text, out_path, voice=VOICE, retries=3, wait_seconds=5.0, communicate_factory=..., sleep=time.sleep) -> list[Word]`

Nota: a partir do edge-tts 7.0 o padrão é `SentenceBoundary`; por isso passamos `boundary="WordBoundary"`. Se aparecer `TypeError: unexpected keyword 'boundary'`, a versão instalada é < 7 — atualize (`pip install -U edge-tts`).

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_tts.py`:
```python
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


def test_synthesize_gives_up_after_three_attempts(tmp_path):
    def broken(text, voice):
        raise ConnectionError("down")

    with pytest.raises(TTSError, match="after 3 attempts"):
        synthesize("x", tmp_path / "n.mp3", communicate_factory=broken, sleep=no_sleep)


def test_no_word_boundaries_is_an_error(tmp_path):
    with pytest.raises(TTSError, match="no word timings"):
        synthesize("x", tmp_path / "n.mp3", communicate_factory=SilentCommunicate, sleep=no_sleep)


@pytest.mark.network
def test_real_edge_tts(tmp_path):
    words = synthesize("Você sofre mais na imaginação do que na realidade.", tmp_path / "n.mp3")
    assert len(words) >= 6
    assert (tmp_path / "n.mp3").stat().st_size > 1000
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_tts.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.tts'`

- [ ] **Step 3: Implementar**

`generator/tts.py`:
```python
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_tts.py -v`
Expected: 4 passed, 1 deselected

Run (confere a voz real): `.venv/Scripts/python -m pytest tests/test_tts.py -m network -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add generator/tts.py tests/test_tts.py
git commit -m "feat: synthesize narration with word timings"
```

---

### Task 7: Legendas animadas (`generator/captions.py`)

**Files:**
- Create: `generator/captions.py`
- Test: `tests/test_captions.py`

**Interfaces:**
- Consumes: `generator.tts.Word`
- Produces: `format_time(seconds) -> str`, `clean(text) -> str`, `caption_events(words) -> list[str]`, `build_ass(words, reference: str, total_duration: float) -> str`, `write_ass(path, words, reference, total_duration) -> None`

Visual: blocos de até 3 palavras no centro, palavra falada em dourado `#D4AF37` (ASS `&H0037AFD4&`); referência da citação no topo durante todo o vídeo.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_captions.py`:
```python
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
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_captions.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.captions'`

- [ ] **Step 3: Implementar**

`generator/captions.py`:
```python
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
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_captions.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add generator/captions.py tests/test_captions.py
git commit -m "feat: build word-highlight ASS captions"
```

---

### Task 8: Vídeo de fundo (`generator/footage.py`)

**Files:**
- Create: `generator/footage.py`, `generator/assets/fallback.mp4`
- Test: `tests/test_footage.py`

**Interfaces:**
- Consumes: `shared.config.ROOT`
- Produces: `SEARCH_URL`, `FALLBACK_VIDEO`, `FALLBACK_KEYWORDS: dict[pillar, list[str]]`, `FootageError(RuntimeError)`, `choose_file(video) -> dict | None`, `pick_video(keywords, pillar, exclude_ids, api_key, session) -> tuple[str, str]`, `fetch_footage(keywords, pillar, exclude_ids, out_path, api_key, session=None) -> str` (retorna `"pexels:<id>"` ou `"fallback"`)

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_footage.py`:
```python
import requests

from generator import footage
from generator.footage import choose_file, fetch_footage, pick_video


class FakeResponse:
    def __init__(self, payload=None, content=b""):
        self.payload, self.content = payload, content

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload

    def iter_content(self, chunk_size):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, results_by_query):
        self.results_by_query = results_by_query
        self.queries = []

    def get(self, url, params=None, headers=None, timeout=None, stream=False):
        if url == footage.SEARCH_URL:
            self.queries.append(params["query"])
            return FakeResponse({"videos": self.results_by_query.get(params["query"], [])})
        return FakeResponse(content=b"video-bytes")


def video(vid, duration=15, files=None):
    if files is None:
        files = [{"file_type": "video/mp4", "width": 720, "height": 1280, "link": f"https://cdn/{vid}-720.mp4"},
                 {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": f"https://cdn/{vid}-1080.mp4"},
                 {"file_type": "video/mp4", "width": 1920, "height": 1080, "link": f"https://cdn/{vid}-land.mp4"}]
    return {"id": vid, "duration": duration, "video_files": files}


def test_choose_file_prefers_portrait_closest_to_1920():
    assert choose_file(video(1))["link"] == "https://cdn/1-1080.mp4"


def test_choose_file_none_without_portrait():
    landscape = [{"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "x"}]
    assert choose_file(video(1, files=landscape)) is None


def test_pick_video_skips_excluded_and_short_clips():
    session = FakeSession({"calm ocean": [video(1), video(2, duration=5), video(3)]})
    assert pick_video(["calm ocean"], "controle", {"pexels:1"}, "key", session) == \
        ("pexels:3", "https://cdn/3-1080.mp4")


def test_pick_video_falls_back_to_pillar_keywords():
    session = FakeSession({"mountain fog": [video(9)]})
    assert pick_video(["nothing"], "controle", set(), "key", session)[0] == "pexels:9"
    assert session.queries == ["nothing", "calm ocean", "mountain fog"]


def test_fetch_footage_downloads(tmp_path):
    session = FakeSession({"calm ocean": [video(1)]})
    out = tmp_path / "bg.mp4"
    assert fetch_footage(["calm ocean"], "controle", set(), out, "key", session=session) == "pexels:1"
    assert out.read_bytes() == b"video-bytes"


def test_fetch_footage_uses_local_fallback_when_pexels_fails(tmp_path, monkeypatch):
    fallback = tmp_path / "fallback.mp4"
    fallback.write_bytes(b"fallback")
    monkeypatch.setattr(footage, "FALLBACK_VIDEO", fallback)

    class Down(FakeSession):
        def get(self, *args, **kwargs):
            raise requests.ConnectionError("down")

    out = tmp_path / "bg.mp4"
    assert fetch_footage(["x"], "controle", set(), out, "key", session=Down({})) == "fallback"
    assert out.read_bytes() == b"fallback"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_footage.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.footage'`

- [ ] **Step 3: Implementar**

`generator/footage.py`:
```python
"""Background footage from the Pexels API, with a local fallback clip."""
import shutil
from pathlib import Path

import requests

from shared.config import ROOT

SEARCH_URL = "https://api.pexels.com/videos/search"
MIN_CLIP_SECONDS = 8
TARGET_HEIGHT = 1920
FALLBACK_VIDEO = ROOT / "generator" / "assets" / "fallback.mp4"
FALLBACK_KEYWORDS = {
    "controle": ["calm ocean", "mountain fog"],
    "adversidade": ["storm waves", "rain window"],
    "disciplina": ["running sunrise", "ancient columns"],
    "emocoes": ["candle flame", "clouds timelapse"],
    "memento_mori": ["marble statue", "hourglass"],
}


class FootageError(RuntimeError):
    """No usable background video could be obtained."""


def choose_file(video: dict) -> dict | None:
    portrait = [f for f in video.get("video_files", [])
                if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")
                and f["height"] > f["width"]]
    return min(portrait, key=lambda f: abs(f["height"] - TARGET_HEIGHT), default=None)


def search(keyword: str, api_key: str, session) -> list[dict]:
    response = session.get(SEARCH_URL, params={"query": keyword, "orientation": "portrait", "per_page": 15},
                           headers={"Authorization": api_key}, timeout=30)
    response.raise_for_status()
    return response.json().get("videos", [])


def pick_video(keywords, pillar, exclude_ids, api_key, session) -> tuple[str, str]:
    for keyword in [*keywords, *FALLBACK_KEYWORDS[pillar]]:
        for video in search(keyword, api_key, session):
            footage_id = f"pexels:{video['id']}"
            if footage_id in exclude_ids or video.get("duration", 0) < MIN_CLIP_SECONDS:
                continue
            chosen = choose_file(video)
            if chosen:
                return footage_id, chosen["link"]
    raise FootageError(f"no portrait Pexels video for {keywords} or pillar {pillar}")


def download(url: str, out_path: Path, session) -> None:
    with session.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(out_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1 << 20):
                file.write(chunk)


def fetch_footage(keywords, pillar, exclude_ids, out_path, api_key, session=None) -> str:
    """Save a background clip to out_path; returns 'pexels:<id>' or 'fallback'."""
    session = session or requests.Session()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        footage_id, url = pick_video(keywords, pillar, exclude_ids, api_key, session)
        download(url, out_path, session)
        return footage_id
    except (FootageError, requests.RequestException):
        if not FALLBACK_VIDEO.exists():
            raise FootageError(f"Pexels unavailable and {FALLBACK_VIDEO} is missing")
        shutil.copyfile(FALLBACK_VIDEO, out_path)
        return "fallback"
```

- [ ] **Step 4: Gerar o clipe de fallback (fundo escuro, 10 s)**

Run: `mkdir -p generator/assets && ffmpeg -y -v error -f lavfi -i "color=c=0x14110f:s=1080x1920:r=30:d=10" -c:v libx264 -pix_fmt yuv420p generator/assets/fallback.mp4`
Expected: arquivo `generator/assets/fallback.mp4` criado (poucos KB).

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_footage.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add generator/footage.py generator/assets/fallback.mp4 tests/test_footage.py
git commit -m "feat: fetch Pexels background footage with fallback"
```

---

### Task 9: Renderização do reel (`generator/render_reel.py`, `generator/media_probe.py`)

**Files:**
- Create: `generator/render_reel.py`, `generator/media_probe.py`, `generator/music/README.md`
- Test: `tests/test_render_reel.py`

**Interfaces:**
- Consumes: `tts.synthesize(text, out_path) -> list[Word]`, `footage.fetch_footage(keywords, pillar, exclude_ids, out_path, api_key) -> str`, `captions.write_ass`, `quotes.display_reference`
- Produces:
  - `generator.media_probe`: `MediaInfo(width, height, duration, size_bytes)`, `probe(path) -> MediaInfo`
  - `generator.render_reel`: `MUSIC_DIR`, `RenderError(RuntimeError)`, `pick_music(item_id, music_dir=None) -> Path | None`, `build_ffmpeg_cmd(background, narration, music, subtitles_name, duration, out_path) -> list[str]`, `render_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage, synthesize=..., fetch=..., run=subprocess.run) -> str` (footage id)

O ffmpeg roda com `cwd=work_dir` e referencia `subs.ass` por nome relativo: caminhos do Windows (`C:\...`) quebram a sintaxe do filtro `ass=`.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_render_reel.py`:
```python
import shutil
import subprocess

import pytest

from factories import NOW, make_quotes, make_reel
from generator import render_reel as rr
from generator.media_probe import probe
from generator.tts import Word

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def test_ffmpeg_cmd_with_music_mixes_two_audio_inputs(tmp_path):
    cmd = rr.build_ffmpeg_cmd(tmp_path / "bg.mp4", tmp_path / "n.mp3", tmp_path / "m.mp3", "subs.ass", 42.5,
                              tmp_path / "out.mp4")
    graph = cmd[cmd.index("-filter_complex") + 1]
    assert "ass=subs.ass" in graph
    assert "[2:a]volume=0.1[m];[1:a][m]amix=inputs=2:duration=longest:normalize=0[a]" in graph
    assert cmd[cmd.index("-t") + 1] == "42.50"
    assert cmd.count("-stream_loop") == 2


def test_ffmpeg_cmd_without_music_pads_narration(tmp_path):
    cmd = rr.build_ffmpeg_cmd(tmp_path / "bg.mp4", tmp_path / "n.mp3", None, "subs.ass", 30.0,
                              tmp_path / "out.mp4")
    assert cmd[cmd.index("-filter_complex") + 1].endswith("[1:a]apad[a]")
    assert cmd.count("-stream_loop") == 1


def test_pick_music_is_deterministic(tmp_path):
    for name in ("a.mp3", "b.mp3", "c.mp3"):
        (tmp_path / name).write_bytes(b"")
    assert rr.pick_music("id-1", tmp_path) == rr.pick_music("id-1", tmp_path)
    assert rr.pick_music("id-1", tmp_path / "empty") is None


def test_render_reel_reports_ffmpeg_stderr(tmp_path):
    def fake_synth(text, out_path):
        out_path.write_bytes(b"")
        return [Word("a", 0.0, 1.0)]

    def fake_fetch(keywords, pillar, exclude, out_path, api_key):
        return "pexels:1"

    def failing_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, "", "Invalid data found")

    with pytest.raises(rr.RenderError, match="Invalid data found"):
        rr.render_reel(make_reel(1, NOW), make_quotes(1)[0], tmp_path / "work", tmp_path / "reel.mp4",
                       api_key="k", exclude_footage=set(), synthesize=fake_synth, fetch=fake_fetch,
                       run=failing_run)


@needs_ffmpeg
def test_render_reel_produces_vertical_video(tmp_path, monkeypatch):
    monkeypatch.setattr(rr, "MUSIC_DIR", tmp_path / "no-music")
    source = tmp_path / "source.mp4"
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=720x1280:rate=30:duration=3", "-pix_fmt", "yuv420p", str(source))

    def fake_synth(text, out_path):
        ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=4", str(out_path))
        return [Word("Você", 0.0, 0.5), Word("sofre", 0.6, 1.2), Word("mais", 1.3, 4.0)]

    def fake_fetch(keywords, pillar, exclude, out_path, api_key):
        shutil.copyfile(source, out_path)
        return "pexels:1"

    out = tmp_path / "reel.mp4"
    footage_id = rr.render_reel(make_reel(1, NOW), make_quotes(1)[0], tmp_path / "work", out, api_key="k",
                                exclude_footage=set(), synthesize=fake_synth, fetch=fake_fetch)
    info = probe(out)
    assert footage_id == "pexels:1"
    assert (info.width, info.height) == (1080, 1920)
    assert info.duration == pytest.approx(5.0, abs=0.2)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_render_reel.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.render_reel'`

- [ ] **Step 3: Implementar**

`generator/media_probe.py`:
```python
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
```

`generator/render_reel.py`:
```python
"""Compose a narrated vertical reel with ffmpeg."""
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
MUSIC_DIR = ROOT / "generator" / "music"
SUBTITLES_NAME = "subs.ass"  # relative: ffmpeg runs inside work_dir so Windows paths never reach the filter graph


class RenderError(RuntimeError):
    """ffmpeg could not produce the reel."""


def pick_music(item_id: str, music_dir: Path | None = None) -> Path | None:
    tracks = sorted(Path(music_dir or MUSIC_DIR).glob("*.mp3"))
    return random.Random(item_id).choice(tracks) if tracks else None


def build_ffmpeg_cmd(background, narration, music, subtitles_name, duration, out_path) -> list[str]:
    cmd = ["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", str(background), "-i", str(narration)]
    video = (f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
             f"fps={FPS},eq=brightness=-0.12,ass={subtitles_name}[v]")
    if music is not None:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        audio = f"[2:a]volume={MUSIC_VOLUME}[m];[1:a][m]amix=inputs=2:duration=longest:normalize=0[a]"
    else:
        audio = "[1:a]apad[a]"
    return cmd + ["-filter_complex", f"{video};{audio}", "-map", "[v]", "-map", "[a]",
                  "-t", f"{duration:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                  str(out_path)]


def render_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage,
                synthesize=tts.synthesize, fetch=footage.fetch_footage, run=subprocess.run) -> str:
    """Render item to out_path; returns the footage id used."""
    work_dir, out_path = Path(work_dir), Path(out_path).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    narration = work_dir / "narration.mp3"
    words = synthesize(item["script"], narration)
    duration = words[-1].end + TAIL_SECONDS
    write_ass(work_dir / SUBTITLES_NAME, words, display_reference(quote), duration)
    background = work_dir / "background.mp4"
    footage_id = fetch(item["footage_keywords"], item["pillar"], exclude_footage, background, api_key)
    cmd = build_ffmpeg_cmd(background.resolve(), narration.resolve(), pick_music(item["id"]),
                           SUBTITLES_NAME, duration, out_path)
    result = run(cmd, cwd=work_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise RenderError(f"ffmpeg failed: {result.stderr[-800:]}")
    return footage_id
```

`generator/music/README.md`:
```markdown
Coloque aqui 3–5 trilhas `.mp3` livres de direitos (https://pixabay.com/music/).
Elas não vão para o git (licença do Pixabay proíbe redistribuí-las soltas). Sem trilhas, o reel sai só com narração.
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_render_reel.py -v`
Expected: 5 passed (o último exige ffmpeg; se aparecer "skipped", instale o ffmpeg antes de seguir)

- [ ] **Step 5: Commit**

```bash
git add generator/render_reel.py generator/media_probe.py generator/music/README.md tests/test_render_reel.py
git commit -m "feat: render narrated vertical reels with ffmpeg"
```

---

### Task 10: Renderização do carrossel (`generator/render_carousel.py`)

**Files:**
- Create: `generator/render_carousel.py`, `generator/templates/carousel.html`
- Test: `tests/test_render_carousel.py`

**Interfaces:**
- Consumes: `quotes.display_reference`
- Produces: `render_html(slide, index, total, handle, quotes) -> str`, `render_carousel(item, quotes, out_dir, handle) -> list[Path]` (arquivos `slide-01.jpg`…)

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_render_carousel.py`:
```python
from PIL import Image

from factories import NOW, make_carousel
from generator.render_carousel import render_carousel, render_html


def test_render_html_escapes_text_and_shows_reference(quotes):
    html = render_html({"title": "<b>Tempo</b>", "body": "Corpo", "quote_id": "q1"}, 2, 6, "@estoico", quotes)
    assert "&lt;b&gt;Tempo&lt;/b&gt;" in html
    assert "Sêneca, Cartas a Lucílio 1.1" in html
    assert "2/6" in html and "@estoico" in html


def test_cover_uses_bigger_title(quotes):
    assert "font-size:96px" in render_html({"title": "Capa"}, 1, 6, "", quotes)
    assert "font-size:72px" in render_html({"title": "Miolo"}, 2, 6, "", quotes)


def test_render_carousel_writes_jpeg_slides(tmp_path, quotes):
    paths = render_carousel(make_carousel(1, NOW), quotes, tmp_path, "@estoico")
    assert [p.name for p in paths] == [f"slide-{n:02d}.jpg" for n in range(1, 7)]
    with Image.open(paths[0]) as image:
        assert image.format == "JPEG" and image.size == (1080, 1350)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_render_carousel.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.render_carousel'`

- [ ] **Step 3: Implementar**

`generator/templates/carousel.html`:
```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,700;1,500&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
  html, body { margin: 0; width: 1080px; height: 1350px; background: #111; color: #f2ede4; }
  .slide { box-sizing: border-box; width: 1080px; height: 1350px; padding: 120px 100px;
           display: flex; flex-direction: column; justify-content: center; gap: 48px; position: relative; }
  .accent { width: 120px; height: 6px; background: #d4af37; }
  h1 { font-family: 'Cormorant Garamond', serif; font-weight: 700; margin: 0; line-height: 1.1;
       font-size:{{ 96 if is_cover else 72 }}px; }
  p { font-family: 'Inter', sans-serif; font-size: 40px; line-height: 1.5; margin: 0; color: #d9d3c7; }
  .ref { font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 40px; color: #d4af37; }
  .footer { position: absolute; bottom: 72px; left: 100px; right: 100px; display: flex;
            justify-content: space-between; font-family: 'Inter', sans-serif; font-size: 28px; color: #8c8578; }
</style>
</head>
<body>
<div class="slide">
  <div class="accent"></div>
  <h1>{{ slide.title }}</h1>
  {% if slide.body %}<p>{{ slide.body }}</p>{% endif %}
  {% if reference %}<div class="ref">{{ reference }}</div>{% endif %}
  <div class="footer"><span>{{ handle }}</span><span>{{ index }}/{{ total }}</span></div>
</div>
</body>
</html>
```

`generator/render_carousel.py`:
```python
"""Render carousel slides from an HTML template to 1080x1350 JPEGs (the only image format the Instagram API accepts)."""
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from generator.quotes import display_reference
from shared.config import ROOT

TEMPLATES_DIR = ROOT / "generator" / "templates"
SLIDE_WIDTH, SLIDE_HEIGHT = 1080, 1350
JPEG_QUALITY = 92

_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))


def render_html(slide: dict, index: int, total: int, handle: str, quotes: dict) -> str:
    quote = quotes.get(slide["quote_id"]) if slide.get("quote_id") else None
    return _env.get_template("carousel.html").render(
        slide=slide, index=index, total=total, handle=handle, is_cover=index == 1,
        reference=display_reference(quote) if quote else None)


def render_carousel(item: dict, quotes: dict, out_dir: Path, handle: str) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(item["slides"])
    paths = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": SLIDE_WIDTH, "height": SLIDE_HEIGHT})
            for index, slide in enumerate(item["slides"], start=1):
                page.set_content(render_html(slide, index, total, handle, quotes), wait_until="networkidle")
                path = out_dir / f"slide-{index:02d}.jpg"
                page.screenshot(path=str(path), type="jpeg", quality=JPEG_QUALITY)
                paths.append(path)
        finally:
            browser.close()
    return paths
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_render_carousel.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add generator/render_carousel.py generator/templates/ tests/test_render_carousel.py
git commit -m "feat: render carousel slides to JPEG"
```

---

### Task 11: Fila de publicação (`shared/post_queue.py`)

**Files:**
- Create: `shared/post_queue.py`, `queue.json` (conteúdo `[]`)
- Test: `tests/test_post_queue.py`

**Interfaces:**
- Consumes: `shared.jsonio`, `shared.timeutil.parse_time`
- Produces: `QUEUE_PATH`, `MAX_ATTEMPTS = 3`, `TIKTOK_AUTOMATED = False`, `load_queue(path=QUEUE_PATH) -> list[dict]`, `save_queue(path, queue)`, `compose_caption(item) -> str`, `make_entry(item, media: list[str]) -> dict`, `add_entries(queue, entries) -> list[dict]`, `due_entries(queue, platform, now) -> list[dict]`, `has_pending(entry) -> bool`, `mark_published(entry, platform, published_id)`, `mark_failed(entry, platform, error) -> bool`
- Entrada da fila: `{"id", "type", "scheduled_at", "caption", "media": ["reel.mp4"], "platforms": {"instagram": {"status", "attempts", "published_id", "last_error"}, ...}}`. Status: `pending | published | failed | manual`.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_post_queue.py`:
```python
from datetime import timedelta

import pytest

from factories import NOW, make_reel
from shared.post_queue import add_entries, due_entries, make_entry, mark_failed, mark_published


def reel_entry(n, when):
    return make_entry(make_reel(n, when), ["reel.mp4"])


def test_make_entry_marks_tiktok_manual_and_composes_caption():
    entry = reel_entry(1, NOW)
    assert entry["platforms"]["instagram"]["status"] == "pending"
    assert entry["platforms"]["tiktok"]["status"] == "manual"
    assert entry["caption"] == "Legenda 1\n\n#estoicismo"


def test_add_entries_sorts_and_replaces_unpublished():
    late, early = reel_entry(2, NOW + timedelta(days=1)), reel_entry(1, NOW)
    queue = add_entries([], [late, early])
    assert [e["id"] for e in queue] == [early["id"], late["id"]]
    assert add_entries(queue, [dict(early, caption="nova")])[0]["caption"] == "nova"


def test_add_entries_refuses_to_replace_published():
    entry = reel_entry(1, NOW)
    mark_published(entry, "instagram", "ig-1")
    with pytest.raises(ValueError, match="already published"):
        add_entries([entry], [reel_entry(1, NOW)])


def test_due_entries():
    past, future = reel_entry(1, NOW - timedelta(hours=1)), reel_entry(2, NOW + timedelta(hours=1))
    assert due_entries([past, future], "instagram", NOW) == [past]
    assert due_entries([past, future], "tiktok", NOW) == []


def test_mark_failed_gives_up_after_three_attempts():
    entry = reel_entry(1, NOW)
    assert mark_failed(entry, "instagram", "boom") is False
    assert mark_failed(entry, "instagram", "boom") is False
    assert mark_failed(entry, "instagram", "boom") is True
    assert entry["platforms"]["instagram"] == {"status": "failed", "attempts": 3,
                                               "published_id": None, "last_error": "boom"}
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_post_queue.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'shared.post_queue'`

- [ ] **Step 3: Implementar**

`shared/post_queue.py`:
```python
"""Publication queue shared by the local generator and the GitHub Actions publisher."""
from datetime import datetime
from pathlib import Path

from shared.config import ROOT
from shared.jsonio import read_json, write_json
from shared.timeutil import parse_time

QUEUE_PATH = ROOT / "queue.json"
MAX_ATTEMPTS = 3
TIKTOK_AUTOMATED = False  # flip once the TikTok app passes audit (spec Phase 5)


def load_queue(path: Path = QUEUE_PATH) -> list[dict]:
    return read_json(path) if Path(path).exists() else []


def save_queue(path: Path, queue: list[dict]) -> None:
    write_json(path, queue)


def compose_caption(item: dict) -> str:
    return f"{item['caption'].strip()}\n\n{' '.join(item['hashtags'])}".strip()


def make_entry(item: dict, media: list[str]) -> dict:
    platforms = {}
    for platform in item["platforms"]:
        status = "manual" if platform == "tiktok" and not TIKTOK_AUTOMATED else "pending"
        platforms[platform] = {"status": status, "attempts": 0, "published_id": None, "last_error": None}
    return {"id": item["id"], "type": item["type"], "scheduled_at": item["scheduled_at"],
            "caption": compose_caption(item), "media": list(media), "platforms": platforms}


def add_entries(queue: list[dict], entries: list[dict]) -> list[dict]:
    """Append entries, replacing same-id entries that were never published."""
    by_id = {entry["id"]: entry for entry in queue}
    for entry in entries:
        old = by_id.get(entry["id"])
        if old and any(state["status"] == "published" for state in old["platforms"].values()):
            raise ValueError(f"{entry['id']}: already published, refusing to replace")
        by_id[entry["id"]] = entry
    return sorted(by_id.values(), key=lambda e: parse_time(e["scheduled_at"]))


def due_entries(queue: list[dict], platform: str, now: datetime) -> list[dict]:
    due = [entry for entry in queue
           if entry["platforms"].get(platform, {}).get("status") == "pending"
           and parse_time(entry["scheduled_at"]) <= now]
    return sorted(due, key=lambda e: parse_time(e["scheduled_at"]))


def has_pending(entry: dict) -> bool:
    return any(state["status"] == "pending" for state in entry["platforms"].values())


def mark_published(entry: dict, platform: str, published_id: str) -> None:
    entry["platforms"][platform].update(status="published", published_id=published_id, last_error=None)


def mark_failed(entry: dict, platform: str, error: str) -> bool:
    """Record a failed attempt; returns True when the entry gave up (status 'failed')."""
    state = entry["platforms"][platform]
    state["attempts"] += 1
    state["last_error"] = error[:500]
    state["status"] = "failed" if state["attempts"] >= MAX_ATTEMPTS else "pending"
    return state["status"] == "failed"
```

`queue.json`:
```json
[]
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_post_queue.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add shared/post_queue.py queue.json tests/test_post_queue.py
git commit -m "feat: add publication queue"
```

---

### Task 12: Slots do próximo lote (`generator/schedule.py`)

**Files:**
- Create: `generator/schedule.py`
- Test: `tests/test_schedule.py`

**Interfaces:**
- Consumes: `post_queue.load_queue`, `timeutil.parse_time`, `timeutil.now_local`
- Produces: `next_slots(queue, now) -> dict` — `{"skip": True, "reason": str}` ou `{"skip": False, "batch": "YYYY-MM-DD", "reels": [7 ISO], "carousels": [3 ISO]}`; CLI `python -m generator.schedule` imprime esse JSON.

Regra: começa no primeiro meio-dia depois de `max(agora, último item da fila)`; 7 dias seguidos; carrosséis às 19:00 nos dias 2, 4 e 6 da janela; se a fila já tem itens mais de 2 dias à frente, `skip`.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_schedule.py`:
```python
from datetime import timedelta

from factories import NOW, make_reel
from generator.schedule import next_slots
from shared.post_queue import make_entry


def entry_at(when):
    return make_entry(make_reel(1, when), ["reel.mp4"])


def test_empty_queue_starts_today_at_noon():
    slots = next_slots([], NOW)
    assert slots["skip"] is False
    assert slots["batch"] == "2026-10-19"
    assert slots["reels"][0] == "2026-10-19T12:00:00-03:00"
    assert slots["reels"][-1] == "2026-10-25T12:00:00-03:00"
    assert slots["carousels"] == ["2026-10-20T19:00:00-03:00", "2026-10-22T19:00:00-03:00",
                                  "2026-10-24T19:00:00-03:00"]


def test_after_noon_starts_tomorrow():
    assert next_slots([], NOW.replace(hour=13))["reels"][0] == "2026-10-20T12:00:00-03:00"


def test_continues_after_last_queued_item():
    queue = [entry_at(NOW.replace(hour=13))]  # Monday 13:00 still queued
    assert next_slots(queue, NOW)["reels"][0] == "2026-10-20T12:00:00-03:00"


def test_late_run_never_schedules_in_the_past():
    tuesday_10am = NOW + timedelta(days=1, hours=2)
    assert next_slots([entry_at(NOW - timedelta(days=1))], tuesday_10am)["reels"][0] == "2026-10-20T12:00:00-03:00"


def test_skips_when_queue_is_already_full():
    slots = next_slots([entry_at(NOW + timedelta(days=3))], NOW)
    assert slots["skip"] is True
    assert "2026-10-22" in slots["reason"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_schedule.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.schedule'`

- [ ] **Step 3: Implementar**

`generator/schedule.py`:
```python
"""Publication slots for the next batch, so a late or repeated routine never overlaps or schedules in the past."""
import json
import sys
from datetime import datetime, time, timedelta

from shared.post_queue import load_queue
from shared.timeutil import now_local, parse_time

REEL_HOUR = 12
CAROUSEL_HOUR = 19
CAROUSEL_DAY_OFFSETS = (1, 3, 5)
DAYS = 7
SKIP_IF_QUEUED_AHEAD = timedelta(days=2)


def next_slots(queue: list[dict], now: datetime) -> dict:
    last = max((parse_time(entry["scheduled_at"]) for entry in queue), default=None)
    if last is not None and last - now > SKIP_IF_QUEUED_AHEAD:
        return {"skip": True, "reason": f"queue already scheduled until {last.isoformat()}"}
    start_after = max(now, last) if last is not None else now
    first_day = start_after.date()
    if datetime.combine(first_day, time(REEL_HOUR), tzinfo=now.tzinfo) <= start_after:
        first_day += timedelta(days=1)
    days = [first_day + timedelta(days=offset) for offset in range(DAYS)]

    def at(day, hour):
        return datetime.combine(day, time(hour), tzinfo=now.tzinfo).isoformat()

    return {"skip": False, "batch": first_day.isoformat(),
            "reels": [at(day, REEL_HOUR) for day in days],
            "carousels": [at(days[offset], CAROUSEL_HOUR) for offset in CAROUSEL_DAY_OFFSETS]}


def main() -> int:
    print(json.dumps(next_slots(load_queue(), now_local()), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_schedule.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add generator/schedule.py tests/test_schedule.py
git commit -m "feat: compute next batch publication slots"
```

---

### Task 13: Validação (`generator/validate.py`)

**Files:**
- Create: `generator/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `batch.quote_ids_of`, `history.quote_on_cooldown`, `media_probe.probe` / `MediaInfo`, `post_queue.compose_caption`, `timeutil.parse_time`
- Produces: `check_plan(batch, quotes, history, now) -> list[str]` (antes de renderizar), `check_media(batch, output_dir, probe=probe) -> list[str]` (depois: `output_dir/<id>/reel.mp4` e `output_dir/<id>/slide-NN.jpg`)

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_validate.py`:
```python
from datetime import timedelta

from PIL import Image

from factories import NOW
from generator.media_probe import MediaInfo
from generator.validate import check_media, check_plan

EMPTY = {"quotes": {}, "footage": {}}


def test_valid_week_passes(week, quotes):
    assert check_plan(week, quotes, EMPTY, NOW) == []


def test_counts(week, quotes):
    week["items"] = week["items"][1:]
    assert "batch must have 7 reels, found 6" in check_plan(week, quotes, EMPTY, NOW)


def test_unknown_quote_and_cooldown(week, quotes):
    week["items"][0]["quote_id"] = "nope"
    history = {"quotes": {"q2": {"on": "2026-09-01", "item": "old"}}, "footage": {}}
    errors = check_plan(week, quotes, history, NOW)
    assert "2026-10-19-r1: quote nope is not in content/quotes.json" in errors
    assert "2026-10-19-r2: quote q2 was used less than 60 days ago" in errors


def test_duplicate_quote_and_hook_in_batch(week, quotes):
    week["items"][1]["quote_id"] = "q1"
    week["items"][1]["hook"] = " gancho 1 "
    errors = check_plan(week, quotes, EMPTY, NOW)
    assert "2026-10-19-r2: quote q1 already used by 2026-10-19-r1 in this batch" in errors
    assert "2026-10-19-r2: hook repeats 2026-10-19-r1" in errors


def test_past_schedule_and_script_length(week, quotes):
    week["items"][0]["scheduled_at"] = (NOW - timedelta(hours=1)).isoformat()
    week["items"][1]["script"] = "curto demais"
    errors = check_plan(week, quotes, EMPTY, NOW)
    assert "2026-10-19-r1: scheduled_at is in the past" in errors
    assert "2026-10-19-r2: script has 2 words (expected 80-145)" in errors


def test_caption_hashtags_and_slides(week, quotes):
    week["items"][0]["caption"] = "x" * 2300
    week["items"][1]["hashtags"] = ["estoicismo"]
    week["items"][7]["slides"] = week["items"][7]["slides"][:3]
    week["items"][8]["slides"][0]["quote_id"] = "q5"
    errors = check_plan(week, quotes, EMPTY, NOW)
    assert any(e.startswith("2026-10-19-r1: caption has") for e in errors)
    assert "2026-10-19-r2: hashtags must be at most 30 single words starting with #" in errors
    assert "2026-10-19-c1: carousel has 3 slides (expected 6-8)" in errors
    assert "2026-10-19-c2: slide 1 quote_id must be listed in quote_ids" in errors


def write_slides(folder, count, size=(1080, 1350)):
    folder.mkdir(parents=True, exist_ok=True)
    for n in range(1, count + 1):
        Image.new("RGB", size).save(folder / f"slide-{n:02d}.jpg", "JPEG")


def render_all(week, out):
    for item in week["items"]:
        folder = out / item["id"]
        if item["type"] == "reel":
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "reel.mp4").write_bytes(b"x")
        else:
            write_slides(folder, len(item["slides"]))


def test_media_ok(tmp_path, week):
    render_all(week, tmp_path)
    assert check_media(week, tmp_path, probe=lambda path: MediaInfo(1080, 1920, 45.0, 10_000_000)) == []


def test_media_problems(tmp_path, week):
    render_all(week, tmp_path)
    (tmp_path / "2026-10-19-r1" / "reel.mp4").unlink()
    write_slides(tmp_path / "2026-10-19-c1", 6, size=(1080, 1080))
    errors = check_media(week, tmp_path, probe=lambda path: MediaInfo(1080, 1920, 20.0, 10))
    assert "2026-10-19-r1: reel.mp4 was not rendered" in errors
    assert "2026-10-19-r2: reel lasts 20.0s, expected 30-60s (adjust script length)" in errors
    assert "2026-10-19-c1: slide-01.jpg must be a 1080x1350 JPEG" in errors
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_validate.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.validate'`

- [ ] **Step 3: Implementar**

`generator/validate.py`:
```python
"""Batch rules: check_plan runs before rendering (cheap), check_media after (output specs)."""
from datetime import datetime
from pathlib import Path

from PIL import Image

from generator.batch import quote_ids_of
from generator.history import QUOTE_COOLDOWN_DAYS, quote_on_cooldown
from generator.media_probe import probe as ffprobe
from shared.post_queue import compose_caption
from shared.timeutil import parse_time

REELS_PER_BATCH = 7
CAROUSELS_PER_BATCH = 3
SCRIPT_MIN_WORDS, SCRIPT_MAX_WORDS = 80, 145
SLIDES_MIN, SLIDES_MAX = 6, 8
CAPTION_MAX_CHARS = 2200
HASHTAGS_MAX = 30
REEL_SIZE = (1080, 1920)
SLIDE_SIZE = (1080, 1350)
REEL_MIN_SECONDS, REEL_MAX_SECONDS = 30.0, 60.0
REEL_MAX_BYTES = 100 * 1024 * 1024


def check_plan(batch: dict, quotes: dict, history: dict, now: datetime) -> list[str]:
    items = batch["items"]
    errors = []
    reels = sum(1 for item in items if item["type"] == "reel")
    carousels = sum(1 for item in items if item["type"] == "carousel")
    if reels != REELS_PER_BATCH:
        errors.append(f"batch must have {REELS_PER_BATCH} reels, found {reels}")
    if carousels != CAROUSELS_PER_BATCH:
        errors.append(f"batch must have {CAROUSELS_PER_BATCH} carousels, found {carousels}")
    used_quotes, hooks = {}, {}
    for item in items:
        errors.extend(_check_item(item, quotes, history, now, used_quotes, hooks))
    return errors


def _check_item(item, quotes, history, now, used_quotes, hooks) -> list[str]:
    label = item["id"]
    errors = []
    when = parse_time(item["scheduled_at"])
    if when <= now:
        errors.append(f"{label}: scheduled_at is in the past")
    for quote_id in quote_ids_of(item):
        if quote_id not in quotes:
            errors.append(f"{label}: quote {quote_id} is not in content/quotes.json")
        elif quote_on_cooldown(history, quote_id, when.date(), label):
            errors.append(f"{label}: quote {quote_id} was used less than {QUOTE_COOLDOWN_DAYS} days ago")
        if quote_id in used_quotes:
            errors.append(f"{label}: quote {quote_id} already used by {used_quotes[quote_id]} in this batch")
        used_quotes.setdefault(quote_id, label)
    caption = compose_caption(item)
    if len(caption) > CAPTION_MAX_CHARS:
        errors.append(f"{label}: caption has {len(caption)} chars (max {CAPTION_MAX_CHARS})")
    tags = item["hashtags"]
    if len(tags) > HASHTAGS_MAX or any(not tag.startswith("#") or " " in tag for tag in tags):
        errors.append(f"{label}: hashtags must be at most {HASHTAGS_MAX} single words starting with #")
    if item["type"] == "reel":
        words = len(item["script"].split())
        if not SCRIPT_MIN_WORDS <= words <= SCRIPT_MAX_WORDS:
            errors.append(f"{label}: script has {words} words (expected {SCRIPT_MIN_WORDS}-{SCRIPT_MAX_WORDS})")
        hook = item["hook"].strip().lower()
        if hook in hooks:
            errors.append(f"{label}: hook repeats {hooks[hook]}")
        hooks.setdefault(hook, label)
    else:
        slides = item["slides"]
        if not SLIDES_MIN <= len(slides) <= SLIDES_MAX:
            errors.append(f"{label}: carousel has {len(slides)} slides (expected {SLIDES_MIN}-{SLIDES_MAX})")
        for number, slide in enumerate(slides, start=1):
            if not str(slide.get("title", "")).strip():
                errors.append(f"{label}: slide {number} has no title")
            if slide.get("quote_id") and slide["quote_id"] not in item["quote_ids"]:
                errors.append(f"{label}: slide {number} quote_id must be listed in quote_ids")
    return errors


def check_media(batch: dict, output_dir: Path, probe=ffprobe) -> list[str]:
    errors = []
    for item in batch["items"]:
        item_dir = Path(output_dir) / item["id"]
        if item["type"] == "reel":
            errors.extend(_check_reel(item["id"], item_dir / "reel.mp4", probe))
        else:
            errors.extend(_check_slides(item["id"], item_dir, len(item["slides"])))
    return errors


def _check_reel(label, path, probe) -> list[str]:
    if not path.exists():
        return [f"{label}: {path.name} was not rendered"]
    info = probe(path)
    errors = []
    if (info.width, info.height) != REEL_SIZE:
        errors.append(f"{label}: reel is {info.width}x{info.height}, expected 1080x1920")
    if not REEL_MIN_SECONDS <= info.duration <= REEL_MAX_SECONDS:
        errors.append(f"{label}: reel lasts {info.duration:.1f}s, expected 30-60s (adjust script length)")
    if info.size_bytes > REEL_MAX_BYTES:
        errors.append(f"{label}: reel has {info.size_bytes // (1024 * 1024)} MB (max 100 MB)")
    return errors


def _check_slides(label, item_dir, expected) -> list[str]:
    paths = sorted(item_dir.glob("slide-*.jpg"))
    if len(paths) != expected:
        return [f"{label}: expected {expected} slides, found {len(paths)}"]
    errors = []
    for path in paths:
        with Image.open(path) as image:
            if image.format != "JPEG" or image.size != SLIDE_SIZE:
                errors.append(f"{label}: {path.name} must be a 1080x1350 JPEG")
    return errors
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_validate.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add generator/validate.py tests/test_validate.py
git commit -m "feat: validate batch plan and rendered media"
```

---

### Task 14: Orquestrador (`generator/build_week.py`)

**Files:**
- Create: `generator/build_week.py`, `content/history.json` (conteúdo `{"quotes": {}, "footage": {}}`)
- Test: `tests/test_build_week.py`

**Interfaces:**
- Consumes: tudo de Tasks 3–13 com as assinaturas acima; `shared.config.OUTPUT_DIR`, `Settings`, `require`
- Produces: `render_item(item, quotes, settings, output_dir, exclude_footage, *, reel_renderer, carousel_renderer) -> tuple[list[str], str | None]`, `build_week(batch_path, *, now, settings, quotes_path, queue_path, history_path, output_dir, reel_renderer, carousel_renderer, media_checker) -> list[str]`, `preview_item(batch_path, item_id, *, settings, quotes_path, queue_path, output_dir, enqueue=False, reel_renderer, carousel_renderer, media_checker) -> list[str]`, CLI `python -m generator.build_week <batch.json> [--preview ID] [--enqueue]` (exit 0 = OK, 1 = erros em stderr)

Garantia: `queue.json` e `history.json` só são escritos quando o lote inteiro renderizou e passou na validação.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_build_week.py`:
```python
from datetime import timedelta

import pytest

from factories import NOW, SETTINGS, make_quotes
from generator.build_week import build_week, preview_item
from shared.jsonio import read_json, write_json


def fake_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(b"mp4")
    return f"pexels:{item['id']}"


def fake_carousel(item, quotes, out_dir, handle):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for number in range(1, len(item["slides"]) + 1):
        path = out_dir / f"slide-{number:02d}.jpg"
        path.write_bytes(b"jpg")
        paths.append(path)
    return paths


def no_media_problems(batch, output_dir):
    return []


@pytest.fixture
def paths(tmp_path, week):
    batch = tmp_path / "batch.json"
    write_json(batch, week)
    quotes = tmp_path / "quotes.json"
    write_json(quotes, make_quotes())
    return {"batch": batch, "quotes_path": quotes, "queue_path": tmp_path / "queue.json",
            "history_path": tmp_path / "history.json", "output_dir": tmp_path / "output"}


def run_build(paths, now=NOW, **overrides):
    kwargs = dict(now=now, settings=SETTINGS, quotes_path=paths["quotes_path"], queue_path=paths["queue_path"],
                  history_path=paths["history_path"], output_dir=paths["output_dir"],
                  reel_renderer=fake_reel, carousel_renderer=fake_carousel, media_checker=no_media_problems)
    kwargs.update(overrides)
    return build_week(paths["batch"], **kwargs)


def test_successful_build_queues_everything_and_records_history(paths):
    assert run_build(paths) == []
    queue = read_json(paths["queue_path"])
    assert len(queue) == 10
    assert queue[0]["id"] == "2026-10-19-r1" and queue[0]["media"] == ["reel.mp4"]
    carousel = next(e for e in queue if e["id"] == "2026-10-19-c1")
    assert carousel["media"] == [f"slide-{n:02d}.jpg" for n in range(1, 7)]
    history = read_json(paths["history_path"])
    assert history["quotes"]["q1"] == {"on": "2026-10-19", "item": "2026-10-19-r1"}
    assert history["footage"]["pexels:2026-10-19-r1"]["item"] == "2026-10-19-r1"


def test_plan_errors_stop_before_rendering(paths):
    def explode(*args, **kwargs):
        raise AssertionError("renderer must not run")

    errors = run_build(paths, now=NOW + timedelta(days=30), reel_renderer=explode, carousel_renderer=explode)
    assert errors and all("in the past" in error for error in errors)
    assert not paths["queue_path"].exists()


def test_render_failure_reports_item_and_writes_nothing(paths):
    def flaky_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage):
        if item["id"] == "2026-10-19-r3":
            raise RuntimeError("ffmpeg failed: boom")
        return fake_reel(item, quote, work_dir, out_path, api_key=api_key, exclude_footage=exclude_footage)

    assert run_build(paths, reel_renderer=flaky_reel) == ["2026-10-19-r3: render failed: ffmpeg failed: boom"]
    assert not paths["queue_path"].exists() and not paths["history_path"].exists()


def test_media_check_failure_writes_nothing(paths):
    errors = run_build(paths, media_checker=lambda batch, out: ["2026-10-19-r1: reel lasts 20.0s"])
    assert errors == ["2026-10-19-r1: reel lasts 20.0s"]
    assert not paths["queue_path"].exists()


def test_rebuilding_same_batch_is_allowed(paths):
    assert run_build(paths) == []
    assert run_build(paths) == []
    assert len(read_json(paths["queue_path"])) == 10


def test_footage_is_not_repeated_within_batch(paths):
    seen = []

    def recording_reel(item, quote, work_dir, out_path, *, api_key, exclude_footage):
        seen.append(set(exclude_footage))
        return fake_reel(item, quote, work_dir, out_path, api_key=api_key, exclude_footage=exclude_footage)

    run_build(paths, reel_renderer=recording_reel)
    assert seen[0] == set() and "pexels:2026-10-19-r1" in seen[1]


def test_preview_renders_one_item_and_can_enqueue(paths):
    errors = preview_item(paths["batch"], "2026-10-19-r1", settings=SETTINGS, quotes_path=paths["quotes_path"],
                          queue_path=paths["queue_path"], output_dir=paths["output_dir"], enqueue=True,
                          reel_renderer=fake_reel, carousel_renderer=fake_carousel,
                          media_checker=no_media_problems)
    assert errors == []
    assert [e["id"] for e in read_json(paths["queue_path"])] == ["2026-10-19-r1"]


def test_preview_unknown_item(paths):
    assert preview_item(paths["batch"], "nope", settings=SETTINGS, quotes_path=paths["quotes_path"]) == \
        [f"nope: not found in {paths['batch']}"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_build_week.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.build_week'`

- [ ] **Step 3: Implementar**

`generator/build_week.py`:
```python
"""Render, validate and queue a batch: `python -m generator.build_week content/weeks/<batch>.json`."""
import argparse
import sys
from pathlib import Path

from generator.batch import load_batch, quote_ids_of
from generator.history import HISTORY_PATH, load_history, recent_footage, record_use, save_history
from generator.quotes import QUOTES_PATH, load_quotes
from generator.render_carousel import render_carousel
from generator.render_reel import render_reel
from generator.validate import check_media, check_plan
from shared.config import OUTPUT_DIR, Settings, load_settings, require
from shared.post_queue import QUEUE_PATH, add_entries, load_queue, make_entry, save_queue
from shared.timeutil import now_local, parse_time


def render_item(item, quotes, settings: Settings, output_dir, exclude_footage, *,
                reel_renderer, carousel_renderer) -> tuple[list[str], str | None]:
    """Render one item into output_dir/<id>/; returns (media file names, footage id or None)."""
    item_dir = Path(output_dir) / item["id"]
    if item["type"] == "reel":
        footage_id = reel_renderer(item, quotes[item["quote_id"]], item_dir / "work", item_dir / "reel.mp4",
                                   api_key=require(settings.pexels_api_key, "PEXELS_API_KEY"),
                                   exclude_footage=exclude_footage)
        return ["reel.mp4"], footage_id
    paths = carousel_renderer(item, quotes, item_dir, settings.handle)
    return [path.name for path in paths], None


def build_week(batch_path, *, now, settings, quotes_path=QUOTES_PATH, queue_path=QUEUE_PATH,
               history_path=HISTORY_PATH, output_dir=OUTPUT_DIR, reel_renderer=render_reel,
               carousel_renderer=render_carousel, media_checker=check_media) -> list[str]:
    """Render and validate a batch; queue and history are written only when there are no errors."""
    batch = load_batch(batch_path)
    quotes = load_quotes(quotes_path)
    history = load_history(history_path)
    errors = check_plan(batch, quotes, history, now)
    if errors:
        return errors
    exclude = recent_footage(history, now.date())
    entries, footage_by_item = [], {}
    for item in batch["items"]:
        try:
            media, footage_id = render_item(item, quotes, settings, output_dir, exclude,
                                            reel_renderer=reel_renderer, carousel_renderer=carousel_renderer)
        except Exception as exc:  # keep going so one run reports every broken item
            errors.append(f"{item['id']}: render failed: {exc}")
            continue
        if footage_id and footage_id != "fallback":
            exclude.add(footage_id)
            footage_by_item[item["id"]] = footage_id
        entries.append(make_entry(item, media))
    if errors:
        return errors
    errors = media_checker(batch, output_dir)
    if errors:
        return errors
    try:
        queue = add_entries(load_queue(queue_path), entries)
    except ValueError as exc:
        return [str(exc)]
    for item in batch["items"]:
        footage = [footage_by_item[item["id"]]] if item["id"] in footage_by_item else []
        record_use(history, item_id=item["id"], quote_ids=quote_ids_of(item), footage_ids=footage,
                   on=parse_time(item["scheduled_at"]).date())
    save_queue(queue_path, queue)
    save_history(history_path, history)
    return []


def preview_item(batch_path, item_id, *, settings, quotes_path=QUOTES_PATH, queue_path=QUEUE_PATH,
                 output_dir=OUTPUT_DIR, enqueue=False, reel_renderer=render_reel,
                 carousel_renderer=render_carousel, media_checker=check_media) -> list[str]:
    """Render a single item for review (no batch-size rules); optionally queue it."""
    batch = load_batch(batch_path)
    item = next((candidate for candidate in batch["items"] if candidate["id"] == item_id), None)
    if item is None:
        return [f"{item_id}: not found in {batch_path}"]
    quotes = load_quotes(quotes_path)
    missing = [quote_id for quote_id in quote_ids_of(item) if quote_id not in quotes]
    if missing:
        return [f"{item_id}: quotes not in bank: {missing}"]
    media, _ = render_item(item, quotes, settings, output_dir, set(),
                           reel_renderer=reel_renderer, carousel_renderer=carousel_renderer)
    errors = media_checker({"week": batch["week"], "items": [item]}, output_dir)
    if errors:
        return errors
    if enqueue:
        save_queue(queue_path, add_entries(load_queue(queue_path), [make_entry(item, media)]))
    return []


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render, validate and queue a content batch")
    parser.add_argument("batch", type=Path)
    parser.add_argument("--preview", metavar="ITEM_ID", help="render only this item, skipping batch rules")
    parser.add_argument("--enqueue", action="store_true", help="with --preview: add the item to queue.json")
    args = parser.parse_args(argv)
    settings = load_settings()
    try:
        if args.preview:
            errors = preview_item(args.batch, args.preview, settings=settings, enqueue=args.enqueue)
        else:
            errors = build_week(args.batch, now=now_local(), settings=settings)
    except Exception as exc:  # report any failure as a readable line for the routine
        errors = [f"{type(exc).__name__}: {exc}"]
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if not errors:
        print("OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
```

`content/history.json`:
```json
{"quotes": {}, "footage": {}}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_build_week.py -v`
Expected: 8 passed

- [ ] **Step 5: Rodar a suíte toda**

Run: `.venv/Scripts/python -m pytest`
Expected: todos passam (1 deselected: teste `network`)

- [ ] **Step 6: Commit**

```bash
git add generator/build_week.py content/history.json tests/test_build_week.py
git commit -m "feat: orchestrate batch rendering, validation and queueing"
```

---

### Task 15: Deploy da mídia (`generator/deploy_media.py`)

**Files:**
- Create: `generator/deploy_media.py`
- Test: `tests/test_deploy_media.py`

**Interfaces:**
- Consumes: `post_queue.load_queue`, `post_queue.has_pending`, `shared.config.OUTPUT_DIR`, `ROOT`
- Produces: `assemble(queue, output_dir, site_dir, dest) -> list[str]` (arquivos faltando), `push_pages(dest, remote_url, run=subprocess.run)`, `prune_output(queue, output_dir, now, keep_days=14) -> list[str]`, CLI `python -m generator.deploy_media`
- Layout publicado: `<PAGES_BASE_URL>/media/<id>/<arquivo>` + arquivos de `site/` na raiz.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_deploy_media.py`:
```python
from datetime import timedelta

from factories import NOW, make_reel
from generator.deploy_media import assemble, prune_output, push_pages
from shared.post_queue import make_entry, mark_published


def reel_entry(n, when):
    return make_entry(make_reel(n, when), ["reel.mp4"])


def setup_output(tmp_path, entry):
    folder = tmp_path / "output" / entry["id"]
    folder.mkdir(parents=True)
    for name in entry["media"]:
        (folder / name).write_bytes(b"media")


def make_site(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("<h1>links</h1>", encoding="utf-8")
    return site


def test_assemble_copies_site_and_pending_media_only(tmp_path):
    pending, done = reel_entry(1, NOW), reel_entry(2, NOW)
    mark_published(done, "instagram", "ig-1")
    for entry in (pending, done):
        setup_output(tmp_path, entry)
    dest = tmp_path / "pages"
    assert assemble([pending, done], tmp_path / "output", make_site(tmp_path), dest) == []
    assert (dest / "index.html").exists() and (dest / ".nojekyll").exists()
    assert (dest / "media" / pending["id"] / "reel.mp4").read_bytes() == b"media"
    assert not (dest / "media" / done["id"]).exists()


def test_assemble_reports_missing_media(tmp_path):
    entry = reel_entry(1, NOW)
    missing = assemble([entry], tmp_path / "output", make_site(tmp_path), tmp_path / "pages")
    assert missing == [str(tmp_path / "output" / entry["id"] / "reel.mp4")]


def test_push_pages_force_pushes_a_single_commit(tmp_path):
    calls = []
    push_pages(tmp_path, "https://github.com/u/stoic-autopilot.git", run=lambda cmd, **kwargs: calls.append(cmd))
    assert calls[0] == ["git", "init", "-q", "-b", "gh-pages"]
    assert calls[-1] == ["git", "push", "-f", "https://github.com/u/stoic-autopilot.git", "gh-pages"]


def test_prune_output_keeps_recent_and_pending(tmp_path):
    old_done, recent_done = reel_entry(1, NOW - timedelta(days=20)), reel_entry(2, NOW - timedelta(days=3))
    old_pending = reel_entry(3, NOW - timedelta(days=20))
    mark_published(old_done, "instagram", "1")
    mark_published(recent_done, "instagram", "2")
    for entry in (old_done, recent_done, old_pending):
        setup_output(tmp_path, entry)
    removed = prune_output([old_done, recent_done, old_pending], tmp_path / "output", NOW)
    assert removed == [old_done["id"]]
    assert (tmp_path / "output" / recent_done["id"]).exists()
    assert (tmp_path / "output" / old_pending["id"]).exists()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_deploy_media.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'generator.deploy_media'`

- [ ] **Step 3: Implementar**

`generator/deploy_media.py`:
```python
"""Publish pending media to the gh-pages branch: `python -m generator.deploy_media`."""
import shutil
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

from shared.config import OUTPUT_DIR, ROOT
from shared.post_queue import QUEUE_PATH, has_pending, load_queue
from shared.timeutil import now_local, parse_time

SITE_DIR = ROOT / "site"
KEEP_DAYS = 14  # rendered files stay locally two weeks for manual TikTok uploads
BOT_IDENTITY = ["-c", "user.name=stoic-autopilot", "-c", "user.email=stoic-autopilot@users.noreply.github.com"]


def assemble(queue, output_dir, site_dir, dest) -> list[str]:
    """Copy the site plus media of entries still pending somewhere into dest; returns missing files."""
    dest = Path(dest)
    shutil.copytree(site_dir, dest, dirs_exist_ok=True)
    (dest / ".nojekyll").touch()
    missing = []
    for entry in queue:
        if not has_pending(entry):
            continue
        for name in entry["media"]:
            source = Path(output_dir) / entry["id"] / name
            if not source.exists():
                missing.append(str(source))
                continue
            target = dest / "media" / entry["id"] / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    return missing


def push_pages(dest, remote_url, run=subprocess.run) -> None:
    """Force-push dest as a one-commit gh-pages branch so the branch history never grows."""
    for cmd in (["git", "init", "-q", "-b", "gh-pages"],
                ["git", "add", "-A"],
                ["git", *BOT_IDENTITY, "commit", "-q", "-m", "deploy media"],
                ["git", "push", "-f", remote_url, "gh-pages"]):
        run(cmd, cwd=dest, check=True)


def prune_output(queue, output_dir, now, keep_days=KEEP_DAYS) -> list[str]:
    """Delete rendered folders of entries with nothing pending that are older than keep_days."""
    removed = []
    for entry in queue:
        if has_pending(entry) or now - parse_time(entry["scheduled_at"]) < timedelta(days=keep_days):
            continue
        folder = Path(output_dir) / entry["id"]
        if folder.exists():
            shutil.rmtree(folder)
            removed.append(entry["id"])
    return removed


def main() -> int:
    queue = load_queue(QUEUE_PATH)
    remote = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.strip()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        dest = Path(tmp) / "pages"
        missing = assemble(queue, OUTPUT_DIR, SITE_DIR, dest)
        if missing:
            for path in missing:
                print(f"ERROR: missing rendered file {path}", file=sys.stderr)
            return 1
        push_pages(dest, remote)
    removed = prune_output(queue, OUTPUT_DIR, now_local())
    print(f"OK: gh-pages updated; pruned {len(removed)} old output folders")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_deploy_media.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add generator/deploy_media.py tests/test_deploy_media.py
git commit -m "feat: deploy pending media to gh-pages"
```

---

### Task 16: Cliente do Instagram (`publisher/instagram.py`)

**Files:**
- Create: `publisher/instagram.py`
- Test: `tests/test_instagram.py`

**Interfaces:**
- Produces: `API_VERSION = "v23.0"`, `BASE`, `TOKEN_ERROR_CODE = 190`, `InstagramError(RuntimeError)` com atributo `code`, `InstagramClient(user_id, token, *, session=None, sleep=time.sleep, poll_seconds=10, max_polls=60)` com `publish_reel(video_url, caption) -> str` e `publish_carousel(image_urls, caption) -> str` (retornam o id da mídia publicada)

Fluxo da API: criar container (`POST /{user}/media`) → aguardar `status_code == FINISHED` (`GET /{container}?fields=status_code,status`) → `POST /{user}/media_publish`. Se a versão `v23.0` for descontinuada, troque `API_VERSION` pela versão vigente na documentação da Meta.

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_instagram.py`:
```python
import pytest

from publisher.instagram import BASE, InstagramClient, InstagramError


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self.payload = status, payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self, method, url, data):
        self.calls.append((method, url.removeprefix(BASE + "/"), data))
        return self.responses.pop(0)

    def post(self, url, data=None, timeout=None):
        return self._next("POST", url, data)

    def get(self, url, params=None, timeout=None):
        return self._next("GET", url, params)


def ok(payload):
    return FakeResponse(200, payload)


def make_client(responses):
    session = FakeSession(responses)
    return InstagramClient("178", "tok", session=session, sleep=lambda s: None, max_polls=3), session


def test_publish_reel_waits_for_container_then_publishes():
    client, session = make_client([ok({"id": "c1"}), ok({"status_code": "IN_PROGRESS"}),
                                   ok({"status_code": "FINISHED"}), ok({"id": "m1"})])
    assert client.publish_reel("https://x/reel.mp4", "legenda") == "m1"
    assert session.calls[0] == ("POST", "178/media", {"media_type": "REELS", "video_url": "https://x/reel.mp4",
                                                       "caption": "legenda", "share_to_feed": "true",
                                                       "access_token": "tok"})
    assert session.calls[1][:2] == ("GET", "c1")
    assert session.calls[-1] == ("POST", "178/media_publish", {"creation_id": "c1", "access_token": "tok"})


def test_publish_carousel_creates_children_then_parent():
    client, session = make_client([ok({"id": "i1"}), ok({"id": "i2"}), ok({"status_code": "FINISHED"}),
                                   ok({"status_code": "FINISHED"}), ok({"id": "car"}),
                                   ok({"status_code": "FINISHED"}), ok({"id": "m2"})])
    assert client.publish_carousel(["https://x/1.jpg", "https://x/2.jpg"], "legenda") == "m2"
    assert session.calls[0][2]["is_carousel_item"] == "true"
    assert session.calls[4][2]["media_type"] == "CAROUSEL"
    assert session.calls[4][2]["children"] == "i1,i2"


def test_container_error_status_raises():
    client, _ = make_client([ok({"id": "c1"}), ok({"status_code": "ERROR", "status": "bad video"})])
    with pytest.raises(InstagramError, match="status ERROR"):
        client.publish_reel("u", "x")


def test_container_timeout_raises():
    client, _ = make_client([ok({"id": "c1"})] + [ok({"status_code": "IN_PROGRESS"})] * 3)
    with pytest.raises(InstagramError, match="not ready"):
        client.publish_reel("u", "x")


def test_api_error_keeps_code():
    client, _ = make_client([FakeResponse(400, {"error": {"message": "Error validating access token",
                                                          "code": 190}})])
    with pytest.raises(InstagramError) as info:
        client.publish_reel("u", "x")
    assert info.value.code == 190
    assert "Error validating access token" in str(info.value)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_instagram.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'publisher.instagram'`

- [ ] **Step 3: Implementar**

`publisher/instagram.py`:
```python
"""Instagram API with Instagram Login: publish reels and carousels from public media URLs."""
import time

import requests

API_VERSION = "v23.0"
BASE = f"https://graph.instagram.com/{API_VERSION}"
TOKEN_ERROR_CODE = 190


class InstagramError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


class InstagramClient:
    def __init__(self, user_id: str, token: str, *, session=None, sleep=time.sleep, poll_seconds=10, max_polls=60):
        self.user_id = user_id
        self.token = token
        self.session = session or requests.Session()
        self.sleep = sleep
        self.poll_seconds = poll_seconds
        self.max_polls = max_polls

    def _post(self, path: str, **fields) -> dict:
        response = self.session.post(f"{BASE}/{path}", data={**fields, "access_token": self.token}, timeout=60)
        return self._json(response)

    def _get(self, path: str, **params) -> dict:
        response = self.session.get(f"{BASE}/{path}", params={**params, "access_token": self.token}, timeout=60)
        return self._json(response)

    @staticmethod
    def _json(response) -> dict:
        try:
            data = response.json()
        except ValueError:
            raise InstagramError(f"HTTP {response.status_code}: non-JSON response")
        if response.status_code >= 400 or "error" in data:
            error = data.get("error", {})
            raise InstagramError(f"HTTP {response.status_code}: {error.get('message', 'unknown error')}",
                                 code=error.get("code"))
        return data

    def wait_until_ready(self, container_id: str) -> None:
        for _ in range(self.max_polls):
            data = self._get(container_id, fields="status_code,status")
            status = data.get("status_code")
            if status == "FINISHED":
                return
            if status in ("ERROR", "EXPIRED"):
                raise InstagramError(f"container {container_id} status {status}: {data.get('status', '')}")
            self.sleep(self.poll_seconds)
        raise InstagramError(f"container {container_id} not ready after {self.max_polls * self.poll_seconds}s")

    def _publish(self, container_id: str) -> str:
        self.wait_until_ready(container_id)
        return self._post(f"{self.user_id}/media_publish", creation_id=container_id)["id"]

    def publish_reel(self, video_url: str, caption: str) -> str:
        container = self._post(f"{self.user_id}/media", media_type="REELS", video_url=video_url,
                               caption=caption, share_to_feed="true")["id"]
        return self._publish(container)

    def publish_carousel(self, image_urls: list[str], caption: str) -> str:
        children = [self._post(f"{self.user_id}/media", image_url=url, is_carousel_item="true")["id"]
                    for url in image_urls]
        for child in children:
            self.wait_until_ready(child)
        container = self._post(f"{self.user_id}/media", media_type="CAROUSEL", children=",".join(children),
                               caption=caption)["id"]
        return self._publish(container)
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_instagram.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add publisher/instagram.py tests/test_instagram.py
git commit -m "feat: add Instagram publishing client"
```

---

### Task 17: Publicador (`publisher/run.py`)

**Files:**
- Create: `publisher/run.py`
- Test: `tests/test_publisher_run.py`

**Interfaces:**
- Consumes: `InstagramClient.publish_reel/publish_carousel`, `InstagramError.code`, `TOKEN_ERROR_CODE`, `post_queue.due_entries/mark_published/mark_failed/MAX_ATTEMPTS/load_queue/save_queue`
- Produces: `RunResult(published, retrying, failed)`, `media_urls(entry, base_url) -> list[str]`, `publish_due(queue, client, base_url, now, *, only=None, dry_run=False, log=print) -> RunResult`, CLI `python -m publisher.run [--dry-run] [--only ID] [--now ISO] [--queue PATH]` (exit 1 se algum item desistiu após 3 tentativas ou token inválido)

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_publisher_run.py`:
```python
from datetime import timedelta

import pytest
import requests

from factories import NOW, make_carousel, make_reel
from publisher.instagram import InstagramError
from publisher.run import media_urls, publish_due
from shared.post_queue import make_entry

BASE_URL = "https://user.github.io/stoic-autopilot"


def quiet(message):
    pass


class FakeClient:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    def publish_reel(self, url, caption):
        self.calls.append(("reel", url))
        if self.error:
            raise self.error
        return "ig-reel"

    def publish_carousel(self, urls, caption):
        self.calls.append(("carousel", urls))
        if self.error:
            raise self.error
        return "ig-carousel"


def due_reel():
    return make_entry(make_reel(1, NOW - timedelta(minutes=5)), ["reel.mp4"])


def test_media_urls():
    entry = make_entry(make_carousel(1, NOW), ["slide-01.jpg", "slide-02.jpg"])
    assert media_urls(entry, BASE_URL) == [f"{BASE_URL}/media/2026-10-19-c1/slide-01.jpg",
                                           f"{BASE_URL}/media/2026-10-19-c1/slide-02.jpg"]


def test_publishes_due_entries_only():
    due, later = due_reel(), make_entry(make_reel(2, NOW + timedelta(hours=1)), ["reel.mp4"])
    client = FakeClient()
    result = publish_due([due, later], client, BASE_URL, NOW, log=quiet)
    assert result.published == [due["id"]]
    assert client.calls == [("reel", f"{BASE_URL}/media/{due['id']}/reel.mp4")]
    assert due["platforms"]["instagram"]["published_id"] == "ig-reel"
    assert later["platforms"]["instagram"]["status"] == "pending"


def test_dry_run_does_not_call_client_or_change_queue():
    entry = due_reel()
    result = publish_due([entry], None, BASE_URL, NOW, dry_run=True, log=quiet)
    assert result.published == []
    assert entry["platforms"]["instagram"]["status"] == "pending"


def test_failures_retry_then_give_up():
    entry = due_reel()
    client = FakeClient(InstagramError("HTTP 400: Media download failed", code=9004))
    for _ in range(2):
        result = publish_due([entry], client, BASE_URL, NOW, log=quiet)
        assert result.retrying and not result.failed
    result = publish_due([entry], client, BASE_URL, NOW, log=quiet)
    assert result.failed == [f"{entry['id']}: HTTP 400: Media download failed"]
    assert entry["platforms"]["instagram"]["status"] == "failed"


def test_network_error_counts_as_attempt():
    entry = due_reel()
    result = publish_due([entry], FakeClient(requests.ConnectionError("reset")), BASE_URL, NOW, log=quiet)
    assert result.retrying == [f"{entry['id']}: network error: reset"]
    assert entry["platforms"]["instagram"]["attempts"] == 1


def test_expired_token_aborts_without_spending_attempts():
    entry = due_reel()
    with pytest.raises(InstagramError):
        publish_due([entry], FakeClient(InstagramError("expired", code=190)), BASE_URL, NOW, log=quiet)
    assert entry["platforms"]["instagram"]["attempts"] == 0


def test_only_publishes_a_future_entry_immediately():
    future = make_entry(make_reel(1, NOW + timedelta(days=2)), ["reel.mp4"])
    result = publish_due([future], FakeClient(), BASE_URL, NOW, only=future["id"], log=quiet)
    assert result.published == [future["id"]]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_publisher_run.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'publisher.run'`

- [ ] **Step 3: Implementar**

`publisher/run.py`:
```python
"""Publish due queue entries: `python -m publisher.run [--dry-run] [--only ID] [--now ISO]`."""
import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import requests

from publisher.instagram import TOKEN_ERROR_CODE, InstagramClient, InstagramError
from shared.config import load_settings, require
from shared.post_queue import (MAX_ATTEMPTS, QUEUE_PATH, due_entries, load_queue, mark_failed,
                               mark_published, save_queue)
from shared.timeutil import now_local, parse_time


@dataclass
class RunResult:
    published: list[str] = field(default_factory=list)
    retrying: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


def media_urls(entry: dict, base_url: str) -> list[str]:
    return [f"{base_url}/media/{entry['id']}/{name}" for name in entry["media"]]


def _select(queue, now, only) -> list[dict]:
    if only:
        return [entry for entry in queue
                if entry["id"] == only and entry["platforms"].get("instagram", {}).get("status") == "pending"]
    return due_entries(queue, "instagram", now)


def _publish(client, entry, urls) -> str:
    if entry["type"] == "reel":
        return client.publish_reel(urls[0], entry["caption"])
    return client.publish_carousel(urls, entry["caption"])


def _record_failure(entry, message, result, log) -> None:
    gave_up = mark_failed(entry, "instagram", message)
    (result.failed if gave_up else result.retrying).append(message)
    log(f"{'FAILED' if gave_up else 'retry next hour'}: {message}")


def publish_due(queue, client, base_url, now, *, only=None, dry_run=False, log=print) -> RunResult:
    """Publish due Instagram entries; an invalid token aborts the run without spending attempts."""
    result = RunResult()
    for entry in _select(queue, now, only):
        urls = media_urls(entry, base_url)
        if dry_run:
            log(f"DRY-RUN {entry['scheduled_at']} {entry['type']} {entry['id']} -> {urls}")
            continue
        try:
            published_id = _publish(client, entry, urls)
        except InstagramError as exc:
            if exc.code == TOKEN_ERROR_CODE:
                raise
            _record_failure(entry, f"{entry['id']}: {exc}", result, log)
        except requests.RequestException as exc:
            _record_failure(entry, f"{entry['id']}: network error: {exc}", result, log)
        else:
            mark_published(entry, "instagram", published_id)
            result.published.append(entry["id"])
            log(f"published {entry['id']} -> {published_id}")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Publish due queue entries to Instagram")
    parser.add_argument("--dry-run", action="store_true", help="list what would be published")
    parser.add_argument("--only", metavar="ID", help="publish this pending entry now, ignoring its schedule")
    parser.add_argument("--now", metavar="ISO", help="pretend the current time is this (testing)")
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    args = parser.parse_args(argv)
    settings = load_settings()
    now = parse_time(args.now) if args.now else now_local()
    queue = load_queue(args.queue)
    base_url = require(settings.pages_base_url, "PAGES_BASE_URL")
    client = None if args.dry_run else InstagramClient(require(settings.ig_user_id, "IG_USER_ID"),
                                                       require(settings.ig_access_token, "IG_ACCESS_TOKEN"))
    try:
        result = publish_due(queue, client, base_url, now, only=args.only, dry_run=args.dry_run)
    except InstagramError as exc:
        save_queue(args.queue, queue)
        print(f"ERROR: Instagram token invalid or expired ({exc}). "
              "Generate a new one: docs/setup/accounts.md, section 5.", file=sys.stderr)
        return 1
    if not args.dry_run:
        save_queue(args.queue, queue)
    for message in result.failed:
        print(f"ERROR: gave up after {MAX_ATTEMPTS} attempts: {message}", file=sys.stderr)
    return 1 if result.failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_publisher_run.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add publisher/run.py tests/test_publisher_run.py
git commit -m "feat: publish due queue entries with retries"
```

---

### Task 18: Renovação de token + workflows do GitHub Actions

**Files:**
- Create: `publisher/refresh_token.py`, `.github/workflows/publish.yml`, `.github/workflows/refresh-token.yml`
- Test: `tests/test_refresh_token.py`

**Interfaces:**
- Consumes: `shared.config.load_settings/require`; `publisher.run` CLI
- Produces: `REFRESH_URL`, `refresh_token(token, session=None) -> tuple[str, int]`, CLI `python -m publisher.refresh_token --out FILE` (escreve o token no arquivo; nunca imprime)

- [ ] **Step 1: Escrever o teste que falha**

`tests/test_refresh_token.py`:
```python
import pytest

from publisher.refresh_token import REFRESH_URL, refresh_token


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self.payload = status, payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.response


def test_refresh_returns_new_token_and_lifetime():
    session = FakeSession(FakeResponse(200, {"access_token": "new", "token_type": "bearer",
                                             "expires_in": 5184000}))
    assert refresh_token("old", session=session) == ("new", 5184000)
    assert session.calls == [(REFRESH_URL, {"grant_type": "ig_refresh_token", "access_token": "old"})]


def test_refresh_error_message_never_contains_token():
    session = FakeSession(FakeResponse(400, {"error": {"message": "Session has expired"}}))
    with pytest.raises(RuntimeError) as info:
        refresh_token("secret-old-token", session=session)
    assert "Session has expired" in str(info.value)
    assert "secret-old-token" not in str(info.value)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_refresh_token.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'publisher.refresh_token'`

- [ ] **Step 3: Implementar**

`publisher/refresh_token.py`:
```python
"""Refresh the 60-day Instagram token: `python -m publisher.refresh_token --out FILE` (never prints it)."""
import argparse
import sys
from pathlib import Path

import requests

from shared.config import load_settings, require

REFRESH_URL = "https://graph.instagram.com/refresh_access_token"


def refresh_token(token: str, session=None) -> tuple[str, int]:
    session = session or requests.Session()
    response = session.get(REFRESH_URL, params={"grant_type": "ig_refresh_token", "access_token": token},
                           timeout=30)
    data = response.json()
    if response.status_code >= 400 or "access_token" not in data:
        message = data.get("error", {}).get("message", "unknown error")
        raise RuntimeError(f"token refresh failed: HTTP {response.status_code}: {message}")
    return data["access_token"], int(data.get("expires_in", 0))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Refresh the Instagram long-lived token")
    parser.add_argument("--out", type=Path, required=True, help="file that receives the new token")
    args = parser.parse_args(argv)
    token, expires_in = refresh_token(require(load_settings().ig_access_token, "IG_ACCESS_TOKEN"))
    args.out.write_text(token, encoding="utf-8")
    print(f"token refreshed; valid for {expires_in // 86400} days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

`.github/workflows/publish.yml`:
```yaml
name: publish

on:
  schedule:
    - cron: "5 * * * *"
  workflow_dispatch:
    inputs:
      only:
        description: "Publish this queue id now (ignores its schedule)"
        required: false
        default: ""
      dry_run:
        description: "Only list what would be published"
        type: boolean
        default: false

permissions:
  contents: write

concurrency:
  group: publish
  cancel-in-progress: false

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-publisher.txt
      - name: Publish due posts
        env:
          IG_USER_ID: ${{ secrets.IG_USER_ID }}
          IG_ACCESS_TOKEN: ${{ secrets.IG_ACCESS_TOKEN }}
          PAGES_BASE_URL: ${{ vars.PAGES_BASE_URL }}
          ONLY: ${{ inputs.only }}
          DRY_RUN: ${{ inputs.dry_run }}
        run: |
          args=()
          if [ -n "$ONLY" ]; then args+=(--only "$ONLY"); fi
          if [ "$DRY_RUN" = "true" ]; then args+=(--dry-run); fi
          python -m publisher.run "${args[@]}"
      - name: Commit queue status
        if: always()
        run: |
          if git diff --quiet queue.json; then exit 0; fi
          git config user.name "stoic-autopilot"
          git config user.email "stoic-autopilot@users.noreply.github.com"
          git commit -m "chore: update queue status" queue.json
          git pull --rebase
          git push
```

`.github/workflows/refresh-token.yml`:
```yaml
name: refresh-token

on:
  schedule:
    - cron: "0 12 * * 1"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-publisher.txt
      - name: Refresh token
        env:
          IG_ACCESS_TOKEN: ${{ secrets.IG_ACCESS_TOKEN }}
        run: python -m publisher.refresh_token --out "$RUNNER_TEMP/ig_token"
      - name: Store new token
        env:
          GH_TOKEN: ${{ secrets.GH_SECRETS_PAT }}
        run: gh secret set IG_ACCESS_TOKEN --repo "$GITHUB_REPOSITORY" < "$RUNNER_TEMP/ig_token"
```

- [ ] **Step 4: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_refresh_token.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add publisher/refresh_token.py .github/ tests/test_refresh_token.py
git commit -m "feat: add token refresh and GitHub Actions workflows"
```

---

### Task 19: Site (links da bio, privacidade, termos)

**Files:**
- Create: `site/index.html`, `site/privacy.html`, `site/terms.html`
- Test: `tests/test_site.py`

**Interfaces:**
- Produces: páginas servidas na raiz do GitHub Pages (`assemble` copia `site/`). `privacy.html` e `terms.html` são exigidas pela auditoria do TikTok.

- [ ] **Step 1: Pedir ao usuário o e-mail de contato**

Pergunte qual e-mail pode aparecer publicamente nas páginas de privacidade e termos. Use-o no lugar de `CONTATO@EXEMPLO.COM` nos passos abaixo.

- [ ] **Step 2: Escrever o teste que falha**

`tests/test_site.py`:
```python
from shared.config import ROOT

SITE = ROOT / "site"


def test_index_links_policies_and_books():
    index = (SITE / "index.html").read_text(encoding="utf-8")
    assert 'href="privacy.html"' in index and 'href="terms.html"' in index
    assert "amazon.com.br" in index


def test_policy_pages_are_complete():
    for page in ("privacy.html", "terms.html"):
        html = (SITE / page).read_text(encoding="utf-8")
        assert html.lower().startswith("<!doctype html>")
        assert "CONTATO@EXEMPLO.COM" not in html
        assert "mailto:" in html
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `.venv/Scripts/python -m pytest tests/test_site.py -v`
Expected: FAIL com `FileNotFoundError` em `site/index.html`

- [ ] **Step 4: Escrever as páginas**

`site/index.html`:
```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Livros estoicos</title>
<style>
  body { margin: 0; background: #111; color: #f2ede4; font-family: Georgia, serif; }
  main { max-width: 560px; margin: 0 auto; padding: 48px 16px; }
  h1 { font-size: 32px; margin: 0 0 8px; }
  p { color: #b9b2a5; }
  a.book { display: block; padding: 16px; margin: 12px 0; border: 1px solid #d4af37; border-radius: 10px;
           color: #f2ede4; text-decoration: none; }
  a.book span { display: block; color: #b9b2a5; font-size: 14px; margin-top: 4px; }
  footer { margin-top: 40px; font-size: 13px; }
  footer a { color: #8c8578; }
</style>
</head>
<body>
<main>
  <h1>Comece pelos clássicos</h1>
  <p>Os livros citados nos nossos vídeos.</p>
  <a class="book" href="https://www.amazon.com.br/s?k=Medita%C3%A7%C3%B5es+Marco+Aur%C3%A9lio">Meditações<span>Marco Aurélio</span></a>
  <a class="book" href="https://www.amazon.com.br/s?k=Cartas+a+Luc%C3%ADlio+S%C3%AAneca">Cartas a Lucílio<span>Sêneca</span></a>
  <a class="book" href="https://www.amazon.com.br/s?k=Sobre+a+brevidade+da+vida+S%C3%AAneca">Sobre a brevidade da vida<span>Sêneca</span></a>
  <a class="book" href="https://www.amazon.com.br/s?k=Manual+de+Epicteto">Manual (Enchiridion)<span>Epicteto</span></a>
  <a class="book" href="https://www.amazon.com.br/s?k=Di%C3%A1rio+Estoico+Ryan+Holiday">Diário Estoico<span>Ryan Holiday</span></a>
  <footer><a href="privacy.html">Privacidade</a> · <a href="terms.html">Termos</a></footer>
</main>
</body>
</html>
```

`site/privacy.html` (troque `CONTATO@EXEMPLO.COM` pelo e-mail do Step 1):
```html
<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Política de privacidade</title>
<style>body{margin:0;background:#111;color:#f2ede4;font-family:Georgia,serif}main{max-width:680px;margin:0 auto;padding:48px 16px;line-height:1.6}a{color:#d4af37}</style>
</head>
<body><main>
<h1>Política de privacidade — Stoic Autopilot</h1>
<p>Stoic Autopilot é uma ferramenta pessoal que publica conteúdo próprio sobre filosofia estoica nas contas do próprio autor no Instagram e no TikTok.</p>
<p>A ferramenta não coleta, armazena nem processa dados de outros usuários. Ela usa apenas os tokens de acesso das contas do próprio autor, guardados de forma criptografada como segredos do GitHub, para publicar vídeos e imagens.</p>
<p>Nenhum dado é vendido ou compartilhado com terceiros. Os links de livros podem ser links de afiliado; a loja de destino tem sua própria política de privacidade.</p>
<h2>English summary</h2>
<p>Stoic Autopilot is a personal tool that publishes the author's own content to the author's own accounts. It does not collect or process data from other users and shares no data with third parties.</p>
<p>Contato / Contact: <a href="mailto:CONTATO@EXEMPLO.COM">CONTATO@EXEMPLO.COM</a></p>
</main></body>
</html>
```

`site/terms.html` (mesma troca de e-mail):
```html
<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Termos de uso</title>
<style>body{margin:0;background:#111;color:#f2ede4;font-family:Georgia,serif}main{max-width:680px;margin:0 auto;padding:48px 16px;line-height:1.6}a{color:#d4af37}</style>
</head>
<body><main>
<h1>Termos de uso — Stoic Autopilot</h1>
<p>Stoic Autopilot é usado exclusivamente pelo seu autor para publicar conteúdo próprio nas suas contas. Não há cadastro nem uso por terceiros.</p>
<p>O conteúdo publicado tem caráter educativo e não constitui aconselhamento profissional. Citações são de obras clássicas em domínio público, traduzidas pelo autor, sempre com referência.</p>
<p>Links de livros podem ser links de afiliado; compras são feitas diretamente na loja de destino.</p>
<h2>English summary</h2>
<p>Stoic Autopilot is used solely by its author to publish the author's own educational content. No third-party users.</p>
<p>Contato / Contact: <a href="mailto:CONTATO@EXEMPLO.COM">CONTATO@EXEMPLO.COM</a></p>
</main></body>
</html>
```

- [ ] **Step 5: Rodar e ver passar**

Run: `.venv/Scripts/python -m pytest tests/test_site.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add site/ tests/test_site.py
git commit -m "feat: add bio links, privacy and terms pages"
```

---

### Task 20: Banco de citações, ROUTINE.md e amostra (gate da Fase 1)

Tarefa de conteúdo, executada pelo Claude, com aprovação visual do usuário no fim.

**Files:**
- Create: `ROUTINE.md`, `content/weeks/sample.json`
- Modify: `content/quotes.json` (de `[]` para ~150 citações)

**Interfaces:**
- Consumes: `python -m generator.quotes`, `python -m generator.build_week --preview`
- Produces: banco de citações válido; `ROUTINE.md` (usado nas Tasks 22–23)

- [ ] **Step 1: Escrever `ROUTINE.md`**

````markdown
# Rotina semanal — Stoic Autopilot

Execute na raiz do repositório, em ordem, com `.venv/Scripts/python`. Nunca leia nem imprima `.env`.

1. `git pull --rebase` (o GitHub Actions atualiza `queue.json` durante a semana).
2. `.venv/Scripts/python -m generator.schedule` → JSON com `skip`, `batch`, `reels` (7 horários) e `carousels` (3 horários).
   Se `skip` for `true`: reporte o motivo e pare.
3. Leia `content/quotes.json`, `content/history.json` e os 2 lotes mais recentes de `content/weeks/`.
4. Escreva `content/weeks/<batch>.json` com `"week": "<batch>"` e 10 itens:
   - reels `<batch>-r1` … `<batch>-r7` nos horários de `reels`, na ordem;
   - carrosséis `<batch>-c1` … `<batch>-c3` nos horários de `carousels`, na ordem.

   Regras de conteúdo:
   - pt-BR, tom sóbrio e direto. Sem emoji em `script`, `hook` e `slides`.
   - `pillar` entre `controle`, `adversidade`, `disciplina`, `emocoes`, `memento_mori`; não repita o mesmo pilar em reels de dias seguidos.
   - Só use `quote_id` existente em `content/quotes.json` e ausente de `history.json` nos últimos 60 dias. Nunca invente citação; ao citar, use o `text_pt` literalmente e diga o autor.
   - ~80% estoicos (Marco Aurélio, Sêneca, Epicteto), ~20% outros clássicos.
   - `script` (80–145 palavras): gancho (a frase de `hook`) → ensinamento com a citação literal → aplicação prática para hoje → CTA.
   - `cta`: `affiliate` em 2 ou 3 reels (o script termina com "O livro está no link da bio."); nos demais `follow` ou `save`.
   - `hook`: curto e provocativo, diferente de todos os ganchos dos 2 lotes anteriores.
   - `footage_keywords`: 2–3 termos em inglês, visuais e sóbrios (ex.: "marble statue", "stormy sea", "candle dark").
   - Carrossel: 6–8 `slides` (`title`, `body`, `quote_id` opcional). Slide 1 = capa com gancho; último = CTA ("Salve para reler." / "Siga para mais."). `quote_ids` lista as citações usadas nos slides.
   - `caption`: 2–4 frases + uma pergunta para comentários. `hashtags`: 3–5, sempre com `#estoicismo`.
   - `platforms`: reels `["instagram", "tiktok"]`; carrosséis `["instagram"]`.
5. `.venv/Scripts/python -m generator.build_week content/weeks/<batch>.json`
   - Erro de conteúdo (palavras do roteiro, duração fora de 30–60 s, citação em cooldown, gancho repetido): corrija o JSON e rode de novo — no máximo 2 correções.
   - Se persistir, ou se o erro for de ambiente (ffmpeg, rede, chave ausente): NÃO faça push. Reporte os erros ao usuário e pare.
6. `.venv/Scripts/python -m generator.deploy_media`
7. `git add content queue.json` → `git commit -m "content: batch <batch>" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"` → `git push` (se rejeitado: `git pull --rebase` e push de novo).
8. Reporte: o batch, os 10 itens com horário e gancho, e o lembrete de que os reels do TikTok estão em `output/<id>/reel.mp4` para upload manual.
````

- [ ] **Step 2: Montar o banco de citações**

Para cada citação, busque o texto-fonte em tradução inglesa de domínio público (Wikisource ou Project Gutenberg), copie o trecho exato para `text_source`, traduza para pt-BR em `text_pt` e preencha a referência exata. Fontes:
- Marco Aurélio, *Meditações* — tradução George Long (Wikisource "The Thoughts of the Emperor Marcus Aurelius Antoninus"). ~50 citações. `work`: "Meditações", `reference`: "4.3".
- Sêneca, *Cartas a Lucílio* — tradução Richard M. Gummere (Wikisource "Moral letters to Lucilius"). ~45 citações. `work`: "Cartas a Lucílio", `reference`: "13.4". Também *Sobre a brevidade da vida* (trad. John W. Basore, Wikisource "On the shortness of life"), ~10.
- Epicteto, *Manual (Enchiridion)* e *Discursos* — traduções de domínio público (Elizabeth Carter, George Long ou T. W. Higginson). ~30 citações.
- Outros clássicos (~15): Sócrates via Platão, *Apologia* (trad. Benjamin Jowett); Schopenhauer (trad. T. Bailey Saunders).

Formato de cada entrada (ids `<autor>-<obra>-<ref>`):
```json
{
  "id": "seneca-letters-13-4",
  "author": "Sêneca",
  "work": "Cartas a Lucílio",
  "reference": "13.4",
  "text_pt": "Há mais coisas que nos assustam do que coisas que nos esmagam; sofremos mais na imaginação do que na realidade.",
  "text_source": "There are more things, Lucilius, likely to frighten us than there are to crush us; we suffer more often in imagination than in reality.",
  "source_url": "https://en.wikisource.org/wiki/Moral_letters_to_Lucilius/Letter_13"
}
```
Regra: se não encontrar o trecho na fonte, a citação **não entra**.

- [ ] **Step 3: Validar o banco**

Run: `.venv/Scripts/python -m generator.quotes`
Expected: `150 quotes, 0 errors` (número aproximado; 0 errors obrigatório)

- [ ] **Step 4: Escrever a amostra**

Crie `content/weeks/sample.json` com `"week": "sample"`, um reel `sample-r1` e um carrossel `sample-c1` seguindo as regras de conteúdo do `ROUTINE.md`. `scheduled_at` = hoje + 1 hora para os dois (ISO com `-03:00`); o publicador só usa essa data na Task 21 via `--only`.

- [ ] **Step 5: Renderizar a amostra**

Pré-requisitos do usuário: `.env` com `PEXELS_API_KEY` e `IG_HANDLE`; trilhas em `generator/music/` (opcional).
Run: `.venv/Scripts/python -m generator.build_week content/weeks/sample.json --preview sample-r1`
Run: `.venv/Scripts/python -m generator.build_week content/weeks/sample.json --preview sample-c1`
Expected: `OK` nos dois. Arquivos em `output/sample-r1/reel.mp4` e `output/sample-c1/slide-01.jpg`…

- [ ] **Step 6: GATE — aprovação visual do usuário**

Envie `output/sample-r1/reel.mp4` e 2–3 slides ao usuário e pergunte se o visual, a voz e o ritmo estão aprovados. Ajustes de estilo vão em `generator/captions.py` (fonte/cores), `generator/templates/carousel.html` e `MUSIC_VOLUME`. Re-renderize até aprovar. **Não siga para a Task 21 sem aprovação.**

- [ ] **Step 7: Commit**

```bash
git add ROUTINE.md content/quotes.json content/weeks/sample.json
git commit -m "content: seed verified quote bank, routine and sample batch"
```

---

### Task 21: Spike de hospedagem (gate da Fase 2)

Primeira publicação real. Ações externas: cada passo marcado com **(usuário aprova)** exige um "sim" explícito no chat antes.

**Files:**
- Modify: `queue.json` (entrada `sample-r1`)

- [ ] **Step 1: Pré-requisitos (Task 1)**

Confirme com o usuário: Instagram aquecido há 5–7 dias, token e `IG_USER_ID` em mãos, PAT do GitHub criado.

- [ ] **Step 2: Criar o repositório (usuário aprova)**

Run: `gh repo create stoic-autopilot --public --source . --push`
Expected: repositório criado e `main` enviado. O usuário então cadastra Secrets e a Variable conforme `docs/setup/accounts.md` seção 7.

- [ ] **Step 3: Enfileirar a amostra**

Run: `.venv/Scripts/python -m generator.build_week content/weeks/sample.json --preview sample-r1 --enqueue`
Expected: `OK`; `queue.json` contém `sample-r1` com instagram `pending`.

- [ ] **Step 4: Publicar a mídia e ativar o Pages (usuário aprova)**

Run: `.venv/Scripts/python -m generator.deploy_media`
Expected: `OK: gh-pages updated`.
Ative o Pages: `gh api -X POST repos/{owner}/stoic-autopilot/pages -f "source[branch]=gh-pages" -f "source[path]=/"` (ou pela tela Settings → Pages). Aguarde ~2 minutos.
Run: `curl -sI "$PAGES_BASE_URL/media/sample-r1/reel.mp4"` (com o valor da Variable)
Expected: `HTTP/2 200` e `content-type: video/mp4`.

- [ ] **Step 5: Commitar a fila**

```bash
git add queue.json
git commit -m "chore: queue sample reel for hosting spike"
git push
```

- [ ] **Step 6: Publicar de verdade (usuário aprova — post público)**

Run: `gh workflow run publish.yml -f only=sample-r1` e depois `gh run watch`
Expected: job verde; log `published sample-r1 -> <id>`; reel visível no perfil; após `git pull`, `queue.json` com `published_id`.

- [ ] **Step 7: GATE — resultado**

- Sucesso → seguir para a Task 22. Envie também a auditoria do TikTok (Task 1, seção 9), já que o site está no ar.
- Erro de download da mídia (ex.: "Media download failed" / código 9004 / container `ERROR`) → PARE. Reporte ao usuário e revise o plano para usar upload resumível da API do Instagram (`upload_type=resumable` + `rupload.facebook.com`), que dispensa URL pública para reels.

---

### Task 22: Primeiro lote completo + dry-run + semana real (gate da Fase 3)

**Files:**
- Create: `content/weeks/<batch>.json`
- Modify: `queue.json`, `content/history.json`

- [ ] **Step 1: Gerar o lote seguindo o `ROUTINE.md` até o passo 6**

Execute os passos 1–6 do `ROUTINE.md` (não faça o passo 7 ainda).
Expected: `build_week` imprime `OK`; `deploy_media` imprime `OK: gh-pages updated`.

- [ ] **Step 2: Dry-run da semana inteira**

Run: `.venv/Scripts/python -m publisher.run --dry-run --now <último horário de reels do schedule>`
Expected: 10 linhas `DRY-RUN ...` (7 reels + 3 carrosséis) com URLs `.../media/<id>/...`; `queue.json` inalterado.

- [ ] **Step 3: GATE — revisão do lote pelo usuário**

Mostre ao usuário os 10 ganchos, horários e 1–2 reels renderizados. Correções: edite o JSON, rode `build_week` e `deploy_media` de novo.

- [ ] **Step 4: Liberar a semana (usuário aprova)**

Execute o passo 7 do `ROUTINE.md` (commit + push).
Expected: a partir do primeiro horário, o workflow `publish` publica sozinho de hora em hora.

- [ ] **Step 5: Conferir o primeiro dia**

Após o primeiro horário: `gh run list --workflow publish.yml --limit 3` e `git pull`.
Expected: run verde; primeiro item `published` em `queue.json`.

---

### Task 23: Rotina semanal agendada (Fase 4)

**Files:** nenhum arquivo do repositório; cria a tarefa agendada no app.

- [ ] **Step 1: Mover o projeto para pasta permanente**

Antes de agendar, confirme que o repositório está numa pasta permanente escolhida pelo usuário (não na pasta temporária da sessão).

- [ ] **Step 2: Criar a tarefa agendada**

Use a skill `anthropic-skills:schedule` para criar a tarefa local:
- nome: `stoic-autopilot-weekly`
- quando: toda segunda-feira às 08:00
- pasta: a raiz do repositório
- prompt: `Execute a rotina semanal descrita em ROUTINE.md neste repositório, passo a passo, e reporte o resultado.`

- [ ] **Step 3: Testar a tarefa agora**

Rode a tarefa manualmente uma vez.
Expected: como a fila já tem a semana da Task 22, `generator.schedule` devolve `skip: true` e a rotina reporta "queue already scheduled until ..." sem criar lote.

- [ ] **Step 4: Critério de sucesso**

Acompanhe as próximas 2 segundas-feiras: lote criado sozinho, `publish` verde todos os dias, `refresh-token` verde. Sucesso = 2 semanas seguidas sem intervenção.

---

## Fora deste plano (Fase 5, plano próprio)

- `publisher/tiktok.py` + `TIKTOK_AUTOMATED = True` após aprovação da auditoria.
- Rotina mensal que amplia `content/quotes.json` com verificação de fonte.
- Trocar os links de busca de `site/index.html` por links de afiliado da Amazon Associados.
