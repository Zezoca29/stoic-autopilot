# Configuração das contas (Fase 0)

Você executa estes passos; o Claude não cria contas, não digita senhas e não lê tokens.
Comece pelo Instagram hoje: a conta precisa de 5–7 dias de uso manual antes da automação.
As telas da Meta e do TikTok mudam com frequência — se um nome de menu não bater, procure pelo termo equivalente.

## 1. Instagram
1. Crie uma conta nova (e-mail dedicado ao projeto) com o nome **Fortaleza Interior**. O @ escolhido foi `@fortalezainterior.br` (o `@fortalezainterior` estava ocupado).
2. Foto, nome e bio. Bio sugerida: "Fortaleza Interior: estoicismo para a vida real. Sêneca, Marco Aurélio, Epicteto. Narração com voz sintética. 📚 Livros ↓"
3. Configurações → Tipo de conta → **Mudar para conta profissional → Criador**. Categoria: "Educação" ou "Autor".
4. Aquecimento (5–7 dias): siga ~30 perfis do nicho, curta e comente de verdade, poste 2–3 vezes manualmente.

## 2. TikTok
1. Crie a conta **Fortaleza Interior** com o mesmo @ do Instagram, foto e bio iguais.
2. Até a Fase 5 os reels são enviados por você: eles ficam em `output/<id>/reel.mp4`. Dá para agendar até 10 dias à frente pelo TikTok Studio na web.

## 3. GitHub
1. Crie uma conta em github.com (se ainda não tiver).
2. O repositório público `stoic-autopilot` é criado na Task 21, com sua aprovação.

## 4. Pixabay (vídeos de fundo)
1. Crie conta em https://pixabay.com (gratuita). Logado, abra https://pixabay.com/api/docs/: a sua chave aparece na própria página. (A emissão de chaves do Pexels está pausada, por isso usamos o Pixabay.)
2. Guarde para colocar no `.env` (seção 7).

## 5. Token do Instagram
1. Em https://developers.facebook.com clique em **Create App** → caso de uso **Other** → tipo **Business** → nome e e-mail → **Create**. No painel, em **Instagram** clique em **Set up**; a **API setup with Instagram login** é adicionada sozinha (não precisa de Página do Facebook). A verificação de empresa só é exigida para colocar o app em modo Live, não para o uso em desenvolvimento.
2. Permissões necessárias: `instagram_business_basic` e `instagram_business_content_publish`.
3. Em "Generate access tokens", clique em **Add account** e entre com a conta do projeto. Se pedir, adicione a conta em Funções do app → Testadores do Instagram e aceite o convite no app do Instagram (Configurações → Apps e sites).
4. Copie o **token** (vale 60 dias; a renovação automática roda toda segunda) e o **ID da conta Instagram** mostrado ao lado.
5. Mantenha o app em modo Desenvolvimento: como a conta é sua e tem função no app, não precisa de App Review.
6. Se o workflow `publish` falhar com "token invalid or expired": repita os passos 3–4 e atualize o secret `IG_ACCESS_TOKEN` (seção 7).

## 6. Token do GitHub para renovar o segredo
1. github.com → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate.
2. Repository access: só `stoic-autopilot`. Permissions → Repository → **Secrets: Read and write**. Validade: 1 ano.

## 7. Onde colocar cada valor
- Arquivo local `.env` (copie de `env.example`): `PIXABAY_API_KEY`, `IG_USER_ID`, `IG_ACCESS_TOKEN`, `PAGES_BASE_URL`, `IG_HANDLE`.
- GitHub → repositório → Settings → Secrets and variables → Actions:
  - **Secrets:** `IG_USER_ID`, `IG_ACCESS_TOKEN`, `GH_SECRETS_PAT` (token da seção 6).
  - **Variables:** `PAGES_BASE_URL` = `https://zezoca29.github.io/stoic-autopilot`.

## 8. Músicas
Baixe 3–5 trilhas calmas (ex.: busque "ambient piano", "cinematic calm") em https://pixabay.com/music/ e salve como `.mp3` em `generator/music/`. Elas ficam só no seu PC.

## 9. App do TikTok (depois que o site estiver no ar — Task 21)
1. Em https://developers.tiktok.com crie um app e adicione **Content Posting API** (Direct Post).
2. Use as páginas `.../privacy.html` e `.../terms.html` do seu GitHub Pages.
3. Envie para auditoria. Aviso honesto: o TikTok exige uma interface onde o criador escolhe privacidade e confirma o post; automação sem interface costuma ser recusada. Se for recusada, o upload manual continua sendo o caminho.
