# Opus / Fable grátis — teste real com uma conta (30/10/2026)

Pedido da dona: pegar uma conta e testar cada site da lista (minha pesquisa + a do Argon), marcar se tem mesmo
Opus/Fable grátis; se precisar cadastro, usar essa conta. Conta de teste: **sua_conta@gmail.com** (cofre, porta 9701,
Chrome escondido). Controle: `python D:\opus-gratis\nav.py ...`; prints em `prints\`.
Retomável: cada site marcado aqui assim que testado.

> **30/10 — o Genspark (linha 8) virou projeto.** Como ele foi o único que funciona de verdade (Opus 5.5,
> 100 créditos/dia por conta Google), montei o POOL no molde do gemini-argo/sonnet web: fila de contas,
> cota, login "1 por 1" (OAuth Google) e driver do navegador. Veja **LEIA-ME.md** e **PROGRESSO.md**.
> Uso: `python genspark.py "pergunta"` · servidor OpenAI: `python genspark_http.py`.
>
> **30/10 tarde — o 1min.ai (linha 11) passou a rodar pela API, sem navegador** (`umin\umin.py`, veja `umin\LEIA-ME.md`).
> Pela API o Opus 5.5 custa **3.973 créditos** por mensagem curta; pela tela custava ~21.600, porque a tela manda
> para vários modelos juntos. Também respondem Opus 5 e Fable 5.1, mais caros. As linhas 1, 6, 10, 15–18 e 21–28
> foram revistas nesta tarde.

| # | Site | Modelo prometido | Resultado do teste | Detalhe |
|---|---|---|---|---|
| 1 | EaseMate (easemate.ai) | Fable 5.1 (200k tokens/dia) | **FRACO: só com cadastro, 30 créditos** | No Chrome do cofre o app não monta (prints easemate_3..7). Revisto 30/10 à tarde num navegador normal: o app monta, mas ao enviar abre "Sign in to EaseMate AI Assistant — New here? Get **30 free credits** instantly. Check in daily…". Os "200 mil tokens/dia" são só texto da página; a página de preços põe o Claude avançado só no pago, e o seletor mostra "Claude Fable 5". Cadastro não testado (fica para a dona, ~2 min num Chrome normal) |
| 2 | Felo (felo.ai) | Opus 5.5 (200 créditos/dia) | **NÃO (Opus só no Pro)** | Login Google ok, 500 créditos/dia grátis (campanha). Na lista de modelos o "Claude 5.5 Opus" fica cinza com selo Pro, sem chave para ligar. Grátis: Claude 5.5 Sonnet, GPT-6.1 Terra, GPT-6 Luna, DeepSeek V4 Flash. Print felo_7 |
| 3 | TicNote (ticnote.com) | Opus 4.7 (30/mês) | **NÃO (propaganda)** | Cadastro com Google ok (300 min/mês grátis). A página "Claude Opus 4.7 Free" leva ao app, mas a lista de modelos não tem Opus nenhum; Claude Sonnet 5/4.6/4.5 todos com "Upgrade". Grátis só GPT-5.6 Luna, DeepSeek, Qwen, GLM, MiniMax. Print ticnote_2 |
| 4 | Kie AI (kie.ai) | Fable 5.1 (créditos de cadastro) | **TRAVADO** | É API paga por uso (Opus 5.5 US$ 1,60/8,00 por milhão; "créditos nunca expiram"). Cadastro só por Google/Microsoft; o botão do Google (quadro GSI) abre e fecha a janela, mas o site continua deslogado no Chrome do cofre. Valor do crédito de cadastro não confirmado. Refazer num Chrome normal |
| 5 | NoteGPT (notegpt.io) | Fable 5 | **FRACO (não vale)** | A tela de login diz "Sign In to get **15 free quotas per month**". Login Google não completou e não consegui abrir o seletor de modelo (propaganda de tela cheia por cima). Mesmo que tenha Fable, 15/mês é quase nada. Não chegou a mandar mensagem |
| 6 | Arena (arena.ai) | Opus 5.5 / Fable 5.1 (Direct) | **NÃO no Direct** | lmarena.ai virou arena.ai. Sem login, modo Direct: busca "opus", "fable" e "anthropic" = nada; os únicos Claude são claude-sonnet-5-high e claude-haiku-4-5. O Opus só pode cair por sorte no Battle (cego, não dá para escolher). Logado não testei. Print arena_3. **Revisto 30/10 à tarde:** os modos são Battle, Agent, Side by Side e Direct. No Side by Side sem login são 116 modelos, e de Claude só os mesmos dois. O ranking lista `claude-opus-5.5-high-vertex` e `claude-fable-5.1-max-text` jogando nas batalhas, ou seja, o Arena esconde o Opus/Fable do seletor (só aparecem nas batalhas) |
| 7 | Poe (poe.com) | Opus 5.5 (pontos diários) | **NÃO (pontos não bastam)** | Login Google ok. Conta grátis = **300 pontos/dia**; uma pergunta curta ao Claude-Opus-5.5 custa **5.804 pontos** → "precisa de mais pontos, assine". Não dá nem 1 mensagem. Tem Opus 5.5/5 e Fable 5.1/5 na lista, só no pago (a partir de R$ 20,82/mês). Print poe_3 |
| 8 | Genspark (genspark.ai) | Opus 5 (100 créditos/dia) | **SIM, FUNCIONA (o melhor até agora)** | Login Google ok → "Grátis · 100 créditos hoje" (renova por dia). Chat com IA já vem com **Claude Opus 5.5** selecionado. Respondeu "Sou o Claude Opus 5.5, da Anthropic" e 17×23=391. Custo: **3 créditos** por mensagem curta (100→97) → ~30 mensagens curtas/dia por conta. Mensagem longa deve custar mais (a medir). Endereço: genspark.ai/agents?type=ai_chat. Prints genspark_2..3 |
| 9 | Puter (puter.com) | Opus 5.5 / Fable 5.1 (user-pays) | **PARADO: pede SMS** | Puter.js (`puter.ai.listModels()`) lista claude-opus-5-5, claude-opus-5, 4-8, 4-7, 4-6, claude-fable-5-1 e fable-5. Sem conta o chat dá "Unauthorized". Cadastro com Google pede **"Verify your phone number"** (SMS +55). Cadastro parado na verificação por SMS (+55). Se a dona liberar um número, dá para continuar |
| 10 | Prophet (extensão Chrome) | Opus 5.5 (US$ 0,07) | **SIM, mas simbólico** (página oficial, não testado ao vivo) | prophetchrome.com/pricing: grátis = US$ 0,07 uma vez, sem cartão, com Opus 5.5 incluído. Cobra no mínimo 1 centavo por turno e o Opus 5.5 custa US$ 4/20 por milhão de tokens mais a margem → 1 a 3 mensagens curtas. Serve de prova, não de uso |
| 11 | 1min.ai (Multi AI Chat) | Opus 5.5 (página "free-ai-chat-with-claude-opus-5-5"; mandado pela dona) | **SIM, FUNCIONA (com limite)** | Login Google = 265.000 créditos. "Claude 5.5 Opus - AWS Bedrock US" respondeu em 5 s, se identificou como `us.anthropic.claude-opus-5-5` e acertou 17×23=391. Custo: ~21.600 créditos por mensagem curta → ~12 mensagens com o bônus. Créditos não expiram; ganha mais com "Daily Visit", avaliação e indicação (valor diário a conferir amanhã). Lista também tem Opus 5/4.8/4.7/4.6/4.5 e Fable 5.1/5. Atenção: o chat manda para vários modelos juntos, tirar o Qwen padrão. Prints 1min_11..14. **30/10 à tarde, pela API** (chave criada em app.1min.ai > API, `umin\umin.py`): Opus 5.5 = **3.973 créditos** (8 s), Opus 5 = 14.124, Fable 5.1 = 60.357, Haiku 5.5 = 87. Das 13h40 às 14h20 o Opus 5.5 deu 503 da AWS; falha não é cobrada, então o `umin.py` tenta de novo e aceita `--reserva`. Saldo às 14h25: 145.429. Créditos grátis: visita diária = **15.000/dia** (≈ 3–4 Opus 5.5; resgatada pela tarefa "1min visita diaria" às 06:10) e pesquisa "AI Agent" = **1.000.000 uma vez** (a dona responde). **Sem cadastro não dá:** a página diz "No registration is needed", mas, testado sem login, o envio abre o quadro "Log In" |
| 12 | AIFreeForever | Opus 5.5 (sem login, limite por IP; mandado pela dona) | **NÃO (isca)** | Passa a Cloudflare clicando na caixinha. A página /chat/claude-opus-5-5 existe ("No Login"), mas ao enviar mostra "Model not available. Choose an available model": só GPT 5.4, DeepSeek V4, Gemini 3.5 Flash, Grok 4, Claude Haiku 4.5, GLM 5.2. Print aiff_4 |
| 13 | Aymo AI | Opus 4.8 (compara lado a lado; mandado pela dona) | **NÃO** | Página de preços: plano Free = "Limited light models" (GPT OSS 120B, GPT-5 Nano, Gemma 4 31B...), 500 mensagens e 50 créditos/mês. Claude/Opus só a partir do Plus (US$ 4–8/mês) |
| 14 | RadoxAI (radoxai.com) | Opus 5.5 pela API, 500 mil tokens/mês grátis (mandado pela dona) | **NÃO (pede cartão)** | Login Google ok, "Free Plan 0.5M tokens/month", chave criada (`D:\opus-gratis\segredos\radoxai.key`, base `https://radoxai.com/v1`). Mas claude-opus-5.5, claude-fable-5.1, claude-opus-4.6 e até claude-sonnet-5 respondem `insufficient_quota: Billing verification failed. Please check your payment method.` Os modelos são revendidos ("owned_by: cleanapis") |
| 15 | v0.app da Vercel (o "V0 Max"; **vzero.app é outro site**, sem IA) | Opus e Sonnet, créditos iniciais no cadastro (mandado pela dona) | **INCERTO** (página oficial) | Grátis = US$ 5 uma vez + no máximo 7 mensagens/dia, sem cartão. O v0 Max roda Opus 4.8 (US$ 5/25 por milhão), mas "todos os modelos" só aparece nos planos pagos. Pede conta Vercel nova (teste para a dona) |
| 16 | ISH Chat | Opus 4.6, créditos diários com login GitHub (mandado pela dona) | **provável NÃO** (página oficial) | Saldo diário sem valor publicado; a API responde "pausada para manutenção" e no Reddit dizem que o Claude sumiu desde 17/04 |
| 17 | "Kira" = **Kiro** (kiro.dev, da AWS) | Opus 4.7, 1.000–5.000 créditos ao ligar o GitHub (mandado pela dona) | **NÃO (só com cartão)** (página oficial) | Grátis = 50 créditos/mês, só Sonnet 4.5 e modelos abertos. Os 1.000–5.000 créditos e o Opus são dos planos pagos |
| 18 | Gab AI | variações do Opus no painel de testes (mandado pela dona) | **NÃO** (catálogo oficial) | Em gab.ai/v1/models todo Claude (Opus 4.6 a 5.5, Fable 5/5.1) vem marcado `is_plus_only=true` (US$ 20/mês); os 250 créditos de cadastro só valem para o modelo deles (Arya) |
| 19 | Ninjachat.ai | Opus 5 (mandado pela dona) | **NÃO (só pago)** | Tem Claude Opus 5 na lista, mas a página de preços é "Every model. One plan. From $11/mo"; não mostra plano grátis |

**Padrão visto 30/10:** captchas (reCAPTCHA do Merlin, Turnstile do Kilo) falham no Chrome do cofre controlado por
CDP; a Cloudflare comum (AIFreeForever) passa clicando na caixinha. Sites travados por isso: refazer num Chrome
normal sem automação (EaseMate, Merlin, Kilo).

## Pesquisa ampliada 30/10 (Argon + Gemini 3.1 Pro)

Busca em várias línguas, Reddit/X/GitHub/fóruns, agregadores, IDEs e APIs. O que eles dizem é só candidato até eu
testar (o Gemini Pro marcou TicNote/EaseMate como "oficial" e o teste real mostrou que não é). O Argon conferiu a
API do OpenRouter: nenhum Opus/Fable tem versão `:free` lá.

### Candidatos novos para testar (dizem que dá Opus/Fable sem cartão)
| # | Serviço | O que dizem | Quem achou |
|---|---|---|---|
| 20 | Kilo Code (kilocode.ai) | US$ 5–20 de crédito no cadastro (Google/GitHub); Opus 5.5 e Fable 5.1 | Argon — **TRAVADO**: app.kilo.ai pede "Security Verification" antes do login Google e falha ("verification failed") no Chrome do cofre. A página fala em Opus 4.8. Refazer num Chrome normal |
| 21 | Amp (ampcode.com) | US$ 10 de crédito no cadastro; Opus 5.5 | Argon — **NÃO** (página oficial): o Amp Free foi pausado sem previsão de volta; o Hobby só roda com chave/assinatura própria |
| 22 | Zed (zed.dev) | US$ 10 / 14 dias de teste com GitHub; Opus 4.6/5 | Argon — **NÃO** (página oficial): o teste de 14 dias dá US$ 5 só de GPT-6 Luna; Opus/Fable só no pago |
| 23 | Requesty (requesty.ai) | US$ 1 de crédito no cadastro; chave API compatível OpenAI com Opus 5.5 e Fable 5.1 | Argon — **NÃO**: conta criada com Google, saldo **US$ 0,00** logo depois do cadastro (só "Top Up"). Print requesty_3 |
| 24 | Merlin (getmerlin.in) | 102 créditos/dia; Opus custa 15–30 → 3 a 6 por dia | Argon e Gemini — **TRAVADO**: sem login o modelo é escolhido sozinho ("Magic"); cadastro com Google não sai porque o reCAPTCHA não carrega no Chrome do cofre. Tentar num Chrome normal |
| 25 | WebDev Arena (web.lmarena.ai) | sem login, cota por IP; Opus 5.5 e Fable 5.1 para código | Argon — **só sorteado**: virou o Code Arena do arena.ai. O ranking WebDev de 27/10 tem Opus 5.5 e Fable 5.1 (Max) nas batalhas, mas, como no #6, não dá para escolher |
| 26 | Flowith (flowith.io) | créditos de boas-vindas; Opus 4.6/5 | Argon — **INCERTO** (página oficial): grátis = 300 créditos uma vez, "modelos limitados"; Opus 5.5 e Fable 5.1 existem, mas os premium começam no Pro. Pede conta nova |
| 27 | Routeway (routeway.ai) | saldo de teste no cadastro; Opus 4.6/5 | Argon — **NÃO** (página oficial): grátis só nos modelos `:free` (nenhum Claude; os "claude-…-distilled" são Qwen/Gemma). Opus 5.5 só pré-pago com cartão |
| 28 | Qoder (qoder.ai) | créditos de teste; Opus 4.6 | Argon — **NÃO** (página oficial): a lista oficial de modelos não tem Claude |
| 29 | Estações NewAPI do fórum linux.do | cota diária com login do fórum, precisa nível 2–3 de confiança | Argon |
| 30 | Shapes.inc | bots com Opus se o criador pagar | Argon (só Reddit) |
| 31 | Bolt.new / Lovable | limite diário/mensal grátis; dizem que roda Opus | Gemini Pro |
| 32 | Windsurf / Augment / Warp / Trae | testes de 14 dias ou cota mensal; Opus em geral só no pago | Argon e Gemini |

### Já descartados pela pesquisa (Opus/Fable só no pago ou com cartão)
Cursor Hobby, GitHub Copilot Free (só Sonnet), Perplexity, You.com (3–5 usos/dia de modos Pro, sem Opus livre),
Monica, Sider, HIX, ChatHub e TypingMind (só com chave própria), Abacus, Together (não tem Claude), AI/ML API (pede
cartão/telefone para premium), OpenRouter (só pago), claude.ai grátis (só Sonnet/Haiku), console da Anthropic
(depósito com cartão), AWS/Vertex/Azure (créditos de teste exigem cartão).

### Já em uso pela casa (lembrete do Argon)
- Conta Cline (`D:\cline-ponte`): Opus 5.5 / Fable 5.1 com créditos de cadastro.
- Antigravity: `claude-opus-4-6-thinking` com cota renovável por conta Google.
