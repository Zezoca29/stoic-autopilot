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
- Pré-visualizar um item: `.venv/Scripts/python -m generator.build_week <lote.json> --preview <id>`
- Publicar mídia no GitHub Pages: `.venv/Scripts/python -m generator.deploy_media`
- Simular publicação: `.venv/Scripts/python -m publisher.run --dry-run --now 2026-10-25T23:00:00-03:00`
