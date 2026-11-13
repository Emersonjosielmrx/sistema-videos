# Fábrica de credenciais: como gerar cada uma

Leia isto antes de criar credenciais em massa. Cada seção diz o passo a passo que funcionou, onde a credencial vai parar
e o que deu errado. Quando um método mudar, atualize a seção dele.

## Regras que valem para todas

- **Contas:** sempre as do cofre `D:\logins-google` (`cofre.py`). Nunca mover nem copiar perfis/cookies de lá: outros
  projetos usam. Abrir com `porta, proc = cofre.abrir(conta, url="about:blank", visivel=True)`, conectar com Playwright
  `connect_over_cdp(f"http://127.0.0.1:{porta}")` e fechar com `cofre.fechar(proc, br, nome=conta)`.
- **Conta com Google morto** (`google` != `vivo` em `D:\logins-google\cofre\contas.json`): pular. Para reviver:
  `python D:\logins-google\cofre.py logar <conta>`.
- **Verificação humana** (Turnstile, reCAPTCHA, "Falha na verificação"): PARAR a fila na hora. Insistir bloqueia a conta
  (a `fabricadeautomacoesia` foi bloqueada no Cloudflare assim). Captcha quem resolve é a pessoa, nunca o robô.
- **Não usar proxy no navegador para esconder que as contas são da mesma pessoa.** O dono pediu e foi recusado em 22/10.
- **Ritmo:** 20 s entre contas. Se começar a falhar verificação em sequência, retomar outro dia em lotes pequenos.
- **Validar a credencial pela API antes de exportar.** Nunca mostrar a chave inteira em log/tela (só os 4 últimos).
- **Backup** do arquivo de produção antes da primeira gravação do dia (`<arquivo>.bak_AAAAMMDD_antes_fabrica`).
- **Mapear serviço novo:** script temporário que abre a página, tira print de cada etapa e lista botões/inputs/iframes
  (`page.locator("button, a, [role=button]").all_inner_texts()`, `page.frames`). Depois escrever o módulo no padrão
  dos que existem (`criar`, `criar_massa`, `salvar`, `listar`; registro local + exportação) e apagar o temporário.

## Cloudflare Workers AI — `cloudflare_tokens.py` (automático)

- **Comandos:** `python cloudflare_tokens.py criar <conta>`, `criar_massa <c1> <c2>...`, `salvar <conta> <token> [account_id]`, `listar`.
- **Passos:** `dash.cloudflare.com/profile/api-tokens` → se cair em `/login`: clicar na linha do e-mail ("…@gmai… Last
  used") ou no link "Google" → no Google, consentimento "Continuar" (repetir até 40 s) → Create Token → Get started
  (Custom token) → nome → Permissions: **Account | Workers AI | Edit** (2º e 3º combobox) → Continue to summary →
  Create Token → copiar `cfut_...` → **account_id**: abrir `dash.cloudflare.com/` e tirar os 32 hex da URL.
- **Validação:** `GET /client/v4/user/tokens/verify`.
- **Destino:** `D:\hipercool-videos\secrets\cloudflare.json` → `{"contas": [{"api_token", "account_id", "conta"}]}`.
  Lido pelo `imagem_reserva.py` (cota de uma acabou = HTTP 429 → passa para a próxima).
- **Cota grátis:** 10 mil neurons/dia por conta (zera 00:00 UTC). flux-2-klein-4b ≈ 105 neurons por imagem 1344x768.
- **Registro local:** `cloudflare_tokens.json`.
- **Histórico:** 21/10 → 60 contas (57 da fábrica + 3 antigas `conta_antiga_1..3`, dono desconhecido). Falhou:
  `msenergypara` (login não terminou).

## Groq (Whisper) — `groq_chaves.py` (automático)

- **Comandos:** `python groq_chaves.py criar <conta>`, `criar_massa --vivas` (todas as vivas; pula as já feitas),
  `criar_massa <c1> <c2>...`, `salvar <conta> <chave>`, `listar`.
- **Passos:** `console.groq.com/keys` → "Reject All" no aviso de cookies → "Continue with Google" → seletor de contas
  (`accountchooser` na URL): clicar no texto do e-mail → consentimento: "Continuar" → volta em `/keys` → Create API Key
  → `input[name="keyName"]` → Submit → copiar `gsk_...` (56 caracteres) → Done.
- **Cota é por conta (organização), não por chave:** a tabela de `/keys` mostra `gsk_...XXXX`; se o final bate com uma
  chave `ok` do rodízio, a conta é pulada.
- **Validação:** `GET https://api.groq.com/openai/v1/models` **sempre pelo proxy Webshare**
  (`D:\postador-de-videos\secrets\proxies.txt`), com `requests` (urllib leva 403).
- **Destino:** `D:\postador-de-videos\secrets\groq_keys.json` → `[{"id", "token", "tipo": "groq", "status": "ok", "note", "conta"}]`.
  Lido pelo `groq_api.py` de todos os projetos (o `secrets` do hipercool é junção para o do postador).
- **Registro local:** `groq_chaves.json`.
- **Armadilhas:**
  - Na tela de consentimento o e-mail aparece de novo (botão de trocar conta). Clicar nele volta ao seletor e entra em
    loop: só clicar no e-mail quando a URL tiver `accountchooser`.
  - "Restricted access … violating our terms of service" = organização bloqueada pelo Groq. Bloqueadas em 22/10:
    `emersongenc`, `emersongencshin`, `emersonjosiel1995`.
  - O Submit só libera depois de um Turnstile invisível. Depois de ~15 contas seguidas ele virou "Falha na verificação"
    (`emersonjosiel2030`, `emersonjosiel2033`): o robô agora para a fila quando o Submit não libera em 30 s.
- **Histórico:** 22/10 → de 8 para 21 chaves boas. Parado no `emersonjosiel649`; faltam ~40 contas, retomar em lotes de 5–10.
  25/10 → lote de 8: ZERO chave. "Restricted access" (organização bloqueada) em `emersonjosiel649`, `murilodoctor192`,
  `solarmundo195`, `vendeafiliados3`, `emersonjosielmrx1995`; `seebotsia` com "Create API Key" desativado (mesmo
  sinal); `contapessoal` Chrome abriu e não respondeu ao CDP (3 min); `mundosolar1995` com o Chrome já aberto em outro
  processo (não fechar: pode ser de outro trabalho). O Groq passou a barrar quase toda organização nova destas contas:
  não insistir em lote; só tentar de novo se o dono pedir.
  25/10 noite → último lote (pedido do dono): 48/59 com chave no rodízio; resto = organização bloqueada. **Encerrado**
  ("não precisamos mais"), fora do lembrete diário.

## SightEngine (censura/nudez) — `sightengine_contas.py` (semiautomático)

> **25/10/2026 (dono): encerrado.** O dono rodou o último lote e disse "não precisamos mais". Tirado do lembrete
> diário (`lembrete_diario.py`, que agora não mostra nada). Só voltar a criar conta se o dono pedir.

- **Comandos:** `python sightengine_contas.py criar <conta>`, `criar_massa --vivas`, `criar_massa <c1> <c2>...`, `listar`.
- **Não tem login com Google.** Passos:
  1. Robô: `dashboard.sightengine.com/signup` → "Work email" = Gmail da conta (aceita Gmail) + senha gerada
     (8+, maiúscula, minúscula, número; guardada no registro ANTES de enviar) + checkbox `tos`.
  2. **Pessoa:** clica em "Não sou um robô" (reCAPTCHA). Resolvido o captcha (`textarea[name="g-recaptcha-response"]`
     preenchido), o robô clica em CREATE ACCOUNT. Espera até 8 min; olha todas as abas da conta (o painel pode abrir
     em outra aba). 2 contas seguidas sem clique = fila para.
  3. Robô: página `/confirm-email?signup=1` → abre o Gmail da própria conta no Chrome do cofre
     (`mail.google.com/mail/u/0/#search/from%3Asightengine`, linha `tr.zA`) → link
     `dashboard.sightengine.com/confirm-email-validation?token=...` → cai em `/welcome` (questionário: dá para pular).
  4. Robô: `dashboard.sightengine.com/api-credentials` → `api_user` = número depois de "API user";
     `api_secret` = atributo `data-secret` de `span.ak-secret` (na tela aparece mascarado com os 4 últimos).
- **Validação:** `POST api.sightengine.com/1.0/check.json` com uma PNG cinza 64x64, `models=nudity-2.0`
  (gasta 1 das 2.000 operações do mês).
- **Destino:** `D:\postador-de-videos\secrets\sightengine.json` →
  `{"keys": [{"name", "api_user", "api_secret", "status": "available", "used_today", "used_at"}]}`.
  Lido pelo `censura_visual.py` (lê os `sightengine.json` de todos os projetos; a que esgota no dia é pulada).
- **Registro local:** `sightengine_contas.json` (e-mail, senha, api_user, api_secret).
- **Cota grátis:** 2.000 operações/mês, 500/dia por conta.
- **Limite por rede:** depois de 2 cadastros seguidos no mesmo IP o site respondeu "Too many accounts have been created
  from your network. If you need a new account, please contact us." O robô reconhece e para a fila. Não contornar
  com proxy; esperar dias e tentar 1 conta, ou falar com o suporte deles.
- **Histórico:** 22/10 → `aulacomia` (api_user 1851350901; cadastro feito à mão, senha guardada pode não ser a usada)
  e `aulasrevolution` (67202044). Na 3ª (`canalalucinaai`) veio o limite da rede. Total: 5 contas (3 antigas + 2).
  25/10 → `comoseriasecomia` (323568761) e `e4487017`; na 3ª (`emersongenc`) veio o limite da rede de novo (de novo
  2 por dia). Total: 7. Na `comoseriasecomia` o Gmail passou de 60 s pra abrir e o cadastro ficou sem confirmar:
  `criar <conta>` de novo retoma sem captcha (lê a sessão logada, confirma o e-mail e pega a chave).

## Gemini (AI Studio) — `gemini_chaves.py` (automático)

- **Comandos:** `python gemini_chaves.py criar <conta>`, `criar_massa --elegiveis` (contas com Google vivo + YouTube ou
  TikTok no cofre), `criar_massa <c1> <c2>...`, `salvar <conta> <chave>`, `listar`, `listar_elegiveis`.
  O antigo `D:\projetos-navegador\key-factory\key_factory.py` ficou intocado (botões velhos, não funciona mais).
- **Passos (UI de 22/10, em português):** `aistudio.google.com/apikey` → conta nova cai em `/onboarding`: marcar só o
  checkbox obrigatório dos 18 anos (clicar no `mat-checkbox`/texto; `check(force=True)` não marca) → "Continuar" →
  "Criar chave de API" → dialog "Criar uma nova chave" (em conta nova fica girando até ~1 min) → combobox "Escolha um
  projeto importado" → **escolher projeto que ainda não tem chave**, senão "Criar projeto" (nome + botão "Criar
  projeto"; volta ao dialog com o projeto escolhido) → "Criar chave" → dialog "Detalhes da chave de API" mostra a chave
  inteira em texto (ler com regex no dialog; o botão copiar exige permissão de área de transferência e trava).
- **Cota é por PROJETO, não por chave:** chave nova num projeto que já tem chave não soma nada (o dialog vem com o
  projeto antigo escolhido por padrão). O registro marca `projeto_exclusivo`; chave da fábrica que divide projeto é
  refeita em projeto próprio e a antiga sai do destino.
- **Formato novo:** chaves criadas desde out/2026 começam com `AQ.` (as antigas `AIza`); a API aceita as duas por `?key=`.
- **Validação:** `GET generativelanguage.googleapis.com/v1beta/models?key=`. 429 = chave boa com projeto no limite.
- **Grátis (teste 22/10):** texto Gemini 3/3.5/3.6/3.8 Flash e 3.1 Flash-Lite; TTS 2.5 Flash, 3.1 Flash e 3.8 Flash(-Lite).
  Cota zero (429): 3.1 Pro, `gemini-pro-latest`, todos os de imagem (Nano Banana, 3 Pro Image, 3.1 Flash Image),
  2.5 Pro TTS. `gemini-2.5-pro` não existe mais para conta nova.
- **Destino:** `D:\hipercool-videos\secrets\gemini_keys.json` → `[{"id", "token", "status": "ok", "fila", "note"}]`
  (lido pelo `gemini_tts.py`/`gemini_llm.py`, sempre pelo proxy). Chave fica no PC local; o OmniRoute é para login OAuth.
- **Armadilhas:** conta que redireciona para `/docs/available-regions` não tem acesso ao AI Studio (não insistir).
- **Registro local:** `gemini_chaves.json` (guarda também `bloqueio`: `bloqueio_idade`, `google_recusou_projeto`,
  `sessao_expirada`; a fila pula quem tem bloqueio — `criar <conta>` força). Cada chave no destino tem `"conta"`.
- **Situação por conta:** `GEMINI_CONTAS.md`; **exportar e-mail+chave:** `gemini_chaves_export.csv`. Os dois saem de
  `python gemini_chaves.py relatorio` (rodar de novo depois de cada fila).
- **Histórico:** 22–23/10 → 59 contas vivas tentadas: 37 com chave em projeto próprio, 9 bloqueio de idade, 12 Google
  recusou projeto novo (8 delas já tinham chave antiga), 1 login vencido; arquivo de credenciais 52 → 94 chaves.

## Cloud Run (deploy de containers) — `cloud_run.py` (automático)

- **Comandos:** `python cloud_run.py criar <conta>`, `criar_massa --sem-canal` (todas sem canal com Google vivo),
  `criar_massa <c1> <c2>...`, `listar`.
- **Passos:** `console.cloud.google.com` → aceitar termos / ativar free trial → para cada API
  (Cloud Run, Container Registry, Cloud Build, Cloud Functions): navegar à biblioteca e clicar Enable.
- **Cota grátis (Cloud Run):** 2M requests/mês, 360k GB-s memória, 180k vCPU-s. Container Registry: 0,5 GB.
- **Filtro:** SÓ contas SEM canal YouTube (`usos.youtube` vazio no cofre).
- **Registro local:** `cloud_run_contas.json`.
- **Histórico:** 24/10 → módulo criado. Nunca rodado em massa.

## Cloud APIs (APIs grátis do Google) — `cloud_apis.py` (automático)

- **Comandos:** `python cloud_apis.py criar <conta>`, `criar_massa --sem-canal`, `criar_massa <c1> <c2>...`, `listar`.
- **APIs ativadas:** Cloud Text-to-Speech (4M chars/mês), Cloud Translation (500k chars/mês),
  Cloud Vision (1k req/mês), Cloud Natural Language (5k un./mês), YouTube Data API v3 (10k un./dia),
  Google Drive API, Gmail API, Google Sheets API, Google Chat API.
- **Passos:** para cada API: navegar à biblioteca → Enable. Se precisar criar projeto, cria automaticamente.
- **Filtro:** SÓ contas SEM canal YouTube.
- **Registro local:** `cloud_apis_contas.json`.
- **Histórico:** 24/10 → módulo criado. Nunca rodado em massa.

## Chat Hub Agentes (Google Chat) — `chat_hub_agentes.py` (automático)

- **Comandos:** `python chat_hub_agentes.py criar <conta>`, `criar_massa --sem-canal`,
  `criar_massa <c1> <c2>...`, `listar`.
- **Passos:** ativar Chat API → abrir chat.google.com → criar Space "agentes-hub" → configurar webhook.
- **Objetivo:** cada conta = 1 espaço no Google Chat, os agentes conversam entre si via webhook.
- **Filtro:** SÓ contas SEM canal YouTube.
- **Registro local:** `chat_hub_contas.json`.
- **Histórico:** 24/10 → módulo criado. Nunca rodado em massa.

## rclone no Drive de uma conta — `rclone_drive_conta.py` (automático)

- **Comando:** `python rclone_drive_conta.py <conta> <remoto>` (ex.: `emersonjosiel649 colab649`).
- **Passos:** `rclone authorize drive --auth-no-open-browser` → URL do 53682 aberta no Chrome do cofre → clica o e-mail
  no seletor → "Continuar" no consentimento → token → `rclone config create <remoto> drive scope drive token ...`.
- **Config:** rclone.conf padrão (o mesmo do `manhwa-drive:`). Exe: `D:\tools\rclone.exe`.
- **Histórico:** 24/10 → `colab649:` (Drive da emersonjosiel649, 3 GB livres; Gmail/Fotos ocupam o resto), para a
  fila do recap longo na Colab (`D:\recapd-ambientes\producao\COLAB_RECAP_LONGO.md`).

## Mineração no Colab — descartada (24/10)

Os termos do Colab proíbem mineração de criptomoeda: a conta Google inteira é banida (perde TikTok, Gemini, Groq...).
O pool configurado no antigo `mining-colab\setup_mining.py` (minexmr) fechou em 2022. Não fazer.

## Conta do Instagram — `D:\postador-de-videos\bin\instagram_criar.py` (automático; 24/10)

- **Criar:** `$env:IG_SENHA='<SEGREDO_REMOVIDO>'; python bin\instagram_criar.py --email <google do cofre> --nome "<nome>"
  --arrobas <@1> <@2> ... --cofre ig_<nome>`. Feito 24/10: @msenergysolar.pa (msenergypara@gmail.com, cofre
  `ig_msenergy_novo`).
- **Fluxo (24/10):** página única em `/accounts/emailsignup/` (e-mail, senha, data em listas personalizadas, nome,
  @) → "Enviar" → código de 6 dígitos no e-mail (mostra o e-mail INTEIRO) → lido no Gmail do cofre e digitado.
- **Armadilha:** o código tem que ser digitado na MESMA janela; fechou antes = conta não existe (login dá "senha
  incorreta"). Conta nova pra substituir conta suspensa = evasão: não fazer.
- **Logar contas que já existem:** `bin\instagram_local.py` (senha por IG_SENHA; código por e-mail lido no Gmail do
  cofre pelo e-mail mascarado; selfie com a foto de rosto da dona; WhatsApp fica pro fim com `--whatsapp`).
- **Instagram NÃO tem "Continuar com Google".** Sem senha: "Esqueceu a senha → link de login" (pede reCAPTCHA).

## Canal do YouTube — `youtube_channel.py`

- Escrito em 21/10, **nunca testado**. `python youtube_channel.py verificar [conta]`, `criar <conta> --nome "..."`.
- Testar numa conta antes de usar em massa e completar esta seção com o fluxo real.

## Kaggle (GPU do recap longo) — `kaggle_contas.json` (chaves) + `recapd colab\kaggle_pool.json` (rodízio)

> **03/11 — REGRA QUE NÃO SE QUEBRA: nunca 2 contas pelo mesmo IP, nem em teste.** Em 02/11 uma medição de cota
> consultou as 25 contas da hermes-prod pelo mesmo IP, de hora em hora, e as 14 verificadas foram BANIDAS juntas.
> Ler antes: D:\hipercool-materiais\comum\kaggle_gerente\INCIDENTE_BANIMENTO_02NOV.md (checklist). Trava no código:
> vps_central._guarda_ip (2ª conta no mesmo IP = recusada por 60 min). Nada de laço sobre a lista de contas.


- Chave de API de cada conta em `kaggle_contas.json` (`username`, `key`). Só conta com **telefone verificado** no
  Kaggle tem internet+GPU no kernel; a central marca "kernel sem internet" quando falta.
- **Cada conta fica ATRELADA a UMA saída (máquina/IP) para sempre — NUNCA misturar** (dona 29/10: "se uma conta está
  saindo da VPS, a outra sai de outra; aquela conta fica atrelada àquela VPS ou ao PC"). Campo `saida` no
  `kaggle_pool.json`; cada saída roda a sua central (`vps_central.py`, config.json `saida`) só com as contas dela:
  | saída | IP | onde | contas (29/10) |
  |---|---|---|---|
  | hermes-prod | 62.171.128.241 | `/opt/recap_central` (principal: fila, página, avisos) | as 25 antigas (incl. 2031, 2032, 2029, 2026) |
  | hermes-staging | 209.145.60.53 | `/opt/recap_central` (so_gpus) | emerson2030 |
  | hermes-bloqueio | 157.173.207.22 | `/opt/recap_central` (so_gpus) | emersonjosiel2023777 (emersonjosiel2027@) |
  | casa-pc1 | 191.36.137.42 | `D:\recap_central_casa` (tarefa RecapCentralCasa) | revolutionemerson (revolutionemerson1@) |
  PC1, PC2, desktop e notebooks saem TODOS pelo IP da casa = uma saída só. Conta nova = saída que ainda não tem conta
  (ou perguntar à dona); a 1ª máquina que falar com o Kaggle pela conta é a saída dela.
- **02/11 noite — 14 contas VERIFICADAS, 1 IP por conta (valendo).** 16 contas da hermes-prod caíram juntas em 02/11
  (4 sessões no mesmo IP; nenhuma era verificada). Regras novas no `vps_central.py`: só lança conta com
  `"verificada": true` no pool (a dona informa; não informou = não verificada); NUNCA 2 sessões no mesmo IP
  (`_ip_da_conta`: Webshare fixo ou a saída); "sem internet" não é re-testada sozinha (`vps_central.py liberar <user>`).
  Webshare grátis = só 10 IPs no total (o `-N` é o mesmo IP nas 96 contas; testado 02/11); o 7 é bloqueado no Kaggle.
  | conta | central (`saida`) | IP |
  |---|---|---|
  | e4487017 | hermes-prod | Webshare 1 |
  | emersongenc | hermes-prod | Webshare 2 |
  | emerson2029 | hermes-prod | Webshare 3 |
  | emersonjosiel | hermes-prod | Webshare 4 |
  | emerson2031 | hermes-prod | Webshare 5 |
  | emerson2032 | hermes-prod | Webshare 9 |
  | revolutionemerson2 | casa-pc1 | Webshare 6 |
  | emersonjosiel2027 | casa-pc1 | Webshare 8 |
  | revolutionemerson3 | casa-pc1 | Webshare 10 |
  | aulacomia + emerson2026 | hermes-prod | IP da hermes-prod (revezam: a trava não deixa as 2 juntas) |
  | emerson2030 | hermes-staging | IP da staging |
  | emersonjosiel2023777 | hermes-bloqueio | IP da bloqueio |
  | revolutionemerson | casa-pc1 | IP da casa |
  Faltam IPs pra as 5 últimas irem pro Webshare (plano pago). Dona 02/11 22h: fica assim; conta NOVA verificada entra
  como a 2ª de um IP que só tem 1 (2 contas por IP, revezando — 1 IP = 168 h/semana, 2 contas = 60 h, cabe; a trava
  `_ip_da_conta` nunca deixa as 2 rodarem juntas). Mais de 10 IPs só com Webshare pago (as 96 contas grátis = os mesmos
  10 IPs, testado em 30 contas). As 17 não verificadas (maitanajssicajesus, jogoscomia,
  jornalia, msenergypar, mundosolar, vendeafiliados, fabioyoutube, fbricadeautomaes, fabricadeautomacoesi, filmescomia,
  gameoftroneskingsroa, inovaremanhwabr, inovaremanhwaverse, inovaremanga, inovaremanhwaversehi, entrevistacomia,
  emersonjosiel1995) ficam fora até a dona dizer. `gpus_por_saida`: hermes-prod 7, casa 4, staging 1, bloqueio 1.
  Banda Webshare: o vídeo NÃO passa por ela (Kaggle ↔ Drive direto; edge-tts no Kaggle saiu 100% direto nos 4 últimos
  longos); pelo IP fixo só vão comandos da API (push, status, cota) = KB por sessão.
- **08/11 — 9 contas novas (dona), cada uma no SEU IP pago rnprmtfo** (token por `kaggle_token_proxy.py <email> <N>`,
  Chrome conferido no IP antes do Kaggle; papel curto; telefone "Verified" no print `_kaggle/token_*/settings.png`):
  french=emersoncunhacunha rnprmtfo-40 · ita=inovaremanhwaverseit 41 · russian=emersonjosielcunha 42 ·
  ind=inovaremanhwaversein 43 · verse2=inovaremanhwaverse2 44 (verificada=false: sem print da Settings, conferir) ·
  thai=inovaremanhwaverseth 45 · mundosolar1995 46 · verse5=inovare 47 · verse6=inovareee 48. Faixa 40-49 reservada ao
  Kaggle (WhatsApp usa 15/17/85/91). inovarecliente1 NÃO está no cofre: dona loga e roda com o rnprmtfo-49.
  Atenção: o username do Kaggle nem sempre é o e-mail — conferir na tela Settings (script pegava do e-mail).
- O `kaggle_pool.json` existe nas 4 centrais: mudou um, copiar pros 4 (o mestre é o do `recapd colab`).
- Cota de GPU: ~30 h/semana por conta, renova sábado 00:00 UTC (sexta 21h BR); cada central tem o "liberar" semanal.

## Avaliados e descartados (21/10)

DeepInfra, Together, Fireworks, Novita, SiliconFlow: só crédito de cadastro, sem cota grátis contínua e sem login Google.
Cohere: modelo de texto abaixo do Sonnet 4.5. Pollinations: uma chave basta. Nenhum serviço com cota grátis tem modelo
de texto acima do Sonnet 4.5.
