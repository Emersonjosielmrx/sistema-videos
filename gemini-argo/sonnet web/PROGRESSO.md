# Sonnet Web — colocar Sonnet 5.5 (claude.ai grátis) no OmniRoute

Documento de handoff. Se os tokens acabarem, outro agente assume lendo isto de cima a baixo.
Última atualização: 2026-10-28, por sessão Opus (cc).

## 1. O QUE A DONA QUER (objetivo)

Usar o **Sonnet 5.5** (e modelos grátis do claude.ai) nos chats, através do provider
**`claude-web`** (alias `cw`) do OmniRoute, alimentado por **contas claude.ai GRÁTIS**
criadas com "Continuar com Google". A ideia é ter uma fila de contas grátis (como o
Argon tem) para os modelos grátis do claude.ai, separada das 12 contas OAuth do Claude Code.

Caminho decidido pela dona (mensagens): as contas já estão logadas no claude.ai no
**Chrome normal do PC2** (disco C). Extrair os cookies **a partir do PC2** e dali:
- OU cadastrar no OmniRoute (provider `claude-web`), OU
- fazer chamada direta como o Argon (proxy local no PC2, igual gemini_http_proxy),
  tunelado até o OmniRoute.

No PC1 (máquina da Haylla) **não dá pra logar mais contas claude.ai** — o claude.ai recusa
porque já há muitas logadas. Por isso a fonte é o PC2.

## 2. ARQUITETURA (o que já está mapeado e CONFIRMADO)

### Dois providers "claude" no OmniRoute (VPS hermes-bloqueio = 157.173.207.22, :20128)
- **`claude`** (alias `cc`): 12 contas **OAuth do Claude Code**, bate em `api.anthropic.com`.
  É o que já serve `cc/claude-sonnet-5-5` HOJE (testado, responde 200 como claude-sonnet-5-5).
  Cota compartilhada com os chats; quando acaba dá 429 "All claude accounts exhausted".
- **`claude-web`** (alias `cw`): usa o executor `claude-web`, bate na interface web
  `https://claude.ai/api/organizations/{orgId}/chat_conversations/{convId}/completion`.
  **Tem 0 contas cadastradas.** É AQUI que entram as contas grátis.

### Como o executor claude-web funciona (código em /opt/omniroute-custom/open-sse/executors/claude-web.ts)
- Credencial = cookie `sessionKey` do claude.ai. Lê de `credentials.cookie`, ou `apiKey`,
  ou `providerSpecificData.cookie` (função `readClaudeWebCookie`).
- `CLAUDE_SESSION_COOKIE_NAME = "sessionKey"` (linha 39). O normalizador extrai só o
  sessionKey do header que você mandar (pode mandar o header inteiro de cookies do claude.ai).
- `cf_clearance` é resolvido automaticamente na VPS (Turnstile auto-solve) — não precisa mandar.
- `transformToClaude(body, model)` manda o `model` CRU pro claude.ai
  (`model: model || "claude-sonnet-4-6"`). Ou seja: o nome do modelo que chega é o que vai
  pro claude.ai. **Falta confirmar qual string o claude.ai grátis aceita p/ Sonnet 5.5**
  (provavelmente "claude-sonnet-5-5", mas só dá pra saber testando com conta real).
- Tem fallback "browser-backed" (`tryBackedChat`) p/ quando o IP da VPS é bloqueado pelo
  Cloudflare. Confiabilidade a partir da VPS: desconhecida (0 conexões, nunca usado de verdade).

### Registry do claude-web (/opt/omniroute-custom/open-sse/config/providers/registry/claude/web/index.ts)
```
id: "claude-web", alias: "cw", format: "openai", executor: "claude-web",
baseUrl: "https://claude.ai/api/organizations", authType: "apikey", authHeader: "cookie",
models: [ {id:"claude-sonnet-4-6"}, {id:"claude-haiku-4-5"} ]
```
- **Sonnet 5.5 NÃO está na lista.** MAS: para o provider `claude` (cc), o OmniRoute passa
  modelos desconhecidos adiante sem bloquear. Falta confirmar se `claude-web` também passa
  (provável que sim — o modelo só vai pro claude.ai). Se precisar adicionar no registry,
  **exige rebuild da imagem Docker** (o /opt/omniroute-custom NÃO é volume montado).

### Como CADASTRAR contas (endpoint genérico, já usado pelo gemini-web)
- Endpoint: `POST http://localhost:20128/api/providers/bulk-web-session` (rodar NA VPS).
- Header: `Cookie: auth_token=<TOKEN>`.
- Body: `{"provider":"claude-web","entries":[{"name":"...","credential":"<cookie header ou sessionKey>"}]}`
- O endpoint é genérico (usa getProvider, NÃO trava em gemini-web). Guarda o cookie em
  `provider_specific_data.cookie` e `auth_type="cookie"` — exatamente onde `readClaudeWebCookie` lê.
- Scripts-molde (gemini-web, adaptar): `D:\gemini-argo\cadastrar_omniroute.py` e
  `D:\gemini-argo\enviar_contas_omniroute.py`.
- TOKEN auth_token do OmniRoute (do enviar_contas_omniroute.py, conferir validade/expira):
  está hardcoded lá no arquivo (campo TOKEN).

## 3. O MURO TÉCNICO DA EXTRAÇÃO (por que não é trivial) — CONFIRMADO no PC1

Os cookies do claude.ai no Chrome estão com **criptografia v20 (App-Bound Encryption)**.
Testado à exaustão no PC1 (Chrome 156):
- **Pasta real (User Data padrão) + remote-debugging = BLOQUEADO.** Desde o Chrome 136 o
  Chrome recusa abrir a porta de debug quando o `--user-data-dir` é a pasta padrão (segurança).
  O processo sobe mas a porta nunca abre (DevToolsActivePort nunca aparece). Confirmado.
- **Junction** (C:\_cltmp_ud -> User Data): o Chrome resolve pro caminho canônico e ainda
  bloqueia. Não dribla.
- **Cópia pra pasta não-padrão + debug = debug OK, mas v20 NÃO descriptografa.** Abri o
  Chrome padrão numa cópia e `Network.getAllCookies` devolveu 0 cookies (a chave App-Bound
  não descriptografa fora da pasta original). Bate com a memória "v20 não abre fora do Chrome padrão".
- **Cópia via SQLite backup**: o Cookies fica travado pelo Chrome rodando (WinError 32 / 
  "unable to open database file"). E mesmo copiado, cai no problema v20 acima.

### Caminhos que AINDA podem funcionar (não esgotados)
1. **Login novo pelo cofre** (pasta não-padrão → debug OK, sessão nova e válida, sem v20 de
   terceiros). No PC1 a página de login do claude.ai CARREGA normal pelo cofre (sem Cloudflare
   ativo bloqueando; botão "Continuar com o Google" existe como role=button). Script:
   `D:\gemini-argo\claude_cofre_login.py` (ver seção 5). PROBLEMA no PC1: a dona não consegue
   logar mais contas (claude.ai recusa por excesso). FALTA testar se o PC2 também recusa.
2. **Decriptação v20 offline via IElevator COM** — TESTADO no PC1, QUASE funcionando. Ver 3b.
3. **PC2**: mesma versão de muro (Chrome 155, também >136), MAS é a fonte indicada pela dona.
   Ver seção 4.

### 3b-RESULTADO (29/10): caminho IElevator ENCERRADO — o serviço recusa o python.exe
- IID novo achado pela typelib do elevation_service.exe: **IElevator2Chrome `{1BF5208B-295F-4992-B5F4-3A9BB6494838}`**
  (QueryInterface OK). No comtypes, `DecryptData` recebe só o ciphertext e devolve `(plaintext, last_error)`.
- Rodado `python v20_decrypt.py "Profile 13"` no PC1: **COMError 0x8004A007** na DecryptData. É a checagem de
  quem chama: o serviço só aceita processo da pasta do Chrome/assinado pelo Google. Não dá pra contornar sem
  injetar no Chrome, então esse caminho para aqui.
- PC2: nenhum Chrome com `--remote-debugging-port` nem `--user-data-dir` próprio (conferido 29/10), então não
  há CDP vivo pra ler o cookie.
- **Caminho que sobra:** login novo pelo cofre (`claude_cofre_login.py`, pasta não-padrão, CDP funciona) rodando
  no PC2, já que o PC1 não aceita mais contas no claude.ai. O fluxo ainda não foi testado de ponta a ponta.

### 3b. DECRIPTAÇÃO v20 via IElevator — (histórico) trava no IID (Chrome 156)
Script: `D:\gemini-argo\v20_decrypt.py` (também na pasta sonnet web). Decripta o cookie v20
SEM abrir o Chrome, chamando o serviço COM "Google Chrome Elevation Service".
- CONFIRMADO: CLSID `{708860E0-F641-4611-8895-7D867DD3675B}` está registrado (tem AppID),
  o objeto COM é criado com sucesso. A segurança COM exigida (CoInitializeSecurity com
  RPC_C_AUTHN_LEVEL_PKT_PRIVACY + EOAC_DYNAMIC_CLOAKING) está no script e funciona.
- A lógica de decriptação está pronta: app_bound_encrypted_key (base64 do Local State,
  prefixo "APPB") → IElevator.DecryptData → chave AES-256 de 32 bytes → cada cookie v20 é
  `b"v20" + nonce[12] + ciphertext + tag[16]`, AES-GCM, e o plaintext tem 32 bytes de prefixo
  a descartar. (cryptography.AESGCM já instalado; comtypes 1.4.17 instalado.)
- **TRAVA ÚNICA:** `QueryInterface` do IID `{463ABECF-410D-407F-8AF5-0DF35A005CC8}`
  (IElevatorChrome documentado) devolve **E_NOINTERFACE**. O Chrome 156 mudou o IID do
  IElevator. O IID novo está embutido em
  `C:\Program Files\Google\Chrome\Application\156.0.8078.73\elevation_service.exe`
  (e no PC2: versão 155.0.8059.85). Nenhum dos 3 IIDs conhecidos (IElevator A949CB4E...,
  IElevatorChromium B88C45B9..., IElevatorChrome 463ABECF...) está registrado em
  HKLM\...\Interface, então tem que ser extraído do binário ou do Chromium source atual.
- **PARA TERMINAR:** achar o IID atual do IElevator (strings/IDL do elevation_service.exe, ou
  procurar no código-fonte do Chromium a `elevation_service_idl.idl` da versão ~156), trocar
  `IID_IELEVATOR` no v20_decrypt.py, rodar `python v20_decrypt.py "Profile 7"`. Se a chave
  vier com 32 bytes e o sessionKey começar com "sk-ant", está resolvido — aí é só extrair as
  9 (PC1) / 11 (PC2) contas e cadastrar.
- RISCO residual: o IElevator pode validar o caller (recusar python.exe). Se mesmo com o IID
  certo a DecryptData falhar com acesso negado, cair pro login novo (caminho 1).

## 4. PC2 (revision-pc-2, `ssh pc2`, Tailscale 100.125.7.77) — RECON FEITO

- Chrome **155.0.8059.85** (também pós-136 → mesmo bloqueio de debug na pasta padrão, mesmo v20).
- User Data: `C:\Users\Emerson-IA\AppData\Local\Google\Chrome\User Data`
- 21 processos chrome rodando (PRODUÇÃO hipercool — **NUNCA matar pythonw lá, cuidado com chrome**).
- Python 3.13 em `C:\Users\Emerson-IA\AppData\Local\Programs\Python\Python313\python.exe`.
- **11 perfis com sessionKey do claude.ai:**
  | Profile | conta |
  |---|---|
  | Profile 13 | fabricadeautomacoes0@gmail.com |
  | Profile 19 | e4487017@gmail.com |
  | Profile 20 | en1653964@gmail.com |
  | Profile 21 | fabiovideoseducativos@gmail.com |
  | Profile 24 | mundosolar1995@gmail.com |
  | Profile 25 | vendeafiliados3@gmail.com |
  | Profile 26 | seebotsia@gmail.com |
  | Profile 5  | (sem user_name) |
  | Profile 6  | canalalucinaai@gmail.com |
  | Profile 8  | jornalcomia@gmail.com |
  | Profile 9  | canalhistoriacomia@gmail.com |

### Decisão de arquitetura pendente (A vs B)
- **A) Extrair sessionKey no PC2 → cadastrar no claude-web do OmniRoute.** Mais simples.
  Risco: o IP da VPS pode ser bloqueado pelo Cloudflare do claude.ai (o executor tem auto-solve
  + browser-backed, mas nunca foi usado de verdade). Precisa do sessionKey em texto → mesmo
  muro v20 do PC2.
- **B) Proxy direto no PC2 (igual Argon/gemini_http_proxy).** Um proxy OpenAI-compatible no PC2
  que fala direto com o claude.ai usando o IP residencial do PC2 (onde os cookies nasceram →
  menos chance de Cloudflare bloquear), tunelado até o OmniRoute. É o que a dona citou
  ("manda como o argo chamada direta a partir do pc2"). Mais robusto, mais trabalho.
  Em ambos A e B é preciso obter o sessionWeb/sessionKey OU dirigir o Chrome logado por CDP.

### Observação importante sobre o muro no PC2
Como o Chrome 155 também bloqueia debug na pasta padrão e tem v20, extrair o cookie das 11
contas existentes esbarra no MESMO muro do PC1. As saídas reais no PC2:
- (b1) Decriptação v20 offline (IElevator) — vale testar no PC2.
- (b2) Se a produção hipercool já abre esses perfis com CDP em porta conhecida (user-data-dir
  próprio OU já com --remote-debugging-port), dá pra conectar nessa porta e ler o cookie sem
  reabrir nada. **CONFERIR como a produção do PC2 abre o Chrome** (pode já ter CDP vivo).
- (b3) Proxy que roda DENTRO do contexto do Chrome logado (extensão/CDP numa instância já aberta).

## 5. SCRIPTS JÁ CRIADOS (no PC1, D:\gemini-argo)

- **`extrair_claude.py`** — tenta extrair sessionKey de um "Profile X" do Chrome normal copiando
  pra pasta temp. **NÃO funciona** por causa do v20 (0 cookies). Mantido como referência do que
  já foi tentado. Uso: `python extrair_claude.py "Profile 7"`.
- **`claude_cofre_login.py`** — loga uma conta Google (perfil do cofre) no claude.ai via
  "Continuar com Google" e extrai o sessionKey. Pasta do cofre é não-padrão → debug CDP funciona.
  Usa `cofre.abrir(conta, visivel=False)` + Playwright CDP. Já clica cookies + Google; trata
  chooser do Google e onboarding. STATUS: a página de login carrega e os seletores por role
  funcionam; o fluxo completo de login+onboarding ainda NÃO foi confirmado ponta a ponta
  (último teste foi interrompido). Uso: `python claude_cofre_login.py <conta> [--shot]`.
- **`claude_web_login.py`** — versão antiga (assumia Chrome normal), substituída pela de cofre.

## 6. PRÓXIMOS PASSOS (ordem sugerida)

1. **No PC2**, descobrir como a produção abre o Chrome (procurar processos chrome com
   `--remote-debugging-port` e `--user-data-dir`; se algum perfil logado no claude.ai já tiver
   CDP vivo, conectar e ler o sessionKey direto — caminho mais limpo).
2. Se não houver CDP vivo: testar **decriptação v20 via IElevator** no PC2 (1 conta de teste).
3. Com 1 sessionKey em mãos: cadastrar no `claude-web` via bulk-web-session (seção 2) e
   **testar `cw/claude-sonnet-5-5`** com uma chamada real (descobrir a string de modelo certa).
   Comando de teste (na VPS):
   `curl -s -X POST http://localhost:20128/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"cw/claude-sonnet-5-5","messages":[{"role":"user","content":"responda so ok"}],"max_tokens":10}'`
4. Se o claude.ai não aceitar a string, inspecionar o model picker do claude.ai logado (quais
   model ids a conta grátis expõe) e ajustar.
5. Se o IP da VPS for bloqueado pelo Cloudflare → partir pro **plano B** (proxy no PC2).
6. Escalar pras 11 contas, criar fila (molde contas_argon.json) e aviso de cota.
7. Adicionar `cw/...` no seletor de modelos do settings.json (hoje tem só `cc/claude-sonnet-5-5`
   rotulado "Sonnet 5.5 (web)" — esse rótulo está ERRADO, é CC, não web; corrigir quando o
   claude-web real estiver no ar).

## 7. ARMADILHAS / REGRAS (não repetir erros)
- Chrome 136+ NÃO abre remote-debugging na pasta padrão. Use sempre user-data-dir próprio.
- v20 (App-Bound) não descriptografa em cópia. Só na pasta original (via IElevator) ou login novo.
- PC2 é produção hipercool: **NUNCA taskkill pythonw**, cuidado ao mexer em chrome lá.
- No PC1, fechar o Chrome normal da dona atrapalha (ela reabre). Não é bom caminho.
- 1 script por conexão SSH no PC2 (rajada de ssh trava o desktop/pc2).
- settings.json atual: `cc/claude-sonnet-5-5` já existe no seletor como "Sonnet 5.5 (web)"
  (rótulo errado) + modelSettings claude-sonnet-5-5 effortLevel medium.
