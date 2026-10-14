# Stoic Autopilot — Design

Data: 2026-10-14
Status: aprovado em conversa, aguardando revisão do documento

## 1. Objetivo

Criar perfis novos de filosofia/estoicismo no Instagram e TikTok, voltados ao público brasileiro (pt-BR), com produção e publicação **100% automáticas e a custo zero** (além da assinatura do Claude já existente).

**Monetização:**
- Fase inicial: afiliados (livros de estoicismo via Amazon Associados), link na bio.
- Fase posterior: produto digital próprio (ebook, diário estoico, desafio de 30 dias), validado pelo engajamento do conteúdo.

**Critério de sucesso da primeira entrega:** pipeline publicando sozinho por **2 semanas seguidas sem intervenção manual**. Métricas de seguidores e vendas são objetivo da fase seguinte, não desta.

## 2. Decisões tomadas

| Tema | Decisão |
|---|---|
| Automação | 100% automática (geração + publicação) |
| Execução | Híbrida: Claude gera o lote 1x/semana no PC local; GitHub Actions publica de hora em hora |
| Ritmo | 1 reel/dia (7/semana) + 3 carrosséis/semana |
| Estilo de reel | Narrado (TTS pt-BR), 30–60s, legenda animada palavra a palavra, vídeo de fundo + trilha livre |
| Stack de geração | Python + ffmpeg (abordagem A); Remotion descartado por peso/licença |
| Plataformas | Reels → Instagram + TikTok; carrosséis → só Instagram |
| Custos | Zero: edge-tts, Pexels API, ffmpeg, Playwright, GitHub (repo público, Pages, Actions) |

## 3. Arquitetura

### 3.1 Repositório

Repositório **público** no GitHub (necessário para Pages e Actions sem limites apertados; o conteúdo é público de qualquer forma).

```
content/
  weeks/YYYY-Www.json     lote semanal escrito pelo Claude
  quotes.json             banco de citações verificadas
  history.json            histórico de citações, ganchos e vídeos usados
generator/
  tts.py                  edge-tts → narration.mp3 + word timings
  captions.py             word timings → legendas animadas (.ass)
  footage.py              busca/baixa vídeos de fundo no Pexels
  render_reel.py          ffmpeg → reel 1080x1920 (H.264/AAC)
  render_carousel.py      templates HTML → PNG 1080x1350 via Playwright
  validate.py             checagens do lote antes do push
  templates/              HTML/CSS dos carrosséis e estilo das legendas
  music/                  trilhas livres de direitos (Pixabay Music)
publisher/
  instagram.py            publica reel/carrossel via Instagram API with Instagram Login
  tiktok.py               publica via Content Posting API (desligado até auditoria)
  token.py                renova o token long-lived da Meta
  run.py                  lê queue.json, publica itens vencidos, atualiza status
site/                     GitHub Pages: página de links/afiliados, privacidade, termos
queue.json                fila de publicação
.github/workflows/
  publish.yml             cron de hora em hora → publisher/run.py
  refresh-token.yml       cron semanal → publisher/token.py
tests/
```

Branch `gh-pages`: hospeda apenas a mídia pendente (URLs públicas para a API do Instagram) e o `site/`. Mídia é removida após publicação; o branch de mídia é reescrito (force-push) para o histórico não crescer.

### 3.2 Formato do lote semanal (`content/weeks/YYYY-Www.json`)

```json
{
  "week": "2026-W43",
  "items": [
    {
      "id": "2026-W43-r1",
      "type": "reel",
      "scheduled_at": "2026-10-20T12:00:00-03:00",
      "pillar": "controle",
      "hook": "Você sofre mais na imaginação do que na realidade.",
      "quote_id": "seneca-letters-13-4",
      "script": "texto completo da narração",
      "footage_keywords": ["marble statue", "stormy sea"],
      "caption": "legenda do post",
      "hashtags": ["#estoicismo", "#seneca", "#filosofia"],
      "cta": "follow | save | affiliate",
      "platforms": ["instagram", "tiktok"]
    },
    {
      "id": "2026-W43-c1",
      "type": "carousel",
      "scheduled_at": "2026-10-21T19:00:00-03:00",
      "pillar": "disciplina",
      "slides": [{"title": "...", "body": "..."}],
      "quote_ids": ["marcus-meditations-5-1"],
      "caption": "...",
      "hashtags": ["..."],
      "platforms": ["instagram"]
    }
  ]
}
```

### 3.3 `queue.json`

Lista de itens com `id`, `type`, `scheduled_at`, `platforms`, `media_urls`, `caption` e, por plataforma, `status` (`pending | published | failed | manual`), `attempts`, `published_id`, `last_error`.

### 3.4 Fluxo semanal

1. **Segunda, 08h (horário local):** tarefa agendada do Claude:
   - lê `history.json` e `quotes.json`;
   - escreve o lote da semana (7 reels + 3 carrosséis);
   - roda o `generator` para cada item;
   - roda `validate.py`;
   - se válido: push da mídia para `gh-pages`, do lote/fila/histórico para `main`;
   - se inválido: não faz push e notifica o usuário (notificação do app).
2. **De hora em hora (GitHub Actions):** `publisher/run.py` publica itens com `scheduled_at <= agora` e status `pending`, marca `published`, remove a mídia publicada de `gh-pages`, commita `queue.json`.
3. **Semanal (GitHub Actions):** `token.py` renova o token da Meta (expira em 60 dias) e atualiza o secret.

Horários padrão: reels às 12:00, carrosséis às 19:00 (America/Sao_Paulo). Atrasos de alguns minutos do cron do Actions são aceitáveis.

## 4. Conteúdo

### 4.1 Pilares

Rotação semanal entre: **controle** (dicotomia do controle), **adversidade**, **disciplina e hábitos**, **emoções** (raiva, ansiedade), **memento mori**. Autores: ~80% estoicos (Marco Aurélio, Sêneca, Epicteto), ~20% outros clássicos (Sócrates, Schopenhauer etc.).

### 4.2 Reel narrado

Estrutura: gancho (0–3s) → ensinamento com citação + referência na tela → aplicação prática → CTA. CTA alterna entre seguir e salvar; 1 a cada 3 reels aponta para o livro do link na bio. Voz fixa: `pt-BR-AntonioNeural`. Trilha de fundo baixa (−20 dB sob a voz), livre de direitos.

Especificação técnica: 1080x1920, 30 fps, H.264 + AAC, duração 30–60s, arquivo < 100 MB.

### 4.3 Carrossel

6–8 slides, 1080x1350. Capa com gancho, conteúdo, slide final com CTA. Template fixo: fundo escuro, tipografia serifada (Google Fonts), uma cor de destaque.

### 4.4 Banco de citações e proteção contra citação falsa

- Setup inicial: banco com ~150 citações em `quotes.json`, cada uma com `id`, autor, obra, livro/seção exata, texto em pt-BR, texto-fonte em inglês e URL da fonte de domínio público.
- Traduções feitas pelo Claude a partir de traduções inglesas em domínio público (ex.: Meditações trad. George Long; Cartas a Lucílio trad. Richard Gummere; Enchiridion trad. Elizabeth Carter). Não copiar traduções brasileiras modernas (protegidas por direito autoral).
- O lote semanal **só pode** referenciar `quote_id` existente no banco; `validate.py` rejeita o lote caso contrário.
- Rotina mensal amplia o banco com verificação da fonte na web.

### 4.5 Variedade (anti "conteúdo repetitivo")

`history.json` impede: mesma citação em menos de 60 dias; mesmo gancho ou mesmo vídeo de fundo na mesma semana.

### 4.6 Afiliados e rótulos

- Bio → página de links no GitHub Pages (`site/`) com livros e links Amazon Associados. Cadastro na Amazon só quando o perfil já estiver postando (exigência de venda nos primeiros 180 dias).
- TikTok: posts marcados como conteúdo gerado por IA (flag da API).
- Bio de ambos os perfis informa "narração com voz sintética".

## 5. Plataformas

### 5.1 Instagram

- Conta Profissional (Criador) + app no Meta for Developers usando **Instagram API with Instagram Login** (não exige Página do Facebook).
- Reel: criar container `REELS` com `video_url` público → aguardar processamento (polling do status) → publicar.
- Carrossel: criar container por imagem → container `CAROUSEL` → publicar.
- Token long-lived (60 dias), renovado semanalmente por workflow.

### 5.2 TikTok

- App de desenvolvedor com Content Posting API. Pedido de auditoria enviado já na Fase 0 (site, política de privacidade e termos hospedados em `site/`).
- Até a auditoria ser aprovada: `tiktok.py` desligado por configuração; itens TikTok ficam com status `manual` e o reel fica disponível para upload manual.
- Após aprovação: publicação automática com flag de conteúdo de IA.

## 6. Tratamento de erros

| Falha | Comportamento |
|---|---|
| Lote inválido (citação fora do banco, duração/resolução fora do padrão) | Não faz push; notifica o usuário; semana anterior não é afetada |
| Pexels sem resultado para a palavra-chave | Tenta palavras-chave genéricas do pilar; depois vídeo de fallback local |
| edge-tts indisponível | Repete 3x com espera; persistindo, aborta o lote e notifica |
| Instagram rejeita mídia / erro de API | `attempts += 1`, nova tentativa na hora seguinte; após 3 falhas → `failed` e o workflow falha (GitHub envia e-mail) |
| Token expirado | Workflow falha com mensagem clara; instrução para gerar novo token |
| PC desligado na segunda 08h | Tarefa roda quando o PC ligar; fila da semana anterior não é afetada |

## 7. Segredos

`IG_ACCESS_TOKEN`, `IG_USER_ID`, `PEXELS_API_KEY`, `TIKTOK_*` e `GH_SECRETS_PAT` (token fine-grained do GitHub com permissão de escrita em secrets deste repo, necessário porque o `GITHUB_TOKEN` padrão do Actions não pode atualizar secrets ao renovar o token da Meta) ficam em **GitHub Secrets** e, localmente, em `.env` fora do git (`.gitignore`). O usuário insere os valores; o Claude nunca lê, imprime ou commita segredos.

## 8. Fases de entrega

| Fase | Entrega | Gate |
|---|---|---|
| 0 | Contas: Instagram (Criador, aquecido 5–7 dias com uso manual), app Meta, Pexels, GitHub, app TikTok + pedido de auditoria | Usuário confirma contas criadas |
| 1 | Gerador local: 1 reel + 1 carrossel de amostra; banco inicial de citações | Usuário aprova o visual |
| 2 | Spike de hospedagem: 1 reel de teste publicado via API usando URL do `gh-pages` | Publicação bem-sucedida; senão, trocar hospedagem antes de seguir |
| 3 | Publisher + fila + workflows com `--dry-run` | Dry-run de uma semana completa sem erro |
| 4 | Tarefa agendada semanal do Claude; primeira semana com olhada do usuário no lote | 2 semanas seguidas sem intervenção |
| 5 | TikTok automático (pós-auditoria), rotina mensal do banco, página de afiliados | — |

## 9. Testes

- `pytest` para: geração de legendas a partir de word timings, `validate.py` (casos válidos e inválidos), montagem/atualização de `queue.json`, seleção de itens vencidos no publisher.
- Teste de fumaça de render: gera um reel de 10s e um carrossel e checa resolução/duração com `ffprobe`.
- Publisher com `--dry-run` (não chama APIs, registra o que faria).
- Clientes de API testados com respostas simuladas (sem chamadas reais em CI).

## 10. Fora de escopo (por enquanto)

Criação do produto digital próprio; YouTube Shorts; respostas automáticas a comentários/DMs; analytics automatizado.

## 11. Riscos

- **Hospedagem via GitHub Pages pode ser recusada pela API do Instagram** → validado na Fase 2.
- **Conta nova com postagem via API pode ser sinalizada como spam** → aquecimento manual na Fase 0.
- **Auditoria do TikTok pode demorar ou ser negada** → TikTok em modo manual até lá.
- **Nicho saturado / penalização de conteúdo repetitivo** → banco de citações, histórico anti-repetição e variedade de ganchos.
- **Limite de uso da assinatura do Claude** → geração em lote semanal único, não diária.
