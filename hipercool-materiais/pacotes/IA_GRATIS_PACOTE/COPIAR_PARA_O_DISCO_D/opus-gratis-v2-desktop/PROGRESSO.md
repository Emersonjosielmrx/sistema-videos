# PROGRESSO — opus-gratis (pool do Genspark / Opus 5.5)

Retomável: cada item marcado quando feito **e** testado.

## 30/10 — virou projeto (molde argo/sonnet web)

Antes o `opus-gratis` era só pesquisa (`RESULTADO.md`) + um helper de navegador (`nav.py`). A dona pediu:
"torne ele um projeto como o argo gemini e sonnet web". O Genspark foi o único da pesquisa que **funciona
de verdade** (Opus 5.5, 100 créditos/dia por conta Google). Então montei o pool.

### Investigação ao vivo do Genspark (conta de teste conta_exemplo)
- Chat em `genspark.ai/agents?type=ai_chat`; abrir essa URL = conversa nova já com **Claude Opus 5.5**.
- Seletores: entrada `textarea.search-input` (placeholder "Pergunte qualquer coisa, crie qualquer coisa");
  botão do modelo = botão com texto "Claude Opus 5.5"; enviar = botão "Enviar mensagem" (ou Enter envia).
- Resposta do modelo sai em `.answer-markdown` (confirmado: "oi" → "oi").
- Cadastro: **não existe formulário** — só "Entrar com Google" (OAuth). Logado = tem o `textarea`.
- Créditos: a barra (`MemberWindowCreditsBar`, `CreditEstimateChip`) fica num menu recolhido, **não** no DOM
  da página → decidido **rastrear a cota localmente** (100/dia, −3/msg, renova à meia-noite) + detectar paywall por texto.

### O que foi construído
| arquivo | papel | estado |
|---|---|---|
| `genspark.py` | fila + cota + login + driver + CLI/módulo | feito; compila; driver validado nos seletores (envio real deu resposta via nav.py) |
| `genspark_http.py` | servidor OpenAI-compatível (semáforo de vagas) | feito; compila |
| `monitor_genspark.py` | painel/zelador (sem navegador) | feito; compila |
| `contas_genspark.json` | 62 contas semeadas do cofre | feito (`semear`) |

### Decisões de projeto (copiadas do que já funciona no argo/sonnet)
- **Fila, não rodízio** (`proxima_conta`): 1ª conta pronta; paywall → fora da fila até o dia virar; 3 erros → bloqueio 30 min (igual ao gemini_argon).
- **Reutilizar a aba** do Chrome em vez de `new_page()`: aba nova via CDP num Chrome escondido não desenha e trava o `goto` do SPA (o nav.py já tratava com `bring_to_front`).
- **Não depender de `domcontentloaded`**: navego com `wait_until="commit"` + polling do campo por `GENSPARK_ESPERA_SPA` (120 s). Sob carga pesada da máquina o `domcontentloaded` não dispara em 60 s (medido: o nav.py levou 78 s no mesmo load).
- **`connect_over_cdp` com timeout 45 s**: Chrome empanzinado não trava o pedido por 3 min.
- Cota local porque a barra de créditos não está no DOM.

### Achados de ambiente (importante)
- A máquina roda a **produção de vídeo** (recapd, manhwa-react, hipercool, veo) o tempo todo; quando ela sobe
  arquivos, a rede/CPU saturam e o Genspark carrega **muito devagar** (8 s → 78 s). O pool é feito para tolerar
  isso (esperas longas), mas **o login em massa das 62 contas deve rodar quando a máquina estiver mais calma**,
  uma conta por vez (abre/fecha 1 Chrome de cada vez — não estoura RAM).
- RAM costuma ficar perto do limite (~2 GB livre). O Wise Memory Optimizer auto-otimiza; o pool abre 1 Chrome por vez.

## 30/10 — revisão adversarial (workflow, 22 agentes) + correções

Rodei uma revisão multi-agente (4 frentes + verificação adversarial) sobre os 3 arquivos. De 18 achados,
**12 confirmados reais e corrigidos** (todos com teste de lógica passando em `test_logica`, sem navegador):

| # | bug | correção |
|---|---|---|
| 1 | `marcar_sem_cota` não fixava `data_cota` → `_virar_dia` renovava a cota no mesmo dia e a conta no paywall voltava à fila | agora fixa `data_cota=hoje` |
| 2 | créditos não reservados + 2 threads pegavam a MESMA conta/aba | `proxima_conta` só escolhe contas LIVRES (`_EM_USO==0`) |
| 3 | `perguntar` deixava `RuntimeError` de fila vazia escapar (contrato: devolver None) | try/except traduz pra None |
| 4 | `_TRAVA` (RLock) não protege entre PROCESSOS → lost update no JSON (http + CLI juntos) | lock de arquivo `_trava_arq` em todo ler-modifica-grava |
| 5 | lentidão transitória do SPA marcava `logado=False` pra sempre | só marca deslogada quando o BOTÃO de login aparece; SPA que não montou = erro transitório |
| 6 | `_logado` dava True só com o textarea (visitante anônimo também vê) | exige `temInput and not temLogin` |
| 7 | termos de paywall genéricos ("upgrade", "assine") casavam com o botão fixo da UI → `SemCota` falso | lista só com frases de crédito esgotado |
| 8 | `_coletar` devolvia resposta parcial como sucesso no timeout | só devolve se estável; senão erro (incompleta) |
| 9 | `_pagina` pegava `pages[-1]` (sequestrava aba de outro projeto) | aba já no genspark → em branco → aba nova dedicada; + lock por conta no `_uma` |
| 10 | `do_POST` não capturava exceção → conexão pendurada | try/except → 500 |
| 11 | stream SSE sem enquadramento HTTP/1.1 → cliente cru travava | `Connection: close` + `close_connection=True` |
| 12 | `_flatten` punha o literal "None" com `content: null` | `m.get("content") or ""` |

Descartados (reais no código mas sem quebrar de fato): divergência de constantes monitor×genspark, `_gravar` tmp órfão, `semear`/`soltar` fora do lock (mitigados pelo lock de arquivo/`_TRAVA` mesmo assim).

## 30/10 — pedido: pôr o "Opus Genspark" no Claude Code do VS Code + pensamento máximo

Arquitetura (ver memória claude-vscode-trocador-de-modelo): o Claude Code do VS Code fala **API Anthropic** com o
**OmniRoute na VPS** (`hermes-bloqueio`, `localhost:20128`), que traduz pra cada provedor; modelos têm prefixo
(`cc/`, `kr/`, `agy/`...). O trocador fica em `C:\Users\SEU_USUARIO\Desktop\Claude VS Code - Trocar Modelo\`.

O Genspark é como o **argon**: endpoint HTTP próprio (não cookie). Então o caminho é:
1. `genspark_http.py` no ar no PC (porta 20160).
2. **Túnel SSH reverso** PC→VPS (molde do argon: `ssh -R 20160:127.0.0.1:20160 hermes-bloqueio`; manter vivo como o `argon_manter.py`).
3. **Registrar no OmniRoute** um provedor OpenAI-compatível com `base_url` = `http://127.0.0.1:20160/v1`, modelo
   `gs/claude-opus-5-5` (a API de registro do OmniRoute para provedor de endpoint — NÃO a `bulk-web-session`, que é
   só cookie — precisa ser vista na VPS; o argon foi configurado direto lá).
4. Entrada nº 8 no trocador (`USAR_8_genspark_opus.cmd` + `settings_8_*.json` copiando um existente e trocando só o
   `--model` para `gs/claude-opus-5-5`; a chave e a base são as mesmas dos outros).

**NÃO feito de propósito (ainda):** não vou fiar um backend no OmniRoute (o roteador do VS Code, ferramenta principal
da dona) enquanto o pool não devolver resposta de verdade — hoje o `_coletar` deu 0 chars porque a máquina está
saturada pela produção. Ordem certa: (a) login em massa, (b) confirmar resposta real com a máquina calma, (c) só então
túnel + provedor no OmniRoute + entrada nº 8. Fiar um backend offline quebraria o seletor do VS Code.

**Pensamento no máximo "no site":** o chat do Genspark precisa ser inspecionado para ver se tem seletor de raciocínio
(como o Gemini tem Baixo/Médio/Alto). Se tiver, o `_garantir_modelo` passa a ligar o nível alto. A conferir com a
máquina calma (precisa de navegador). Aviso do sonnet web: para pontes de chat web o nível às vezes não é controlável
(o claude-web ignora; medido 29/10).

## 30/10 — sistema unificado (genspark + 1min) e divisão de trabalho com o outro chat

Outra sessão ("outro chat") construiu `umin/umin.py` — 1min.ai pela **API** (Opus 5.5 = 3.973–20k créditos, Fable 5.1,
etc.), bem mais barato e **sem navegador** (imune à carga da máquina). Testado por mim: Opus 5.5 e Fable 5.1
respondem e **se identificam certo** (`us.anthropic.claude-opus-5-5` / `...fable-5-1`).

`genspark_http.py` virou o **front unificado** (um endpoint OpenAI, roteia por modelo):
- `1min/claude-opus-5-5`, `1min/claude-fable-5-1`, `1min/claude-opus-5`, `1min/claude-sonnet-5-5`, `1min/claude-haiku-5-5` → API (umin)
- `genspark/claude-opus-5-5` → pool de navegador
- Testado ao vivo na porta **20165** (a 20160 é do cline-ponte): `/v1/models` ok, Opus 5.5 e Fable 5.1 ok.

**Divisão de lanes (2 chats no mesmo projeto):** o outro chat cuida do `umin/` (1min API e novas fontes); eu cuido do
front unificado (`genspark_http.py`), do pool de navegador (`genspark.py`) e da fiação no VS Code/OmniRoute. O front
consome o `umin` por import (não modifico o módulo dele) — se o umin ganhar multi-conta, o front herda de graça.

**Fontes que valem pool (pela pesquisa):** Genspark (navegador, 62 contas) e 1min (API). O resto (Prophet US$0,07,
Arena só sorteio, EaseMate 30 créditos, Merlin/Kilo travados em captcha, Felo/TicNote/Poe/Gab/Kiro/Amp/Zed/... só pago)
não compensa pool.

## 30/10 noite — "logado: true" era FALSO; SSO real provado e resposta real medida

Provado ao vivo na conta conta_exemplo (Chrome do cofre, porta 9701), prints em `prints/gs_sso_*.png`:
- Deslogado, o Genspark mostra o chat e o textarea IGUAL à conta logada; o modal "Entrar ou cadastrar-se" só abre ao ENVIAR. Por isso `_logado` dava True nas 62 contas (ok=0 em todas; 5 contas seguidas com 0 chars em 240 s). O `_JS_ESTADO` só conhece "entrar|sign in|log in" e o menu em português diz "Iniciar sessão".
- A prova de login é o menu do rodapé (`.sidebar-footer .trigger`): deslogada = "Iniciar sessão"; logada = e-mail + "Créditos: N" + "Terminar sessão". Dá também o saldo real sem gastar mensagem.
- SSO que funciona (sem senha: o perfil do cofre já tem o Google): menu → "Iniciar sessão" → "Continuar com Google" → em accounts.google.com clicar a conta → volta logada.
- Resposta real: 14,1 s; 96 → 93 créditos = 3 por mensagem (CUSTO_MSG certo).
- O `innerText` de `.answer-markdown` PERDE as cercas ``` e traz a palavra "Copy" do botão; o HTML tem `<code class="hljs language-tool_call">`. O proxy do Claude Code precisa das cercas → reconstruir o markdown pelo DOM.
- 1min: site e API mostram 0 crédito na conta_exemplo; sem mais chaves não há rotação (lane do outro chat).

## 31/10 madrugada — NO SELETOR (experimental, opção 1 da dona)

Fiação feita e testada ponta a ponta:
- `genspark.py`: login provado pelo menu do rodapé (`_menu_conta`: e-mail/"Créditos: N"/"Terminar sessão" × "Iniciar sessão"),
  saldo REAL gravado por conta (`marcar_creditos`; a fila troca de conta pelo crédito de verdade), resposta com as cercas
  ``` refeitas pelo DOM (sem o "Copy"), modal de login ao enviar = `NaoLogado` na hora.
- `genspark_http.py`: prompt apresenta o sistema como "agente ao qual você está conectado" + fecho "a conversa acima já
  aconteceu" (sem isso: recusava a ferramenta no 1º turno e repetia a ferramenta no 2º). Sem conta: 429 "Nenhuma conta com
  cota" → o proxy da VPS põe o Sonnet web no lugar, com aviso.
- `og_manter.py` + tarefa `OpusGratisManter` (pythonw, 5 em 5 min e no logon): sobe o front :20165 e o túnel ssh -R
  127.0.0.1:20165 → hermes-bloqueio. Estado em `og_manter.json`.
- VPS: `fechar-20165.service` (DROP v4+v6 na eth0, enabled; de fora = sem resposta). Proxy 20133 com `PONTES`
  (`genspark-opus-5-5` → :20165 pelo caminho do Argon). Backup `proxy.mjs.bak-antes-genspark-31out`; cópia local
  `D:\gemini-argo\proxy_vps.mjs` (hash `f0d83ced…` = produção). Testado numa cópia na 20134 antes: Genspark com e sem
  ferramenta, ciclo tool_use → tool_result → resposta, e Argon igual.
- Seletor: "Opus 5.5 Genspark (experimental)" = `genspark-opus-5-5`, 2ª opção (backup `settings.json.bak_31out_genspark`).
  Testado em produção: HTTP 200 em ~29 s; opus-auto seguiu ok (3 s).

**Limite atual:** só a conta_exemplo está logada de verdade (~30 msg/dia, 3 créditos cada). O login automático das outras
chegou na escolha de conta do Google mas não voltou logado (conta_exemplo, CPU 100%) — refazer com a máquina calma.
Cada turno abre o Chrome e leva ~25–40 s.

## Pendências (ordem sugerida)
1. [ ] **Login em massa** `python genspark.py login` nas 62 contas — rodar com a máquina calma (madrugada). Uma por vez.
2. [ ] Validar ponta a ponta com a conta de teste (rodando; depende da máquina responder).
3. [ ] Medir o custo real de uma mensagem longa (agora assume 3 créditos; ajustar `GENSPARK_CUSTO`).
4. [ ] Ler os créditos reais (abrir o menu da barra `MemberWindowCreditsBar`) para não depender só da estimativa.
5. [ ] Integrar no OmniRoute (como o argo/sonnet) se a dona quiser o Opus 5.5 no seletor do VS Code — `genspark_http.py` já fala OpenAI.
6. [ ] Reuso de conversa (mandar só o turno novo) como no gemini_http — otimização.
7. [ ] Zelador agendado (tarefa) chamando `monitor_genspark.py` e religando contas deslogadas.

## 30/10 noite — por que os modelos não aparecem no seletor (achados; nada na VPS foi alterado)

**Seletor:** o `modelPicker` de `C:\Users\SEU_USUARIO\.claude-vscode\settings.json` não tem genspark/1min/fable porque a fiação nunca foi feita. Faltam 4 peças (molde = Cline, que já funciona):
1. Túnel PC→VPS da 20165: `ssh -N -R 127.0.0.1:20165:127.0.0.1:20165 hermes-bloqueio`, mantido vivo como o `D:\gemini-argo\argon_manter.py` (tarefa a cada 5 min). Não é a 20160 da seção acima: essa é do cline-ponte.
2. Rota no proxy da VPS (`/opt/antigravity-cc-proxy/proxy.mjs`, porta 20133, serviço `antigravity-cc-proxy`): copiar `isCline`/`forwardToCline` e a linha `if (isCline(j.model))` do handler. Cópia local idêntica (mesmo hash `2d8bd60c…` em 30/10 20:13): `D:\gemini-argo\proxy_vps.mjs`. Testar numa cópia em outra porta antes de reiniciar o serviço (o reinício corta as respostas em andamento).
3. Firewall ANTES do túnel: o sshd da VPS tem `GatewayPorts yes`, então a porta de túnel nasce aberta para a internet e o front não tem chave. Criar `fechar-20165.service` igual ao `fechar-20160.service` (iptables/ip6tables DROP em eth0). A 20165 está livre na VPS.
4. Entradas no `modelPicker` (+ `modelSettings`).

**Feito hoje:** Cline Opus fora do seletor (25 opções, a 1ª é o Opus Automático); `ANTHROPIC_MODEL` do VS Code (`%APPDATA%\Code\User\settings.json`) trocado de `cline-opus-5-5` para `opus-auto` (backup `settings.json.bak_30out_modelo` ao lado; `ANTHROPIC_DEFAULT_*` e `ANTHROPIC_SMALL_FAST_MODEL` ainda apontam para `cline-*`); `/v1/models` do front consertado (os valores de `MODELOS` são listas de tuplas).

**1min (lane do outro chat; não mexi no `umin/`):** às ~22h deu `INSUFFICIENT_CREDITS` (equipe "aula com ia" com 0; a pergunta mínima pedia 2.581). Calculado: usado 270.876 de uma base de 265.000. Gasto médio medido: Fable 5.1 ≈ 51 mil por mensagem, Opus 5.5 ≈ 15,5 mil, Opus 5 ≈ 14 mil, Haiku 5.5 ≈ 86. Sem recarga ou chaves novas o 1min não serve nem para teste.

**Genspark:** o login em massa marcou 62/62 como `logado`, mas nenhuma resposta real saiu. Teste de 21:38 a 21:57 pelo front: 5 contas seguidas (conta_exemplo, conta_exemplo, conta_exemplo, conta_exemplo, conta_exemplo) esperaram 240 s e voltaram com 0 chars, e o driver não conseguiu clicar no botão do modelo. Máquina na hora: 0,4 GB de RAM livre, CPU em 100%. O print que abri (`prints/gs_aulacomia_*`, 13:50–13:53) mostra o modal "Entrar ou cadastrar-se" por cima do chat, com o prompt ainda no campo de texto.
Hipótese (NÃO provada): o `logado: true` é falso positivo. 59 contas ficaram com `login_detalhe="já logada"` (nenhum login foi tentado) e `_logado` aceita `temInput and not temLogin`; o visitante anônimo também vê o campo.
Parei o front (pid 16252), que seguia passando de conta em conta por um pedido que o cliente já tinha abandonado, e fechei o Chrome órfão da porta 9706.

**Próximo:** (1) prova de login real em 1 conta (print e e-mail no menu do perfil, sem mandar mensagem); (2) se for falso positivo, trocar `_logado` por um sinal positivo (avatar/e-mail da conta) e refazer o sweep; (3) 1 resposta real ponta a ponta; (4) só então fiar (as 4 peças acima). O 1min depende de crédito.

## 31/10 01h — login em massa tentado com a máquina calma (CPU 18%, 10 GB livres)
- Consertado em `_tentar_login_google`: na tela /signin/oauth/id o e-mail é um chip (troca de conta); clicar nele travava. Agora só clica na conta em accountchooser (`[data-identifier]`) e procura 'Continuar' em laço, com log da URL.
- Mesmo assim conta_exemplo (invisível e --visivel) fica presa em accountchooser: o Google recarrega a escolha (muda o `as=`) e não volta ao genspark. Provável recusa do Google ao Chrome dirigido por CDP. NÃO rodei nas 62.
- Caminho que sobra: login à mão, uma vez por conta (`python cofre.py logar <apelido>` e fazer o SSO no Chrome), depois `python genspark.py checar`.


## 31/10 02h — melhorias copiadas do Argon/Sonnet
- Login à mão em fila: `login_fila.py` (3 janelas; detecta o login, fecha, abre a próxima). Contas não provadas pelo menu foram desmarcadas (backup `contas_genspark.json.bak_31out_rotacao`).
- Chrome QUENTE entre turnos (`_QUENTES`, fecha após 10 min parado, máx 3): 2º turno 40 s → 13-16 s (CLI) / ~21 s pelo front.
- Fim da resposta pela rede (requestfinished do `/api/agent/ask_proxy`) em vez de 9 s de texto parado; menu de créditos só na 1ª vez de cada Chrome; o clique no seletor de modelo saiu.
- **MODELO**: contas novas vêm com gpt-5.5/sonnet de padrão (era o 'GPT-5.6 Luna'). Agora `pg.route` troca `ai_chat_model` para claude-opus-5-5 no pedido. Algumas contas (conta_exemplo) não têm Opus no grátis: resposta 'benefício da assinatura' → SemCota → próxima conta.
- Rotação: Chrome quente primeiro, depois a de mais crédito.
- API pura (sem Chrome, como o Argon) NÃO dá: o ask_proxy exige g_recaptcha_token novo por pedido.
- Desktop (D:\opus-gratis-desktop): versão de 30/10 13:47, com o falso 'logado' — não serve.


## 31/10 08h40 (pc1) — v2 virou a produção do pc1
- Tarefas OpusGratisManter e ZeladorGenspark apontam para D:\opus-gratis-v2-desktop; front :20165 roda daqui (túnel → VPS PONTES genspark-opus-5-5). contas_genspark.json = a do pc1 (backup da do desktop: .bak_desktop). Cookies de conta_exemplo/6 capturados aqui. `pip install curl_cffi` feito.
- CORREÇÃO: a VPS manda `genspark/claude-opus-5-5`, que na v2 era só a automação de tela (respostas de 15-100 s e o tool-call saía errado, ex. JSON solto com name 'Run'). Agora = puro → pagina → tela; a tela antiga ficou em `tela/claude-opus-5-5`.
- Recusa 'não tenho acesso à ferramenta' (vista 1x em ~5): o front repete 1x com LEMBRETE_FERRAMENTA no fim.
- Testado pela VPS (Anthropic /v1/messages com tools): tool_use do Bash 3/3; 2º turno usa o tool_result; Read → Bash encadeado com o valor certo; ~5 s por passo.
- Diagnóstico: o front grava o último pedido cru em `ultimo_pedido.json`; `_teste_ferramenta.py` reenvia pelo PURO.

## 31/10 08h42 (pc1) — CORREÇÕES OBRIGATÓRIAS reaplicadas
- 08:37 o desktop sobrescreveu genspark_http.py + CLAUDE.md desta pasta e as correções de 08h40 sumiram. Juntei: versão do desktop (com `_caber`, limite de 185 mil) + as 3 correções. Backups: `genspark_http.py.bak-20261031-antes-correcao-pc1`, `CLAUDE.md.bak-20261031-antes-correcao-pc1`.
- Anotado no topo do CLAUDE.md como CORREÇÕES OBRIGATÓRIAS, para qualquer agente manter em versão nova. Retestado pela VPS: tool_use 6 s; 2º turno usa o resultado, 5 s.

## 31/10 08h53 (pc1) — conversa 'sem terminal'
- Conversa do Claude Code que antes passou pela tela inventou a ferramenta 'Run' 2x; depois concluiu que não há terminal e mandava a dona rodar. Corrigido no front: lembrete com os nomes exatos no fim do prompt, troca de Run/Shell/Terminal pelo PowerShell/Bash, e até 2 repetições quando vem bloco de shell sem tool_call. Pedido real (pedido_print_0845.json): 4/4 tool_call. Anotado como correções 4 e 5 no CLAUDE.md.

## 31/10 09h00 (desktop) — conta sem crédito passava como resposta
- Visto no Antigravity: "Você usou todos os seus créditos. Visite esta página para adicionar mais: upgrade" chegou como resposta (log: `OK(puro) conta_exemplo 2.1s 141 chars`) e a ponte não trocou de conta. A checagem antiga só valia para < 40 chars e a frase não estava na lista.
- Corrigido por sinal ESTRUTURAL (`genspark_api.classificar`): o aviso vem sem `_llm_model`, com `consume_usage_quota_exceeded` e `credit_exhausted`. Usado no PURO, CAPTCHA e PÁGINA. Item 6 das CORREÇÕES OBRIGATÓRIAS no CLAUDE.md.
- Enviado ao pc1 08:58 (backups `.bak-20261031-antes-sem-credito`; conferido antes que o pc1 não tinha mudado esses 3 arquivos) e front do pc1 reiniciado pelo og_manter. Teste no pc1: "16".
- 09h05: o desktop puxou a correção de ferramentas do pc1 (itens 4 e 5); os dois PCs ficam com o mesmo genspark_http.py.

## 31/10 09h30 (pc1) — revisão de erros
- Prints não chegavam ao Opus Genspark: VPS visao.mjs precisaOlhos += /^genspark-/ (backup .bak-antes-genspark-31out), 20133 reiniciado sem pedido em andamento. Testado: leu o print.
- Repetição por bloco de shell agora exige pedido para a dona rodar (_PEDE_RODAR): 'só mostre' não é executado.
- Revisado sem erro: limites de tempo da VPS (600 s + ping 15 s), log do PURO (sem bloqueio, cookies de todas as 38), turnos da VPS (blocos perdidos e timeouts só antes de 08h31). Correções 7 e 8 no CLAUDE.md.

## 31/10 09h50 (desktop) — aplicado o PARA_O_DESKTOP_APLICAR.md do pc1 + sessão longa + prints locais
- Correções 1-8 do pc1 puxadas (genspark_http.py, CLAUDE.md, PROGRESSO.md do pc1; backups `.bak-20261031-antes-pc1-0935`).
- Item 9 (`_caber`): sessão real que "misturava os chats e parava" tinha 537 mil chars e só 42 de 216 mensagens chegavam (antes: 16-26 de 199). Agora 119 de 216: resultados de ferramenta antigos encolhidos, 8 últimas inteiras, 1º pedido da dona fixo no topo.
- Item 10: `proxy_cc/visao.mjs` do desktop era stub (prints descartados). Copiado o da VPS (UP_HOST = OmniRoute 157, aceita genspark/). Teste: leu o print.
- Ponte e proxy do desktop reiniciados sem pedido em andamento.

## 31/10 09h53 (pc1) — correção 11: falas falsas de 'não tenho terminal' saem do histórico
- A sessão abriu o navegador e depois disse que não havia PowerShell (o front rodava o código das 09:25; a frase escapou do _RECUSA). Agora _fala_sem_ferramenta limpa essas falas do assistente no _flatten e o _RECUSA pega a forma geral. Testes: _teste_recusa.py 5/5 e 6/6; pedido real das 09:42: 3/3 tool_call. Front reiniciado 09:53 sem pedido em andamento.
- Apagados os pedido_print_*.json de teste (um tinha a senha do Instagram digitada no chat). O ultimo_pedido.json guarda o último pedido cru e pode conter segredo: é local, sobrescrito a cada pedido.

## 31/10 10h15 (pc1) — Sonnet no lugar do Opus (09:46-09:47) e correções 12/13
- Causa: ECONNRESET na ponte; o front do pc1 foi reiniciado/duplicado no meio de pedidos (3 'subiu' no out.log entre 09:44 e 09:53; o desktop entrava no pc1 por ssh dezenas de vezes nesse horário). Túnel estável desde 07:57; montar o prompt leva 0,03 s.
- VPS: genspark-opus-5-5 nunca mais cai no Sonnet — espera a ponte ~54 s e o substituto é o opus-auto (Opus 5.5). Testado (12 s fora → Genspark; 90 s fora → Opus Automático).
- PC: _ServidorExclusivo (2º servidor falha com WinError 10048) + reiniciar_front.ps1. Regra no topo do CLAUDE.md.

## 31/10 18h20 (desktop) — Proxy Webshare para o IP_LOCKED do 1min (pedido da dona)
- O 1min travou o IP de casa (IP_REMOVIDO) por 24 h após 3 cadastros seguidos (POST api.1min.ai/auth/oauth 400 IP_LOCKED). A dona pediu para usar o proxy da Webshare que já temos.
- NOVO `umin/proxy_umin.py`: repassador local (PAC 18250, nós 18251..18259), gêmeo do proxy_tiktok mas com portas próprias (não toca a produção do TikTok) e PAC que manda SÓ *.1min.ai pelo IP Webshare — Google e o resto saem de casa. Reusa as mesmas credenciais (D:\postador-de-videos\secrets\proxies.txt, 71 no pool). IP fixo por conta em proxy_umin_mapa.json.
- `criar_contas.py` e `login_fila.py` ganharam `--proxy` (abre o Chrome do cofre com as flags do PAC; pula a conta se o Chrome já estava aberto sem proxy, pois sairia pelo IP bloqueado).
- Achado: porta 18210 estava ocupada por um ssh → mudei o PAC para 18250 (faixa 18250-18259 livre). Sob pythonw o sys.stdout é None → protegi o reconfigure.
- Provado: `proxy_umin.py --teste` = 9/9 IPs tunelam até api.1min.ai; curl pelos nós deu IP_REMOVIDO / IP_REMOVIDO / IP_REMOVIDO (≠ IP de casa).
- FALTA: login de verdade (a dona escolhe a conta no popup do Google) para confirmar que o IP_LOCKED some pelo proxy. Rodar `python umin\login_fila.py 1 --proxy`.

## 03/11 - Opus 5.5 Genspark SOZINHO no seletor
- Seletor: novo item "Opus 5.5 Genspark (so ele)" = `genspark-opus-5-5-so` (settings.json do .claude-vscode + modelSettings xhigh).
- VPS proxy.mjs: `PONTES["genspark-opus-5-5-so"]` (mesma porta 20165 / genspark/claude-opus-5-5) com `soPonte: true` e `fonte: null`: `sonnetNoLugar` devolve 429 com o erro do Genspark, NUNCA substituto. Backup `proxy.mjs.bak-antes-genspark-so-03nov`. Testado: sem cota -> 429 "Nenhuma conta com cota agora no Genspark" (sem trocar de modelo).
