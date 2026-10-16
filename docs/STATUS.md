# Status — stoic-autopilot

Atualizado em 2026-10-15.

## Agora

- Branch `feat/stoic-autopilot`: Tasks 1–20 do plano concluídas (visual v2 aprovado em 2026-10-16), revisão final feita e achados críticos/importantes corrigidos. Nada publicado ainda; sem remote.
- Reel real de teste gerado de ponta a ponta (`output/amostra-teste.mp4`, 40 s, fundo reserva, sem música).

## Pendências

- 2026-10-16 — Task 21: criar o repositório no GitHub, cadastrar secrets e fazer a primeira publicação real (spike de hospedagem). Depende do Instagram aquecido por 5–7 dias e do token da Meta.
- 2026-10-15 — Tasks 22–23: primeira semana completa (dry-run + publicação) e rotina semanal agendada. Dependem das contas (`docs/setup/accounts.md`).
- 2026-10-15 — Nome do perfil escolhido: Fortaleza Interior (`@fortalezainterior`); falta confirmar se o @ está livre no Instagram e no TikTok.
- Adiados da revisão: timeout ambíguo no `media_publish` pode duplicar um post; token renovado sem `::add-mask::`.

## Como verificar

| Comando | Resultado esperado (2026-10-15) |
|---|---|
| `.venv/Scripts/python -m pytest` | 106 passando, 1 desmarcado (`network`) |
| `.venv/Scripts/python -m pytest -m network` | 1 passando (depende do serviço de voz da Microsoft estar no ar) |
