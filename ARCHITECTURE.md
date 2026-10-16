# Arquitetura — stoic-autopilot

Execução híbrida: o PC gera a mídia uma vez por semana; o GitHub Actions publica de hora em hora, com o PC desligado.

## Fluxo

```
Segunda 08h (tarefa agendada do Claude, local)
  generator.schedule ──▶ slots (7 reels 12h, 3 carrosséis 19h)
  Claude escreve content/weeks/<lote>.json (citações só do banco)
  generator.build_week
     ├─ check_plan (contagem, cooldown 60d, ganchos, horários)
     ├─ reel: tts (edge-tts + tempo por palavra) → captions (.ass) → footage (Pixabay/fallback) → ffmpeg
     ├─ carrossel: Jinja2 + Playwright → JPEG 1080x1350
     ├─ check_media (1080x1920, 30–60 s, < 100 MB)
     └─ grava queue.json + content/history.json só se tudo passou
  generator.deploy_media ──▶ força push do gh-pages (site/ + mídia pendente)
  git push main

De hora em hora (GitHub Actions: publish.yml)
  publisher.run ──▶ itens vencidos ──▶ Instagram API (container → status → media_publish)
                 └─ salva queue.json após cada post; 3 tentativas; token inválido aborta sem gastar tentativas
  commit de queue.json (com retry de push)

Toda segunda (refresh-token.yml) ──▶ renova o token de 60 dias e atualiza o secret
```

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `shared/config.py` | Settings do ambiente, constantes, caminhos |
| `shared/post_queue.py` | fila de publicação e estados por plataforma |
| `generator/batch.py` | estrutura do lote |
| `generator/quotes.py`, `history.py` | banco de citações e anti-repetição |
| `generator/validate.py` | regras antes e depois de renderizar |
| `generator/build_week.py` | orquestração e CLI (`--preview`, `--enqueue`) |
| `publisher/instagram.py` | cliente da API; tira o token das mensagens de erro |
| `publisher/run.py` | publica itens vencidos |
