# Status — stoic-autopilot

Atualizado em 2026-10-15.

## Agora

- Branch `feat/stoic-autopilot`: Tasks 1–22 do plano concluídas (visual v2 aprovado em 2026-10-16), revisão final feita e achados críticos/importantes corrigidos. Código na `main` de https://github.com/Zezoca29/stoic-autopilot (público, criado em 2026-10-22). Nada publicado ainda.
- Reel real de teste gerado de ponta a ponta (`output/amostra-teste.mp4`, 40 s, fundo reserva, sem música).

## Pendências

- 2026-10-22 — Task 22 concluída: lote 2026-10-26 (7 reels + 3 carrosséis, 26/10–01/11) liberado na fila. Task 23: rotina agendada no app (tarefa `fortaleza-interior-weekly`, segundas 08:05, modo Auto). Em 26/10 deve só reportar "skip" (fila cheia); em 02/11 gera o primeiro lote sozinha. Critério de sucesso: 2 semanas seguidas sem intervenção.
- 2026-10-15 — Tasks 22–23: primeira semana completa (dry-run + publicação) e rotina semanal agendada. Dependem das contas (`docs/setup/accounts.md`).
- 2026-10-22 — Instagram criado: Fortaleza Interior (`@fortalezainterior.br`), conta pública de Criador. App Meta `stoic-autopilot` com `instagram_business_basic` e `instagram_business_content_publish`; testador aceito; token gerado e verificado (2026-10-22: /me responde fortalezainterior.br, ID confere). Repositório, variável `PAGES_BASE_URL` e os 3 secrets configurados; workflow `publish` em simulação passou no Actions (2026-10-22). Primeira publicação automática feita em 2026-10-22: reel https://www.instagram.com/reel/DezyQzQiLcX/ e carrossel https://www.instagram.com/p/DezyYP2mEJF/ — hospedagem via GitHub Pages aceita pela API.
- 2026-10-22 — Amazon Associados ativo (ID `fortalezain08-20`); links da página com a tag e aviso de afiliado. Prazo: uma venda pelo link até ~20/04/2027, senão a conta é revogada. Links apontam para páginas de produto (/dp/) desde 2026-10-22, incluindo o Box Biblioteca Estoica.
- 2026-10-22 — Isca gratuita no ar: "Mini Diário Estoico — 7 dias" para download direto na página da bio (`site/mini-diario-estoico-7-dias.pdf`, gerado por `python -m products.mini_diario.build`). A Kiwify exige preço mínimo de R$ 5, então não coleta e-mail por enquanto; a Kiwify fica para o Diário de 30 dias pago.
- 2026-10-22 — Produto pago pronto: "Diário Estoico — 30 dias" (43 páginas), gerado por `python -m products.diario_30.build` em `products/diario_30/dist/`. O texto (`products/diario_30/content.json`) fica FORA do git (repositório público): faça backup. Falta: cadastrar na Kiwify (preço sugerido R$ 27).
- Adiados da revisão: timeout ambíguo no `media_publish` pode duplicar um post; token renovado sem `::add-mask::`.

## Como verificar

| Comando | Resultado esperado (2026-10-15) |
|---|---|
| `.venv/Scripts/python -m pytest` | 106 passando, 1 desmarcado (`network`) |
| `.venv/Scripts/python -m pytest -m network` | 1 passando (depende do serviço de voz da Microsoft estar no ar) |
