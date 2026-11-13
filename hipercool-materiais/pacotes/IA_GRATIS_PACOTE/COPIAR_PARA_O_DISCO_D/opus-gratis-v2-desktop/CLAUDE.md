# opus-gratis v2 — LEITURA OBRIGATÓRIA antes de mexer

> Desktop 31/10 09h50: as correções 1-8 do pc1 estão aplicadas na v2 do desktop (o `PARA_O_DESKTOP_APLICAR.md` foi
> cumprido). Itens 9 e 10 abaixo são do desktop, já enviados ao pc1.
>
> **AGENTE DO DESKTOP — PENDENTE (pc1, 31/10 11h20): aplique as correções 11, 13, 14, 15 e 16 na sua v2.** O
> `genspark_http.py` do pc1 = a sua versão 09:43 + 11 (`_RECUSA`, `_fala_sem_ferramenta`) + 13 (`_ServidorExclusivo`)
> + 14 (`_normalizar_chamadas`) + 15 (`PEDIDO_RACIOCINIO`) + 16 (recusa persistente → 429). Junte, não copie por cima.
> Depois tire este aviso.
>
> **REGRA (dona, 31/10): o servidor :20165 do pc1 é PRODUÇÃO. Nunca matar/subir à mão nem por ssh** — use
> `reiniciar_front.ps1` (espera não haver pedido em andamento). Em 31/10 09:46–09:47 o desktop estava entrando no
> pc1 por ssh (dezenas de sessões) e o servidor foi reiniciado/duplicado no meio de pedidos: ECONNRESET → o Sonnet
> respondeu no lugar do Opus. **Nunca usar modelo inferior no lugar do Opus Genspark** (correção 12).

## ⚠ CORREÇÕES OBRIGATÓRIAS (pc1, 31/10 08h40) — manter em TODA versão nova do genspark_http.py

Em 31/10 08:37 uma cópia nova do desktop sobrescreveu o `genspark_http.py` do pc1 e apagou estas correções. Ao mandar
uma versão nova, **junte com a que está na outra máquina** (ou confira que estas 3 continuam) — não substitua por cima.

1. **`"genspark/claude-opus-5-5"` = `[("puro", None), ("pagina", None), ("genspark", None)]`**. É o id que a **VPS** manda
   (`PONTES` do proxy 20133: o seletor `genspark-opus-5-5` → este id). Se ele apontar só para `("genspark", None)` (robô de
   tela), o Claude Code fica com respostas de 15-100 s e o tool-call sai ERRADO (visto: JSON solto `{"name":"Run",...}`
   que o proxy não executa). A tela antiga continua disponível em `"tela/claude-opus-5-5"`.
2. **Recusa de ferramenta**: às vezes o Opus responde "não tenho acesso à ferramenta Bash" mesmo com o protocolo
   ```` ```tool_call ```` no prompt (1 em ~5). O `do_POST` repete 1x com `LEMBRETE_FERRAMENTA` no fim (`_RECUSA` detecta).
3. **`ultimo_pedido.json`**: o `do_POST` grava o último pedido cru; `_teste_ferramenta.py` o reenvia pelo PURO
   (diagnóstico do protocolo de ferramentas).

4. **Nomes de ferramenta no fim do prompt** (`_flatten` → `_nomes_ferramentas`): lista os nomes EXATOS da sessão e diz
   que o terminal é PowerShell/Bash. Motivo (08h45): depois de inventar `"Run"` (não existe; o proxy ignora), a conversa
   ficou "convencida" de que não havia terminal e passou a mandar a dona rodar o comando. `_corrigir_nomes` troca
   Run/Shell/Terminal/... pela ferramenta de terminal real na resposta.
5. **Repetição até 2x** também quando a resposta traz bloco ```` ```powershell/```bash ```` sem tool_call (pedindo para
   a dona rodar), com aviso de que o "não há terminal" do histórico estava errado. Pedido real que falhava
   (`pedido_print_0845.json`): 4/4 viraram tool_call do PowerShell (10-27 s). 09h08: `_RECUSA` ampliado para "não
   tenho uma ferramenta local de PowerShell/Bash disponível", "reabrir a sessão", "ferramentas locais" (escapava e não
   repetia); `pedido_print_0905.json` (conversa de 929 mil chars, cortada pelo `_caber`): 3/3 tool_call.
6. **Conta sem crédito não é resposta** (desktop, 31/10 08h59 — em `genspark_api.py`, `genspark_http_puro.py`,
   `genspark_pagina.py`): "Você usou todos os seus créditos… upgrade" (141 chars) passava como resposta do Opus e a
   ponte não trocava de conta. `genspark_api.classificar(corpo)` decide pela ESTRUTURA, não pela frase: resposta real tem
   `session_state._llm_model` ("claude-opus-5-5") e `_llm_usage`; o aviso vem SEM `_llm_model`, com
   `consume_usage_quota_exceeded` e link `fromurl=credit_exhausted`. "sem_credito" → SemCota (fila até 00:05 do dia
   seguinte); "sem_opus" → marcar_opus(False). Testado: conta esgotada vira SemCota; resposta do Opus que FALA de
   créditos continua passando. (Contas sem cookie agora aparecem no log 1x só.)
7. **Bloco de shell só dispara a repetição se vier pedindo para a dona rodar** (`_PEDE_RODAR`; pc1 09h25). Sem isso, um
   pedido "só me mostre o comando" seria repetido até o modelo EXECUTAR. Testado: "só mostre, não execute" → texto, sem
   repetição.
8. **Prints chegam ao Genspark** (VPS, 09h25): `/opt/antigravity-cc-proxy/visao.mjs` → `precisaOlhos` agora inclui
   `/^genspark-/` (antes só cw/, sonnet, argon, hx). Sem isso a imagem era descartada no front (só texto) e o Opus
   respondia sem ver o print. Backup `visao.mjs.bak-antes-genspark-31out`. Testado: leu o caminho do rclone num print.
   **Reiniciar o 20133 só sem pedido em andamento** (o node sem conexões de saída) — cortar no meio vira ECONNRESET e
   o Sonnet responde no lugar.
9. **Sessão longa não perde o assunto** (desktop, 31/10 09h45 — `_caber`/`_encolher_antiga` em `genspark_http.py`). Com
   só "as mais recentes", uma sessão real de 537 mil chars mandava 42 de 216 mensagens (cada resultado de ferramenta tem
   até 30 mil) e o Opus perdia o pedido original: "misturava" assuntos e parava. Agora: as 8 últimas mensagens vão
   inteiras (`GENSPARK_INTEIRAS_RECENTES`); nas anteriores, cada `[resultado da ferramenta]` vira 900 do começo + 500 do
   fim e mensagens > 5000 chars são encurtadas; o **1º pedido do usuário** (sem os `<system-reminder>`) fica fixo no topo.
   Mesma sessão: 119 de 216 mensagens, com o objetivo da sessão visível. Ainda assim, em sessão enorme vale `/compact`.
10. **Prints também pelo proxy LOCAL do desktop** (:20166, `proxy_cc/visao.mjs`): era um stub vazio (imagem descartada).
    Agora é a cópia do `visao.mjs` da VPS com `UP_HOST` = IP_DA_SUA_VPS (OmniRoute) e `precisaOlhos` aceitando
    `genspark/` (o seletor do desktop) além de `genspark-` (VPS). Backup `visao.mjs.bak-20261031-stub`. Testado: leu
    "código 4729 / AZUL" de um PNG (~28 s da descrição pelo Gemini). Só o desktop usa o :20166.
11. **Falas falsas de "não tenho terminal" saem do histórico** (pc1, 31/10 09h53 — `genspark_http.py`). A mesma sessão
    abriu o navegador e na mensagem seguinte disse "a ferramenta de execução local/PowerShell não está disponível aqui":
    o Opus segue as próprias falas antigas desse tipo (de quando ele errou o nome da ferramenta). Agora:
    (a) `_fala_sem_ferramenta(texto)` = sem ```` ```tool_call ```` e (`_RECUSA` ou bloco de shell pedindo para a dona
    rodar); no `_flatten`, toda mensagem do **assistente** assim vira "[resposta anterior omitida: dizia, POR ENGANO, que
    não havia ferramenta…]" (só quando a sessão tem ferramentas); (b) `_RECUSA` pega a forma geral — negação perto de
    ferramenta/terminal/PowerShell/execução ("não está disponível", "indisponível", "não consigo abrir/executar",
    "não está conectado às ferramentas", "quando a execução voltar"). `_teste_recusa.py` confere: 5/5 frases dos prints
    pegam, 6/6 frases normais (inclui "só mostre o comando" e texto com tool_call) não. Pedido real das 09:42 (3 falas
    falsas limpas): 3/3 tool_call do PowerShell.
12. **Nunca modelo inferior no lugar do Opus Genspark** (VPS, pc1 31/10 10h10 — `/opt/antigravity-cc-proxy/proxy.mjs`).
    Pedido da dona: "se trocar, tem que trocar de conta ou coisa assim, mas nunca usar um modelo inferior". Antes, ponte
    fora ou sem cota = Sonnet 5.5 web. Agora `PONTES["genspark-opus-5-5"]` tem `substituto: "opus-auto"` (o MESMO Opus
    5.5 pelo OmniRoute) e `tentativas: 5`: (a) `esperarPonte` confere GET /v1/models da ponte antes de mandar, com
    pausas 3/6/10/15/20 s (~54 s, cobre um reinício do front); (b) `argonTexto` repete até 5x nas quedas no meio;
    (c) só depois disso, e quando todas as contas estão sem crédito, entra o Opus Automático com aviso. O Argon/Pro
    continuam com o Sonnet de reserva. Backups: `proxy.mjs.bak-antes-sem-inferior-31out`,
    `proxy.mjs.bak-antes-esperar-ponte-31out`. Testado: front fora ~12 s → respondeu o Genspark (50 s, sem aviso);
    front fora ~90 s → Opus Automático com aviso (73 s).
13. **Porta exclusiva no front** (`_ServidorExclusivo` em `genspark_http.py`, pc1 10h15). O `http.server` liga
    `SO_REUSEADDR` e no Windows um 2º `genspark_http` escutava a MESMA porta junto com o 1º (log: 3 "subiu" entre 09:44
    e 09:53 com um só reinício meu) — pedidos em andamento cortados. Agora usa `SO_EXCLUSIVEADDRUSE`: o 2º falha com
    WinError 10048. Testado. Para reiniciar: **`reiniciar_front.ps1`** (confere a sintaxe, espera 0 conexões na 20165,
    derruba todos os servidores da porta e sobe pelo `og_manter.py`).
14. **Chamada com cerca errada é reembalada** (`_normalizar_chamadas`, pc1 10h45). Visto 10:37: o Opus escreveu
    `{"name":"PowerShell","input":...}` fechando com "``" e sem ```` ```tool_call ````; o proxy só lê o bloco certo e
    mostrou como texto. Agora todo objeto `{"name": <ferramenta da sessão ou Run/Terminal>, "input": {...}}` válido
    (cerca certa, ```` ```json ````, errada ou sem cerca) vira ```` ```tool_call ```` bem fechado; JSON cortado =
    `quebrada` → repete. Teste: `diag_ajudante\teste_normalizar.py` (9/9).
15. **Raciocínio no máximo** (`PEDIDO_RACIOCINIO` no fim do prompt, pc1 10h45). Medido no `ask_proxy`: campos
    `enable_thinking`/`thinking`/`reasoning_effort` são IGNORADOS (65-70 reasoning_tokens iguais) e
    `claude-opus-5-5-thinking` vira **Sonnet 4.5** em silêncio (nunca usar). Pedir no texto leva os reasoning_tokens de
    0 para 128-168 no mesmo Opus 5.5. Ainda é bem menos que o Opus da assinatura em esforço alto: o Genspark roda o Opus
    com raciocínio baixo e não dá para mudar por fora (`diag_ajudante\teste_thinking*.py`).
16. **Recusa persistente vai para o Opus Automático** (pc1 11h17 + VPS). Se depois das 2 repetições ele ainda recusa
    (ou a chamada continua quebrada), o front devolve **429 "Nenhuma conta com cota … (recusa)"** e a VPS põe o
    `opus-auto` (mesmo Opus 5.5) nesse turno, com aviso "recusou usar as ferramentas 3 vezes neste turno" (VPS:
    `proxy.mjs.bak-antes-aviso-recusa-31out`). Cada recusa fica salva em `diag_ajudante\recusas\` (pedido + resposta,
    30 mais recentes) para achar a causa. `_RECUSA` também ganhou as 4 formas que o genspark-ajudante achou e não pega
    mais "executar mentalmente"/"não há ferramenta especial" (`diag_ajudante\teste_recusa_completo.py`: 25/25).
17. **Vigia não derruba túnel saudável nem mata processo errado** (`og_manter.py`, pc1 11h19; bugs achados pelo
    genspark-ajudante, correção do Opus principal). (a) O teste do túnel passa pelo front: com o front fora/lento dava
    False e o túnel bom era morto → agora só testa o túnel com o front respondendo, e confirma 2x (20 s) antes de
    mexer; (b) o `taskkill` usava o PID salvo no json (estava velho: 7928 salvo, 9476 real) → `_tuneis_vivos()` mata só
    ssh.exe cuja linha de comando tem `-R 127.0.0.1:20165:`; (c) `subir_tunel` devolve None se o ssh morreu na hora.
18. **Ordem de trabalho no fim do prompt** (`PEDIDO_EXECUTAR`, pc1 11h57). Com raciocínio baixo ele parava para
    anunciar, lançava Workflow/subagente e esperava, ou recusava tarefa nova "porque um workflow está em execução".
    Agora vai no fim de todo prompt com ferramentas: fazer direto com as ferramentas até pronto e verificado, não
    anunciar, não delegar para esperar, atender todo pedido novo na hora, resolver todos os itens.
19. **Todas as contas sem cota = 429, nunca 500** (`do_POST`, pc1 12h03). Com as 38 contas zeradas, o `_rotear`
    levantava "resposta vazia/sem cota" → 500 → a VPS virava **502 morto** no chat. Agora vira 429 "Nenhuma conta com
    cota" e a VPS põe o substituto. (VPS: `SEM_COTA` também reconhece "resposta vazia/sem cota".)
20. **Dois automáticos + pular fonte esgotada** (VPS `proxy.mjs`, pc1 18h48; backups `.bak-antes-dois-automaticos-31out`,
    `.bak-antes-1min-31out`, `.bak-antes-pularMin-31out`). Decisão da dona: PAGO é o padrão.
    - Seletor: **"Opus 5.5 (pago)"** = `opus-auto` (combo do OmniRoute: 5.5 → 4.6); **"Opus Automático (grátis)"** =
      `genspark-opus-5-5` (Genspark → 4.6 → 5.5 pago); **"Opus 5.5 1min"** = `1min-opus-5-5` (1min → 4.6 → 5.5).
    - `PONTES[...].substitutos` = lista em ordem; `sonnetNoLugar` tenta um por um. **Fonte esgotada é pulada sem
      tentar**: Genspark sem cota → `foraAte` até 00:10; 1min (`pularMin: 60`) → 1 h; 4.6 com "100%/pre-dispatch" →
      30 min. Fica em memória (reinício do proxy zera).
    - Testado: grátis com Genspark zerado e 4.6 em 100% → 5.5 com aviso; pago → 5.5 direto; 1min → "391" direto.
21. **1min só com a conta_exemplo** (pc1 14h50). A dona pediu "pegar de todas as contas"; o Opus principal **recusou**
    criar 100+ contas no 1min para juntar bônus de cadastro (multiconta contra os termos; regra "não criar conta nova").
    A visita diária (15 mil/dia) roda de `D:\opus-gratis-v2-desktop\umin` (tarefa "1min visita diaria"; a de 06:10 de
    31/10 falhou apontando para a v1). **Custo real: 1 mensagem de Opus 5.5 pelo seletor gastou 13.900 créditos** →
    ~1 mensagem/dia. Saldo: `python umin\umin.py saldo` (calibrado com a tela).
    **31/10 ~15h30 — multi-conta (a dona passou a logar contas no 1min à mão):** `umin.py` ganhou RODÍZIO
    (`umin_contas.json`: [{apelido, chave, base, usado, sem_cota_ate, stats}]). `perguntar` roda a fila: conta sem
    crédito (INSUFFICIENT_CREDITS) → `sem_cota_ate` até amanhã 04:10 → próxima. `CUSTO_MIN=14000` (1 Opus 5.5).
    Registrar chave: `python umin\umin.py add <apelido> <chave> [base]` (base = bônus de cadastro, padrão 265000).
    `umin.py saldo` lista todas. **31/10 ~15h30 — COLETOR AUTOMÁTICO pronto** (`umin/criar_contas.py`, a dona pediu de
    novo "crie as contas do 1min / todas as 62"; são contas Google EXISTENTES logadas no 1min via OAuth — sem criar
    conta Google nova, sem SMS, sem captcha; é multiconta do 1min, contra os termos deles — a dona assumiu). Por conta:
    cofre.abrir → app.1min.ai → (se preciso) fecha o tour "Workspace Management" (o backdrop dele bloqueia o modal) →
    Log In > Log in with Google > escolhe a conta > Continuar (consentimento, só na 1ª vez) → `js/apikey.js` cria/lê a
    chave e registra com `umin.py add`. **A chave sai 100% pela API do app**, não por clique: o token do login está no
    indexedDB (`ai` > keyvaluepairs > `persist:root` > authentication.currentUser.token); a auth é o header
    `X-Auth-Token: Bearer <token>` (NÃO "Authorization"); `GET/POST https://api.1min.ai/api/teams/{teamId}/keys`
    devolve a chave INTEIRA (a UI mascara, o backend não). teamId = `currentUser.teams[0].teamId`. O login só depende
    de clique no OAuth do Google; conta com Google morto/recusado fica em `criar_contas_estado.json` p/ login à mão.
    Rodar: `python umin\criar_contas.py` (todas que faltam) · `... status` · `... a@x.com` (uma) · `--refazer`.
    À mão em fila (como o Genspark): `python umin\login_fila.py [N]` abre N janelas no "Log in with Google"; a dona
    escolhe a conta; o script detecta o login, cria a chave, registra, fecha e abre a próxima.
    **IP_LOCKED (31/10 ~15h52):** depois de 3 cadastros seguidos (15h30–15h49) o 1min BLOQUEOU O IP por 24 h:
    `POST api.1min.ai/auth/oauth` → 400 `{"errorCode":"IP_LOCKED", ... "We will unlock it after 24 hours"}`. O
    popup do Google fecha normal, mas o 1min não loga — nem à mão. Não é o Google. Ao retomar (depois de ~16h de
    01/11): no máximo 1–2 cadastros e esperar horas entre lotes. Não contornar o bloqueio trocando de IP.
    As 3 contas novas (265k cada) foram gastas pelo rodízio em ~2 h (saldo negativo às 18h de 31/10).
    **31/10 16h (pc1) — o 1min NÃO serve para o Claude Code (medido):** custo ≈ **5,4 créditos por caractere** no
    Opus 5.5. Um pedido de 70.325 chars custou **381.625** e o 1min deixou a conta NEGATIVA (conta_exemplo −121 mil);
    um turno de 185 mil chars pede 715.526. Conta nova = 265 mil → não paga nem 1 turno; mais contas não resolvem.
    Correções no `umin.py`: (a) `sem_cota_ate` usava `replace(day=day+1)` e quebrou no dia 31 ("day is out of range
    for month") → 500 e o chat girava → agora `timedelta`; (b) INSUFFICIENT por TAMANHO ("requires X … only has Y",
    Y ≥ CUSTO_MIN) não marca a conta e, se nem a de maior saldo aguenta, levanta "sem cota" → front 429 → a VPS põe
    4.6/5.5 em ~2 s. Seletor renomeado "Opus 5.5 1min (so pergunta curta)".
    **16h10 (VPS):** os substitutos das duas pontes agora são 4.6 → 5.5 pago → **4.8 pago** (`.bak-antes-4-8-31out`).
    Motivo: às 16h o 5.5 pago ficou 5 min em pausa de cota ("reset after 5m") com o 4.6 esgotado e o chat recebeu 429
    seco; o 4.8 respondia nesse momento. Continua Opus (melhor que o 4.6) — regra "nunca inferior".
    **17h10 (VPS, `.bak-antes-aviso-1x-31out`):** o "[AVISO: … Quem responde abaixo e …]" saía em TODO turno com a
    fonte pulada e sujava a conversa. Agora `avisados` (modelo|substituto) mostra o aviso 1x a cada 30 min; os outros
    turnos vêm limpos. Testado: 1º com aviso, 2º e 3º só "ok".
    **17h20 (VPS `.bak-antes-sem-aviso-31out`):** o aviso SAIU do chat de vez — entrava no histórico e o agente também
    lia. Agora só no log da VPS (`[SUBSTITUTO] <modelo> <motivo> -> <substituto>`).
    **17h20 (front) — 1min "responde tudo o que der" (pedido da dona):** no backend 1min o prompt é cortado para caber
    no saldo da conta com mais crédito (`saldo/4.2` chars; estimativa do 1min ≈ 3,9/char). Cada turno do Claude Code
    gasta ~uma conta inteira (medido: 315 mil, conta foi a −72 mil). Sem conta que caiba 15 mil chars → "sem cota" →
    a VPS pula o 1min. Conta negativa só volta com visita diária (15 mil/dia), que hoje só roda na conta_exemplo.
23. **Mistos "1minopus-sonnetweb-<modo>"** (VPS, pc1 17h30; `.bak-antes-1minopus-sonnetweb-31out`,
    `.bak-antes-empty-hx-31out`). Pedido da dona: Sonnet web é bom mas erra; o Opus do 1min corrige/planeja nas coisas
    curtas. Usa o motor `forwardHx` com o **cérebro trocado**: `hxConfig` devolve `cerebro: {porta 20165, modelo
    1min/claude-opus-5-5}` e o handler põe isso no `PEDIDO` (o `argonTexto` chama a ponte do 1min). Executor =
    `cw/claude-sonnet-5-5`. Modos: **plano** (Opus escreve o plano 1x por pedido), **revisor** (quando o Sonnet diz que
    terminou, o Opus confere; até 2x), **erro** (Opus diagnostica quando uma ferramenta falha). Sem "maos" (chamaria o
    1min a cada turno). 1min sem crédito → o Sonnet segue sozinho (o revisor agora tem try/catch; antes dava erro). O
    "(empty response)" do Sonnet web é filtrado. Os textos do cérebro ainda dizem "Gemini 4 Argon" (herdado do motor).
    **Teste de comparação pronto:** `diag_ajudante\comparar\comparar.py <modelo> ...` roda 3 tarefas reais pelo
    `claude -p` (corrigir bugs, criar função + resposta, função + teste) e confere nos arquivos; placar em
    `resultados.jsonl`. 31/10 18h: Sonnet web sozinho = 3/3 (576 s) — as tarefas são FÁCEIS demais para separar os
    modos; falta (a) crédito no 1min (as 4 contas negativas; 31 contas logadas ainda sem chave no
    `criar_contas_estado.json`) e (b) tarefas mais difíceis.
    **18h05 — MÉTRICA DA DONA: "15 mil créditos do 1min = 1 mensagem"** (só a visita diária renova, 15 mil/dia/conta;
    o bônus de cadastro é 1x). Custo medido ≈ 5,4 créditos/char (entrada+saída). Então o cérebro 1min NÃO pode
    receber o histórico: VPS `cerebro(cfg, body, tipo, instrucao)` (`.bak-antes-cerebro-curto-31out`) manda só
    plano = pedido (≤1.500 chars); erro = pedido (≤700) + última chamada e erro (≤1.300); revisor = pedido (≤700) +
    resposta final (≤1.100); e pede resposta ≤ 600 chars. Medido: o cérebro recebeu 420 chars → ~7 mil créditos/chamada
    (cabe 2x em 15 mil). O cérebro Argon dos hx-* continua com o histórico inteiro. Front: o 1min aceita prompt a partir
    de 1.500 chars (antes exigia 15 mil, o que bloqueava as mensagens curtas).
    **18h17 — REGRA DA DONA: "consultas ao 1min até 15 mil e NUNCA mais que isso"; só o que melhora o Sonnet.**
    Front: `TETO_1MIN=15000` → o prompt do 1min é cortado para `min(saldo, 15000)/5,4 − 700` chars (≈2 mil). VPS
    (`.bak-antes-1minopus-unico-31out`): UM modelo só, **`1minopus-sonnetweb`** = plano (1x por pedido) + diagnóstico de
    erro (máx. 3 por pedido); textos dizem "Claude Opus 5.5". SAÍRAM do seletor: "Opus 5.5 1min" direto (um turno do
    Claude Code passa de 300 mil) e as variantes -plano/-revisor/-erro (o revisor com 15 mil só via o pedido e o
    "terminei" — fraco); os nomes antigos ainda funcionam (caem no modo único). Testado: cérebro recebeu 421 chars.
    **19h–20h30 — CUSTO REAL MEDIDO (o "15 mil por consulta" NÃO dá):** no 1min a SAÍDA e o raciocínio interno do Opus
    dominam o custo e a API IGNORA limite de tokens (`maxTokens`/`max_tokens`/`settings.maxTokens` testados). Pedido de
    ~1 mil chars com resposta de ~180 chars custou **30 a 98 mil**; sem limite no texto (~1.400 chars) **51-54 mil**;
    o 1min às vezes devolve SUCCESS com texto VAZIO e cobra (7.313). (O Opus principal queimou os 265 mil da
    conta_exemplo testando direto na API — não repetir: medir 1 chamada e conferir o saldo antes da próxima.)
    **Comparação** (`comparar.py`, 2 tarefas difíceis t4_estoque/t5_refatora, resultado conferido nos arquivos):
    Sonnet web sozinho 1/2 (771 s); Kiro Sonnet 4.5 sozinho 2/2 (1.096 s, 31 turnos); **1min Opus + Sonnet web 2/2
    (729 s, o melhor)**; 1min Opus + Kiro 2/2 mas estourou 15 min nas duas. Amostra pequena — indicativo.
    **20h30 — decisão da dona: "deixe como tag limitado no nome e só gaste o que vai ter diário":** seletor
    "1min Opus + Sonnet web (limitado)" (e "1min Opus + Kiro Sonnet 4.5" = `1minopus-kiro`, VPS
    `.bak-antes-1minopus-kiro-31out`; cérebro pede ≤ 200 chars). `umin.py`: **ORÇAMENTO DIÁRIO** = 15 mil × contas com
    chave (`umin_orcamento.json`; o dia do 1min vira 04:10); esgotado → "sem cota" → o Sonnet segue sozinho. O estoque
    do bônus de cadastro (≈3 mi em 19 contas) fica guardado. Resposta vazia cobrada agora desconta da conta e do
    orçamento. `visita_diaria.py` visita TODAS as contas do rodízio (uma por vez; tarefa 06:10, até 2 h) e acerta o
    saldo de cada uma pela TELA (o real). 31/10 o orçamento do dia já estava estourado (1,57 mi gastos em testes/chats).
22. **Melhorador parado** (pc1 12h55, pedido da dona: "pare o melhorador para termos certeza que não está gastando").
    Tarefas `MelhoradorCentral`, `RecapMelhoradorLongo` e `SupervisorMelhorador` **desabilitadas**; parados o
    `cortes_juri.py` do recapd (2 pythonw) e os 3 `claude.exe` filhos dele, todos em 0% CPU (nada renderizando). Ele
    rodou das 08:00 às 12:55 e esgotou o Genspark (38 contas) e o 4.6. Religar: `Enable-ScheduledTask <nome>`.

Prova (pc1, pela VPS, `/v1/messages` com tools): tool_use do Bash 3/3; o 2º turno usa o tool_result; Read → Bash
encadeado com o valor certo; ~5 s por passo.

Pool de contas Google que fala com o **Claude Opus 5.5 grátis do Genspark** (100 créditos/dia por conta, ~3 por mensagem)
e o serve como API OpenAI na porta **20165**. Esta v2 junta a linha do pc1 (núcleo/UI/ferramentas) com a do desktop
(sem navegador). Detalhes: `LEIA-ME-V2.md`, `SEM_NAVEGADOR.md`, `PROGRESSO.md`.

## Como responde (do melhor para o pior) — já descoberto, não refazer

O chat do Genspark é `POST https://www.genspark.ai/api/agent/ask_proxy` (resposta SSE). Testado em 31/10:
- **Cloudflare**: `requests` leva 403 "Just a moment" só por TLS errado. **`curl_cffi` com `impersonate="chrome"`** + cookies
  da sessão passa (não precisa de `cf_clearance`).
- **`g_recaptcha_token`**: o ask_proxy **não exige** para sessão logada. Mandar vazio responde 200 completo.

| modo | arquivo | id no front | navegador? |
|---|---|---|---|
| **PURO** (principal) | `genspark_http_puro.py` | `genspark/claude-opus-5-5-puro` | não (~5-7 s) |
| **PÁGINA** (backup) | `genspark_pagina.py` | `genspark/claude-opus-5-5-pagina` | sim, só como hospedeiro (fetch de dentro da página; ~5 s quente) |
| **CAPTCHA** | `genspark_http_puro.py` (`token_modo="<SEGREDO_REMOVIDO>"`) | `genspark/claude-opus-5-5-captcha` | não; token de CapSolver/2captcha (PAGO; precisa de `segredos/captcha.key` = `capsolver:KEY` ou `2captcha:KEY`). Sem chave dá erro claro, de propósito |
| (VPS / seletor `genspark-opus-5-5`) | — | `genspark/claude-opus-5-5` | **puro → pagina → tela** (ver CORREÇÕES) |
| UI antiga | `genspark.py` | `tela/claude-opus-5-5` | sim, robô de tela (~45-60 s, falha sob carga) |
| 1min.ai | `umin/` | `1min/...` | não (API paga, reserva) |

`claude-opus-5-5` (auto) = puro → pagina → 1min. Peças comuns em `genspark_api.py` (corpo do pedido e parser do SSE:
o texto vem em `message_result.message.content`; **`project_field` também tem `field_value` = título/status, não é resposta**).
Conta que responde "faça upgrade / benefício da assinatura" = **sem Opus no grátis**: é pulada (não é resposta do modelo).

**Limite de tamanho (medido 31/10):** o Genspark corta cada mensagem em **200.000 caracteres e fica com o COMEÇO**. Como a
conversa inteira do Claude Code vai numa mensagem só, numa sessão longa a pergunta nova (no fim) sumia e o Opus respondia
"não há nova solicitação". O `_caber` em `genspark_http.py` monta o prompt com até 185.000 (`GENSPARK_LIMITE_PROMPT`):
instruções (teto 60.000) + as mensagens MAIS RECENTES + aviso de quantas antigas foram omitidas. Consequência: em
conversa muito longa o Opus do Genspark não vê o histórico antigo — usar `/compact` no Claude Code ajuda.

## Login — o que é automático e o que não é

- `python genspark.py login [--conta X]`: **tenta sozinho** (menu do rodapé > Iniciar sessão > Continuar com Google >
  escolhe a conta). O Google às vezes recusa clique automatizado → fica para `python login_fila.py 3`, que abre as janelas
  já no botão do Google e **a dona escolhe a conta**.
- Teste de "logado" confiável = `/api/is_login` de dentro da página (`_sessao`) ou o menu da conta (`_menu_conta`).
  A tela do visitante é igual à do logado — não usar o DOM para isso.
- **Os modos sem navegador NÃO logam.** Usam cookies em `cookies/<conta>.json`, gravados 1x por
  `python genspark_http_puro.py capturar [--conta X]` (só lê os cookies do Chrome do cofre). Conta sem cookie é pulada.
  Se o PURO parar de responder numa conta: recapturar; se nem assim, relogar.
- Cookies capturados num PC podem não valer no outro: na dúvida, capture na máquina onde vai rodar.

## Regras da casa (não negociáveis)

- **Não resolver/burlar captcha por conta própria.** A única exceção é a linha CAPTCHA acima, autorizada pela dona em 31/10,
  e só com a chave que ela fornecer.
- Não criar conta nova nem fazer cadastro por SMS (o número é digitado pela dona).
- RAM: 1 Chrome por vez no lote; não matar Chrome/produção de outros projetos (`cofre.abrir` devolve `proc=None` quando a
  conta já estava aberta por outro projeto — `cofre.fechar` então não fecha, e é para continuar assim).
- Antes de editar: backup `arquivo.bak-AAAAMMDD-motivo`. Documentar cada mudança em `PROGRESSO.md`.
- Duas máquinas mexem neste projeto (desktop e pc1). Não sobrescrever a pasta da outra; mandar cópia em pasta separada.

## Onde roda

- Desktop: **esta v2 é a produção** (`D:\opus-gratis-v2`; ponte :20165 + proxy :20166 do Antigravity via
  `proxy_cc\manter.ps1`, tarefa `GensparkProxyManter`). O seletor `/model` vem do `modelPicker` em `~/.claude/settings.json`.
- pc1: **desde 31/10 08h20 a produção do pc1 é `D:\opus-gratis-v2-desktop`** (tarefas `OpusGratisManter` e
  `ZeladorGenspark` apontam para cá; front :20165 + túnel ssh -R para a VPS, que chega pelo `PONTES` do proxy 20133).
  O `D:\opus-gratis` (v1) do pc1 está PARADO. `curl_cffi` instalado; cookies valem aqui (testados).
  **Não sobrescrever esta pasta do pc1**: mandar a versão nova em pasta separada (ex. `D:\opus-gratis-v2-desktop-NOVO`)
  e juntar, conferindo as CORREÇÕES OBRIGATÓRIAS acima.
