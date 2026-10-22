# Rotina semanal — Fortaleza Interior (stoic-autopilot)

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
   - `pillar` entre `controle`, `adversidade`, `disciplina`, `emocoes`, `memento_mori`; não repita o mesmo pilar em reels de dias seguidos. O campo `pillar` de cada citação no banco ajuda a escolher.
   - Só use `quote_id` existente em `content/quotes.json` e ausente de `history.json` nos últimos 60 dias. Nunca invente citação; ao citar, use o `text_pt` literalmente e diga o autor.
   - ~80% estoicos (Marco Aurélio, Sêneca, Epicteto), ~20% outros clássicos.
   - `script` (80–145 palavras): gancho (a frase de `hook`) → ensinamento com a citação literal → aplicação prática para hoje → CTA.
   - `cta` dos 7 reels, sem repetir o mesmo tipo em dias seguidos:
     - `affiliate` em 2 reels: o script termina com "O livro está no link da bio.";
     - `freebie` em 1 reel: o script termina com "Baixe grátis o Mini Diário Estoico no link da bio." e a `caption` também menciona o diário grátis no link da bio;
     - `product` em 1 reel: o script termina com "O Diário Estoico completo, com 30 dias de exercícios, está no link da bio." e a `caption` menciona o diário de 30 dias no link da bio. Escolha um tema ligado a hábito e prática diária (disciplina, revisão da noite, constância);
     - `follow` ou `save` nos 3 restantes.
   - Últimos slides dos carrosséis: em 1 dos 3, use `{"title": "Baixe grátis o Mini Diário Estoico", "body": "7 dias de exercícios estoicos. Link na bio."}`; em outro, use `{"title": "Quer praticar por 30 dias?", "body": "O Diário Estoico completo está no link da bio."}`; no terceiro, mantenha "Salve para reler.".
   - `hook`: curto e provocativo, diferente de todos os ganchos dos 2 lotes anteriores.
   - `footage_keywords`: 2–3 termos em inglês, visuais e sóbrios (ex.: "marble statue", "stormy sea", "candle dark").
   - Carrossel: 6–8 `slides` (`title`, `body`, `quote_id` opcional). Slide 1 = capa com gancho; último = CTA ("Salve para reler." / "Siga a Fortaleza Interior."). `quote_ids` lista as citações usadas nos slides.
   - `caption`: 2–4 frases + uma pergunta para comentários. `hashtags`: 3–5, sempre com `#estoicismo`.
   - `platforms`: reels `["instagram", "tiktok"]`; carrosséis `["instagram"]`.
5. `.venv/Scripts/python -m generator.build_week content/weeks/<batch>.json`
   - Erro de conteúdo (palavras do roteiro, duração fora de 30–60 s, citação em cooldown, gancho repetido): corrija o JSON e rode de novo — no máximo 2 correções.
   - Se persistir, ou se o erro for de ambiente (ffmpeg, rede, chave ausente ou rejeitada): NÃO faça push. Reporte os erros ao usuário e pare.
6. `.venv/Scripts/python -m generator.deploy_media`
7. `git add content queue.json` → `git commit -m "content: batch <batch>" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"` → `git push` (se rejeitado: `git pull --rebase` e push de novo).
8. Reporte: o batch, os 10 itens com horário e gancho, e o lembrete de que os reels do TikTok estão em `output/<id>/reel.mp4` para upload manual.
