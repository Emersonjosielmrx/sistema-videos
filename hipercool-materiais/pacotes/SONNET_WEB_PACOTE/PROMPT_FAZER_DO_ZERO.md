# Prompt para fazer o Sonnet web do zero, sem nenhum arquivo do pacote

Como usar: abra um chat de IA com agente (Claude Code, por exemplo) que tenha acesso ao seu PC Windows e à sua VPS por
SSH. Cole TUDO que está abaixo da linha. Ele constrói o sistema inteiro. Nada aqui contém senha, cookie ou chave: o
agente vai pedir o que faltar na hora, e o que for segredo fica só em `segredos\` no seu PC.

---

Você vai construir um sistema que dá **Claude Sonnet 5.5 de graça** no Claude Code (VS Code) usando várias contas
**gratuitas** do claude.ai. O servidor é o **OmniRoute** (gateway de IA de terceiros, em Docker, na minha VPS), que já
traz um provedor chamado `claude-web` (prefixo `cw/`). Cada conta do claude.ai entra no OmniRoute com o cookie de sessão
dela. O modelo final no VS Code se chama `cw/claude-sonnet-5-5`. Responda sempre em português, direto, sem enrolar.

## Regras que não se quebram

1. **Nunca duas contas pelo mesmo IP, nem em teste.** Google e claude.ai ligam contas que saem do mesmo IP e barram o
   grupo inteiro de uma vez (já aconteceu com outro serviço: 14 contas banidas juntas). Cada conta só fala com o serviço
   pela saída dela. É **proibido** fazer laço sobre a lista de contas ("criar todas", "testar todas", "medir todas").
   Uma conta por vez, espaçadas ao longo de horas e dias. Comece com 3 a 5 contas. Se uma conta for banida, o IP dela
   nunca é reusado em outra conta.
2. **Segredo nunca é impresso nem copiado.** Cookie, chave `sk-` do OmniRoute, senha do painel e IP da VPS ficam em
   variáveis ou em `segredos\` (pasta que não sai do PC). Nunca ponha em log, em chat, em commit ou em arquivo de
   documentação.
3. Antes de alterar o banco do OmniRoute (`/opt/omniroute/data/storage.sqlite`), faça backup com `cp`. Antes de alterar o
   proxy, copie o `proxy.mjs` para `.bak`.
4. Se algo pedir telefone/SMS, **pare** e me avise. Não peça nem digite código.
5. Antes de dizer que terminou, rode os testes da seção 9 e me mostre o resultado real.

## 1. O que eu preciso que você me pergunte primeiro

- IP da VPS e se o `ssh` já entra sem senha (apelido `hermes-bloqueio` no `~\.ssh\config`; todos os scripts usam esse nome).
- Se o OmniRoute já está instalado (contêiner `omniroute`, porta 20128, dados em `/opt/omniroute/data`). Se não estiver,
  instale pela documentação dele e crie uma chave de API (`sk-...`) no painel: é a chave do VS Code.
- Quais contas Google vão virar contas do claude.ai (comece com poucas). Cada uma precisa estar logada num perfil de
  Chrome próprio (um "cofre": uma pasta de perfil por conta, abrindo o Chrome com `--remote-debugging-port` diferente
  para cada uma). O cofre e a senha eu faço à mão.

## 2. Arquitetura

```
VS Code (Claude Code) ── ANTHROPIC_BASE_URL = http://IP_DA_SUA_VPS:20133
   ▼
VPS: proxy Node :20133 (na frente do OmniRoute, opcional mas recomendado)
   ▼
VPS: OmniRoute :20128 ── provedor claude-web, N contas, rodízio "fill-first" (usa a primeira até esgotar)
   ▼
claude.ai (cada conta com o cookie sessionKey dela)
```

No **PC** ficam os scripts em Python (D:\sonnet web) que criam/entram na conta, tiram o cookie e renovam antes de vencer.
Na **VPS** ficam o OmniRoute e alguns scripts pequenos que leem e organizam as contas no banco dele.

## 3. No PC: entrar no claude.ai e tirar o cookie

**3.1 Criar/entrar na conta (`claude_criar.py`).** Para cada conta, abre o Chrome do perfil dela e vai em claude.ai >
"Continuar com o Google". Pontos que custaram caro para descobrir:

- O login do Google tem que ser feito por **CDP cru** (websocket do Chrome via aiohttp: `DOM.performSearch` para achar o
  botão e `Input.dispatchMouseEvent` para clicar), **sem o Playwright ligado na aba**. Com o Playwright conectado, o
  claude.ai responde "Não foi possível verificar seu navegador" na volta do Google. Só depois que a página sai de
  `/login` é que o Playwright pode entrar para as telas do cadastro.
- Telas do cadastro: (a) termos: marque **só** a caixa dos termos/maior de 18, deixe a de e-mail promocional
  desmarcada; (b) "Criar conta"; (c) planos: clique **somente** em "Use o Claude gratuitamente", nunca em Pro/Max;
  (d) "Pular" (app de desktop); (e) "Configurar depois" (área de trabalho); (f) chega no chat.
- Está logado quando a URL é `/chat`, `/new` ou `/recents`, ou quando `/api/organizations` devolve um uuid.
- **Espere uns 40 segundos antes de fechar o Chrome**: fechar logo depois do login faz o `sessionKey` não ir para o
  disco e a sessão se perde.
- Telefone/SMS: pare (regra 4). Se o navegador for o do PC de casa e o claude.ai barrar, tente de outra máquina/IP que
  seja daquela conta (regra 1), nunca pelo IP de outra conta.

**3.2 Ler o cookie (`pegar_cookies.py`).** Sem abrir página e sem mostrar valor: pegue `http://127.0.0.1:PORTA/json/version`,
use o `webSocketDebuggerUrl` e mande **`Storage.getCookies`** para o navegador inteiro. Filtre os cookies do domínio
`.claude.ai`; o essencial é o `sessionKey`. Monte o cabeçalho `a=b; c=d` com todos eles. Grave em
`D:\sonnet web\segredos\cookies.json` no formato:

```json
{ "sua_conta@gmail.com": { "cookie": "<SEGREDO_REMOVIDO>", "orgId": "...", "deviceId": "...", "expira": 1795000000, "em": "2026-11-03 10:00" } }
```

`expira` é o vencimento do `sessionKey` (a sessão dura ~4 semanas). **Grave de forma atômica**: releia o arquivo na hora,
altere só a conta, escreva num `.tmp` e troque com `os.replace` (vários scripts escrevem o mesmo arquivo; senão uma
conta some).

## 4. Na VPS: cadastrar as contas no OmniRoute (`cadastrar_claude_web.py`)

Script Python que roda **na VPS** e recebe o `cookies.json` pela entrada padrão. Fluxo:

1. Senha do painel = variável `INITIAL_PASSWORD` do contêiner: `docker exec omniroute printenv INITIAL_PASSWORD`.
2. `POST http://localhost:20128/api/auth/login` com `{"password": ...}`. A resposta traz `Set-Cookie: auth_token=...`;
   use esse cookie nas chamadas seguintes.
3. `GET /api/providers`. Monte o mapa das conexões `claude-web` por nome. O nome de cada conta é
   `claude-web <parte do e-mail antes do @>`.
4. Conta que **já existe**: `PUT /api/providers/<id>` com `{"apiKey": <cookie>, "isActive": true}` (atualiza, não
   duplica). Conta nova: junte e envie `POST /api/providers/bulk-web-session` com
   `{"provider": "claude-web", "entries": [{"name": "...", "credential": "<cookie>"}]}`.
5. Opção `--simular` que só mostra o que faria. Nunca imprima o cookie.

Comando do PC: `type segredos\cookies.json | ssh hermes-bloqueio 'S=$(docker exec omniroute printenv INITIAL_PASSWORD); python3 /opt/omniroute/cadastrar_claude_web.py "$S"'`

**Passo obrigatório depois de cadastrar** (faça o backup do banco antes):

```sql
UPDATE provider_connections SET health_check_interval=0, test_status='active', last_error=NULL, error_code=NULL
WHERE provider='claude-web';
```

Por quê: o health check do OmniRoute usa um fetch comum da VPS, o Cloudflare responde "Just a moment..." 403 e ele marca
o cookie como revogado ("expired") à toa. O chat de verdade usa um cliente TLS que imita o Chrome e passa. Intervalo 0
desliga o health check. Conta nova sempre vem com intervalo padrão: repita o UPDATE a cada cadastro.

Regra de limite (depois de ver o formato em `/api/settings`, com backup): em `providerErrorRules.claude-web`, resposta
429 contendo "rate limited" deixa a conta **10 minutos de lado**. Sem isso o gateway re-tenta todas as contas a cada 3 s.

## 5. Scripts auxiliares na VPS (cada um é um arquivo pequeno em /opt/omniroute/)

Todos leem `/opt/omniroute/data/storage.sqlite` (tabelas `provider_connections` e `usage_history`).

- **`ler_claude_web.py`**: só leitura. Imprime JSON com cada conta `claude-web` (nome, ativa, prioridade, limitada até
  quando) e o uso das últimas 24 h (contagem e latência por status). Sem segredos.
- **`sonnet_estado.py`**: só leitura. JSON `{agora, contas:[{nome, ativa, status, erro, limitada_ate}]}`. Regra extra: conta
  com **5 ou mais respostas 403 e nenhuma 200 em 24 h** recebe status `error` ("sessão do claude.ai recusada"), porque
  com o health check desligado ela pareceria saudável.
- **`sonnet_oi.py`** (timer systemd ou cron a cada 1 min). Conta com `rate_limited_until` novo = "oi agendado" para essa hora.
  Passada a hora, mande `POST /v1/chat/completions` com `{"model":"cw/claude-sonnet-5-5","stream":false,"messages":[{"role":"user","content":"responda so: oi"}]}`
  **só naquela conta**, com o cabeçalho `x-omniroute-connection: <id da conexão>`. Só vale se o cabeçalho de resposta
  `x-omniroute-selected-connection-id` for o mesmo id e o corpo tiver um id começando com `chatcmpl-`. Respondeu =
  gravou `voltou_em`. Falhou = tenta de novo em 10 min. No máximo 8 por rodada. Se o gateway limpar o limite sozinho
  antes do oi, tire a conta da espera sem contar como "volta confirmada". Estado em `sonnet_oi.json`, gravado de forma
  atômica; contas apagadas saem do estado. Horas sempre com fuso (a VPS pode estar em outro fuso).
- **`ordenar_contas_cw.py`** (cron a cada 2 min). Reordena `priority` das contas ativas, sem desligar nenhuma. Grupos:
  0 = respondeu 200 e não falhou depois; 1 = sem falha recente; 2 = falhou na última hora (429/502/503/504);
  3 = sessão caiu (401/403 sem 200 depois) ou limitada agora. Ordena por grupo, depois pela resposta mais recente, e grava
  a prioridade 1..N. Opção `--simular`.
- **Combo opcional** (só se eu também tiver contas pagas do Claude Code no OmniRoute): combo `priority` com `cw/claude-sonnet-5-5`
  primeiro e `claude/claude-sonnet-5-5` de reserva, e um mapeamento do nome do modelo para esse combo (`/api/combos` e
  `/api/model-combo-mappings`).

## 6. Proxy :20133 na frente do OmniRoute (serviço systemd, Node 20+)

Um servidor `http` em Node que repassa tudo para `127.0.0.1:20128` e só mexe em pedidos `POST .../messages` e
`.../chat/completions`. Duas funções:

1. **Esforço máximo.** O executor `claude-web` do OmniRoute manda por padrão `effort: low` e `thinking_mode: off`. Se o corpo
   tiver o campo `reasoning_effort`, ele usa `effort = <valor>` e `thinking_mode = extended` (valores: low, medium,
   high, xhigh, max). Então: para modelos `cw/*`, `claude-sonnet-5-5`, `claude/claude-sonnet-5-5` e `cc/claude-sonnet-5-5`,
   se o corpo não tiver `reasoning_effort`, injete `"reasoning_effort": "max"`.
2. **Olhos para imagem (`visao.mjs`).** O claude-web **descarta imagem** (responde "não consigo ver nenhuma imagem"). Para
   esses modelos, cada imagem do pedido (blocos `image` e `image_url`, **inclusive dentro de `tool_result`**, que é como
   o Read do Claude Code devolve um .png) é enviada a outro modelo seu que enxerga (variável `VISAO_MODELO`, por
   exemplo um Gemini Flash do próprio OmniRoute) com este pedido: "Descreva esta imagem para alguém que não pode vê-la:
   1) transcreva literalmente todo texto visível, 2) descreva layout, elementos, posições e cores, 3) aponte o que for
   estranho; diga 'ilegível' quando for o caso". O texto volta como bloco de texto logo depois da imagem. **Dentro de
   `tool_result` a imagem tem que ser trocada pelo texto** (com a imagem lá o claude-web devolve 400 "No user message
   found"). Cache por hash da imagem (até 500), porque o Claude Code reenvia o histórico a cada turno.

Arquivo de serviço: `WorkingDirectory=/opt/antigravity-cc-proxy`, `ExecStart=/usr/bin/node proxy.mjs`,
`Environment=LISTEN=20133 UP_HOST=127.0.0.1 UP_PORT=20128`, `Restart=always`. Libere no firewall só a 20133 e o SSH.

## 7. Manutenção no PC (tarefas agendadas do Windows, sem janela)

- **Zelador, 1x por dia (04:20).** Para cada conta: se o `sessionKey` vence em **menos de 14 dias** ou o OmniRoute marcou a conta
  com cookie ruim, renove. **Reler o cookie devolve a mesma sessão** e não renova nada. Então: se o Chrome tem a mesma
  sessão (mesmo `expira`), apague **só o `sessionKey`** daquele perfil (`Storage.clearCookies` filtrado ou
  `Network.deleteCookies`), entre de novo pelo Google (seção 3.1) para gerar sessão nova, e só aceite se o novo
  vencimento for maior que o antigo + 10 minutos. Aí grave e atualize a conta no OmniRoute (PUT, sem duplicar) e repita
  o UPDATE do health check. Depois de renovar, mande um "oi" só naquela conta: se der **403 de novo com sessão nova, ela
  está barrada no claude.ai**: desligue (`is_active=0`), anote em `contas_barradas.json` e avise. No máximo **5 por
  rodada** (o Google trava depois de muitos logins seguidos). Opções `--simular` e `--so <conta>`.
- **Monitor, a cada 10 min.** Lê `sonnet_estado.py` por SSH (stdin fechado, timeout, 3 falhas seguidas = um aviso só).
  Todas as contas sem uso: avise uma vez, com a hora em que a primeira volta (hora local). Voltou: só avise depois de
  **2 pedidos reais** pelo claude-web (id `chatcmpl-`). Menos de 5 contas boas: avise no máximo 1x por dia.
  Opção `--status` só imprime.
- Avisos: uma função `avisar(texto)` que escreve num log e, se eu configurar um bot do Telegram, também manda.

## 8. Limites conhecidos (me avise, não esconda)

- O OmniRoute joga o **histórico inteiro como uma conversa nova** do claude.ai a cada pedido. A conta gratuita tem limite
  por janela de 5 horas, então esgota rápido. Mais contas = mais cota, não resolve de vez.
- Imagem nunca é nativa: só descrição por outro modelo.
- O conteúdo de `tool_result` (texto) precisa chegar ao modelo como texto da mensagem; teste com um Read de arquivo.
- 502 "message_start is out of order" acontece de vez em quando: repita o pedido.
- Sessão dura ~4 semanas: sem o zelador, tudo para no mesmo dia.

## 9. Testes que provam que funciona (rode e me mostre a saída real)

1. Na VPS: `curl -s localhost:20128/v1/chat/completions -H "Authorization: Bearer sk-SUA_CHAVE" -H "Content-Type: application/json" -d '{"model":"cw/claude-sonnet-5-5","messages":[{"role":"user","content":"quanto e 17x23?"}]}'`
   deve responder **391** com id `chatcmpl-...` (id `msg_...` seria outro provedor, não o claude-web).
2. Formato do Claude Code (`/v1/messages`, cabeçalho `x-api-key`) com uma ferramenta declarada: deve voltar um bloco
   `tool_use` com o input certo e `stop_reason: tool_use`.
3. Pergunta pequena 4 vezes seguidas: respostas OK, girando entre as contas conforme a prioridade.
4. Imagem pelo proxy :20133: mande uma imagem simples (um quadrado vermelho com um texto) e confira se a resposta cita a cor e o texto.
5. `sonnet_estado.py` e `ler_claude_web.py` imprimem JSON válido, sem cookie.
6. `--simular` do zelador e do cadastro mostram o plano sem gravar nada.

## 10. Configurar o VS Code

Em `settings.json` do VS Code, em `claudeCode.environmentVariables`, defina: `ANTHROPIC_BASE_URL = http://IP_DA_SUA_VPS:20133`,
`ANTHROPIC_API_KEY` e `ANTHROPIC_AUTH_TOKEN` = a chave `sk-` do OmniRoute, `ANTHROPIC_MODEL` = `cw/claude-sonnet-5-5`.
Faça backup do `settings.json` antes. Peça a chave a mim na hora, não a grave em nenhum arquivo do projeto.

## Ordem de trabalho

Faça nesta ordem e me mostre o resultado de cada passo antes do seguinte: (1) perguntas da seção 1; (2) VPS e OmniRoute
funcionando; (3) **uma** conta de ponta a ponta (seções 3 e 4) e o teste 1; (4) scripts da seção 5; (5) proxy da seção 6
e testes 2 a 4; (6) mais contas, **uma por vez**; (7) zelador e monitor (seção 7); (8) VS Code (seção 10).
