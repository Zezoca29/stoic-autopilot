---
status: ativo
owner: kaique
stack: python3.13, edge-tts, ffmpeg, playwright, jinja2, pytest, github-actions, github-pages, instagram-graph-api
updated: 2026-10-15
---
# stoic-autopilot

Gera toda semana 7 reels narrados e 3 carrosséis de estoicismo em pt-BR e publica sozinho no Instagram via GitHub Actions (TikTok em upload manual até a auditoria). Custo zero além da assinatura do Claude.

## Comandos

| Ação | Onde | Comando |
|---|---|---|
| instalar | raiz | `python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt && .venv/Scripts/python -m playwright install chromium` |
| testar | raiz | `.venv/Scripts/python -m pytest` |
| testar voz real | raiz | `.venv/Scripts/python -m pytest -m network` |
| slots do próximo lote | raiz | `.venv/Scripts/python -m generator.schedule` |
| gerar lote | raiz | `.venv/Scripts/python -m generator.build_week content/weeks/<lote>.json` |
| prévia de um item | raiz | `.venv/Scripts/python -m generator.build_week <lote.json> --preview <id>` |
| publicar mídia (gh-pages) | raiz | `.venv/Scripts/python -m generator.deploy_media` |
| simular publicação | raiz | `.venv/Scripts/python -m publisher.run --dry-run --now <ISO>` |

ffmpeg (com libass) precisa estar no PATH.

## Convenções

- Design aprovado: `docs/superpowers/specs/2026-10-14-stoic-autopilot-design.md`. Plano: `docs/superpowers/plans/2026-10-14-stoic-autopilot.md`.
- Citações só de `content/quotes.json`, com referência exata; nunca inventar citação.
- `generator/` roda no PC; `publisher/` roda no GitHub Actions e só depende de `requirements-publisher.txt`; `shared/` é usado pelos dois.
- Todo timestamp é ISO 8601 com offset (`America/Sao_Paulo`).
- Segredos ficam no `.env` local e nos GitHub Secrets; nunca ler, imprimir ou commitar. Modelo em `env.example`.
- Rotina semanal do Claude: `ROUTINE.md` (criado na Task 20).
