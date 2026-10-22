# Status — stoic-autopilot

Atualizado em 2026-10-15.

## Agora

- Branch `feat/stoic-autopilot`: Tasks 1–21 do plano concluídas (visual v2 aprovado em 2026-10-16), revisão final feita e achados críticos/importantes corrigidos. Código na `main` de https://github.com/Zezoca29/stoic-autopilot (público, criado em 2026-10-22). Nada publicado ainda.
- Reel real de teste gerado de ponta a ponta (`output/amostra-teste.mp4`, 40 s, fundo reserva, sem música).

## Pendências

- 2026-10-22 — Task 22: gerar o primeiro lote semanal completo (ROUTINE.md), dry-run e liberar a semana.
- 2026-10-15 — Tasks 22–23: primeira semana completa (dry-run + publicação) e rotina semanal agendada. Dependem das contas (`docs/setup/accounts.md`).
- 2026-10-22 — Instagram criado: Fortaleza Interior (`@fortalezainterior.br`), conta pública de Criador. App Meta `stoic-autopilot` com `instagram_business_basic` e `instagram_business_content_publish`; testador aceito; token gerado e verificado (2026-10-22: /me responde fortalezainterior.br, ID confere). Repositório, variável `PAGES_BASE_URL` e os 3 secrets configurados; workflow `publish` em simulação passou no Actions (2026-10-22). Primeira publicação automática feita em 2026-10-22: reel https://www.instagram.com/reel/DezyQzQiLcX/ e carrossel https://www.instagram.com/p/DezyYP2mEJF/ — hospedagem via GitHub Pages aceita pela API.
- Adiados da revisão: timeout ambíguo no `media_publish` pode duplicar um post; token renovado sem `::add-mask::`.

## Como verificar

| Comando | Resultado esperado (2026-10-15) |
|---|---|
| `.venv/Scripts/python -m pytest` | 106 passando, 1 desmarcado (`network`) |
| `.venv/Scripts/python -m pytest -m network` | 1 passando (depende do serviço de voz da Microsoft estar no ar) |
