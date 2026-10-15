# Status — stoic-autopilot

Atualizado em 2026-10-15.

## Agora

- Branch `feat/stoic-autopilot`: Tasks 1–18 do plano implementadas, revisão final feita e achados críticos/importantes corrigidos. Nada publicado ainda; sem remote.
- Reel real de teste gerado de ponta a ponta (`output/amostra-teste.mp4`, 40 s, fundo reserva, sem música).

## Pendências

- 2026-10-15 — Task 19: páginas `site/` (links, privacidade, termos); falta o e-mail de contato público.
- 2026-10-15 — Task 20: banco de ~150 citações verificadas, `ROUTINE.md`, amostra e aprovação visual (precisa de `PEXELS_API_KEY` e `IG_HANDLE` no `.env`).
- 2026-10-15 — Tasks 21–23: repositório no GitHub, primeira publicação real, primeira semana e rotina agendada. Dependem das contas (`docs/setup/accounts.md`).
- 2026-10-15 — Nome do perfil escolhido: Fortaleza Interior (`@fortalezainterior`); falta confirmar se o @ está livre no Instagram e no TikTok.
- Adiados da revisão: timeout ambíguo no `media_publish` pode duplicar um post; token renovado sem `::add-mask::`.

## Como verificar

| Comando | Resultado esperado (2026-10-15) |
|---|---|
| `.venv/Scripts/python -m pytest` | 92 passando, 1 desmarcado (`network`) |
| `.venv/Scripts/python -m pytest -m network` | 1 passando (depende do serviço de voz da Microsoft estar no ar) |
