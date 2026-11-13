# Comparação de modelos (Argon e companhia) — documento COMUM de todos os chats

Pedido da dona (27/10): cada chat que testar um modelo escreve AQUI a sua análise, para comparar os modelos lado a
lado em código, vídeo, texto etc. e decidir quem fica em cada tarefa.

Este é o documento ÚNICO. A pasta `analises\` guarda só o detalhe de cada linha (`<data>_<LINHA>.md`) e os dados
brutos (`analises\dados\`).

## Como escrever (todos os chats)
1. Arquivo compartilhado: **Read + Edit para acrescentar**. Nunca Write (apaga o que os outros puseram).
2. Sua análise vai em **Análises** com o título `### dd/mm hh:mm — LINHA/chat — o que foi testado`, a mais nova em cima.
3. Na análise: a tarefa, os modelos, como você deu a nota (de 0 a 10, às cegas se der), a tabela modelo / nota /
   tempo / falhou?, e o que foi conferido de verdade (teste, render, nota de júri). Suposição escrita como suposição.
4. Depois **atualize a linha do modelo no Resumo** (só a coluna da sua tarefa) com a nota e o link da análise.
5. Modelo sem crédito ou fora do ar: anote em **Disponibilidade** com data e hora.

## Modelos (nomes no seletor e no proxy 157…:20133)
| Nome | O que é |
|---|---|
| `gemini-4-argon` (Argon puro) | Argon direto, HTTP puro; ferramentas por protocolo de texto |
| `argon-pro` (Argon Pro) | Aponta para a melhor dupla do teste (`/opt/antigravity-cc-proxy/argon_pro.txt`); desde 27/10 ~18h = `hx-maos-gemini` (Argon decide, Gemini 3.8 executa) |
| `argon-kiro` | Argon pensa; Kiro Sonnet 4.5 executa a ferramenta quando o Argon não chama |
| `argon-gemini` | Argon pensa; Gemini 3.8 Flash executa a ferramenta quando o Argon não chama |
| `argon-opus` | Argon pensa; Opus 4.6 (Antigravity) executa a ferramenta quando o Argon não chama |
| `argon-flash` (Flash + Argon) | Gemini 3.8 Flash trabalha com ferramentas e manda o difícil para o Argon (ask_argon) |
| `cw/claude-sonnet-5-5` (Sonnet web, 29/10) | Sonnet 5.5 das 48 contas claude.ai grátis, provedor claude-web do OmniRoute; ferramentas emuladas pelo OmniRoute (obedeceu no teste); pergunta curta 1–7 s; comparação com o Argon em `D:\sonnet web\COMPARACAO_ARGON_x_CLAUDEWEB.md` (sem nota de tarefa ainda) |
| `agy/gemini-3.8-flash-high` | Gemini 3.8 Flash high, referência atual de várias linhas |
| `gweb/gemini-4-argon` | o mesmo Argon pela rota gweb/ do proxy |
| `gweb/gemini-3.1-pro` | Gemini 3.1 Pro web (rota gweb/) |

## Resumo (nota 0–10; "—" = não testado; ✗ = travou/falhou)
| Modelo | Código (testes passando) | Melhorador: análise e proposta | Roteiro de anúncio | Roteiro de entretenimento | Texto criativo longo (passagens/narrador) | Edição de vídeo (Remotion) | Precisa do Kiro? |
|---|---|---|---|---|---|---|---|
| Argon puro | ver HIBRIDOS_PROGRESSO.md · caixa 9 [2] · **10** (no prompt) / 2 (ferramentas) [3] | 6,5 [1] · **9,5** [2] · 7,0* [4] | 6,5 [1] · 6,0 [2] | ✗ [1] · **8,0** (título 5,0) [4] | **9,0** [3] | — | não |
| Argon Pro | ver HIBRIDOS_PROGRESSO.md · caixa 2 [3] | 7,5 [1] · 5,5* [4] | 8,0 [1] | ✗ [1] · **8,0** (título 5,0) [4] | 8,5 [3] | — | **sim** (hoje) |
| Argon + Kiro | ver HIBRIDOS_PROGRESSO.md · caixa: **resposta falsa** [2] · 0 [3] | 6,5 [1] · 4,0 [2] · 4,5* [4] | 7,5 [1] · 7,0 [2] | ✗ [1] · 7,5 (título 7,0) [4] | 8,5 [3] | — | **sim** |
| Argon + Gemini 3.8 | ver HIBRIDOS_PROGRESSO.md · caixa **10** [2] · 10 (18 min) [3] | 7,5 [1] · 5,5 [2] · ✗ [4] | 7,0 [1] · 7,5 [2] | ✗ [1] · 6,0 (título 4,0) [4] | 7,5 [3] | — | não |
| Argon + Opus 4.6 | ver HIBRIDOS_PROGRESSO.md · caixa 9 [2] · 10 [3] | 5,5 [1] · 7,0 [2] · 5,0* [4] | ✗ [1] · 6,0 [2] | ✗ [1] · **8,0** (título 5,5) [4] | 7,5 [3] | — | não |
| Flash + Argon | caixa 9 [2] · **10** [3] | 6,0 [1] · 8,0 [2] · 6,5 [4] | ✗ [1] · 6,5 [2] (sem ferramentas = só o Flash) | ✗ [1] · 6,5 (título **7,5**) [4] | 8,0 [3] (revisor 4/4) | — | não |
| Gemini 3.8 Flash high | caixa 8 [2] · **10** [3] | ~7,5 [1] · 5,0 [2] · 6,5 [4] | ✗ [1] · 7,0 [2] (24 s) | 7,0 (título **7,5**, 8 s) [4] | 7,0 [3] | 1ª versão 5,6–6,5 em 6 vídeos [1] | não |
| gweb/gemini-4-argon | caixa 8 [2] | 8,0 [2] | 7,5 [2] | — | — | — | não |
| gweb/gemini-3.1-pro | caixa 1 [2] | 6,5 [2] | 5,5 [2] | — | — | — | não |

[1] = análise de 27/10 do CLAUDE-CODE-VIDEO, abaixo. [2] = análise de 27/10 da linha PRODUTOS, abaixo. [3] = análise
de 27/10 da linha LONGOS, abaixo. [4] = análise de 27/10 da linha CORTES (Shorts), abaixo; * = rodou antes da
conferência do Argon servido (10:10), pode ter sido Flash-Lite.

## Disponibilidade
- **28/10 ~14h (chat do OmniRoute):** sondagem "6+7" pelo :20133. Respondem: `gemini-4-argon` (119 s),
  `gweb/gemini-4-argon` (73 s), `gweb/gemini-3.1-pro` (168 s), `argon-pro` (137 s; 3 Argon em paralelo, tempos
  inflados). NÃO respondem: `gemini/gemini-4-argon`, `gemini/gemini-3.1-pro-preview`, `gemini/gemini-pro-latest` (429
  "all credentials cooling down" = chaves de API sem Pro), `dva/gemini-3-1-pro-high` (500), `agy/gemini-pro-agent` (fora
  do catálogo), `agy/gemini-3.8-flash-medium` e `gemini/gemini-3.8-flash` (sem resposta em 240 s). A conta agy (Pro)
  está travada ("familyLocked") desde 27/10 23:26: todo Gemini 3.8 sai pelas 8 contas `antigravity/...-tiered`.
- **28/10 — `hx-maos-*` agora tem fallback:** se o Argon falha (sem cota/fora), o reserva faz o passo sozinho (antes
  o pedido dava erro). Backup `proxy.mjs.bak-maos-fallback-20261028`. O subagente `argon-ajudante` usa `argon-pro`:
  o vencedor dos testes vai para `/opt/antigravity-cc-proxy/argon_pro.txt` (troca sem reiniciar) e o ajudante segue junto.
- **27/10 ~15:50 — Argon agora com raciocínio ALTO de verdade** (gemini-argo). Antes disso o gemini_http só escolhia o
  Argon e ele rodava no nível PADRÃO da conta (mais raso); agora toda chamada manda o nível Alto (f.req[68]=2 /
  jspb[11]=2). Medido: ~2,4x mais tempo por resposta (10 s -> 25 s) e mais raciocínio. Notas do Argon antes das 15:50 =
  nível padrão; vale refazer o que for decidir algo. Contas no rodízio: 29 Pro.
- 27/10 14:54–15:10 (PRODUTOS): `antigravity/claude-opus-4-6-thinking` = 403 "Your current account is not eligible for
  Gemini Code Assist for individuals… must be 18 years old" (conta do Antigravity no OmniRoute recusada pelo Google).
  O teste "Opus 4.6 sozinho x Argon + Opus" foi CANCELADO: dona 27/10 15:40 "não use Opus nem Kiro por agora, só o
  Argon (se tiver) e o Gemini".
- 27/10 até ~10:10: o "Argon" podia responder com **Flash-Lite em silêncio** (conta sem cota); a conferência do modelo
  servido entrou no gemini_http.py às 10:10 (argon.log: "servido 3.5 Flash Lite (limite atingido) — próxima conta").
- 27/10 ~10:16 (CORTES): `argon-gemini` → "Todas as contas estão bloqueadas" depois de 7 modelos em paralelo — rodar
  o Argon 1 por vez.
- 27/10 ~09:40: `gemini-4-argon` deu 429 "All credentials … cooling down"; voltou ~10:20.
- 27/10 ~10:45: **Kiro acabou** → `argon-kiro` e `argon-pro` (hoje `hx-socorro-kiro`) fora até o Kiro voltar.
  Nesse horário as chamadas a `argon-opus`, `argon-flash` e `agy/gemini-3.8-flash-high` passaram de 15 min sem
  resposta (motivo não confirmado).
- 27/10 ~10:40–10:55 (PRODUTOS): `gweb/gemini-3.1-pro` deu timeout + "Remote end closed" + 502 Bad Gateway x2 no
  roteiro do Disparo; `gemini-4-argon` e `argon-opus` estouraram 600 s uma vez cada nesse horário.

## Análises (mais nova em cima)

### 03/11 17:15 — PESQUISADOR DE MELHORIAS — Busca GitHub (`area_voz_rapida`: Argon vs Claude Sonnet vs Gemini Pro vs Opus)
Mesmo pedido (`rodadas\2026-11-03_1205\pedidos\area_voz_rapida.md`, com 69 repositórios em `ja_conhecidos.txt` proibidos de repetir) enviado em paralelo para `argon-pesquisa`, `sonnet-ajudante`, `gemini-pro-pesquisa` e `opus-ajudante`. Conferido na API do GitHub (`pesquisador.py comparar` -> `placar.json` e `JUNTO.md`):

**CORRIGIDO 04/11 02:50 (Opus).** A 1ª versão desta tabela (escrita pelo Argon) estava ERRADA: os arquivos de resposta
eram resumos reescritos pelo Argon, a conta de "inéditos" e "repetiu proibidos" era falsa (GPT-SoVITS/F5/Applio não
estavam no ja_conhecidos) e o import dizia +21 repos quando gravou 0. Refeito com as respostas BRUTAS e o Opus 5.5 (chat) fazendo a mesma pesquisa:

| Agente | Tempo | Repos | Existem (API) | Só ele achou | Erros graves | Nota |
|---|---|---|---|---|---|---|
| **sonnet-ajudante (Sonnet 5.5)** | 451 s | 27 | 26 | 9 | nenhum; foi o ÚNICO que pegou a licença NÃO-COMERCIAL dos pesos do F5-TTS e disse que não há RTF medido em T4 | **9,5** |
| **opus-auto (Opus 5.5, chat)** | ~15 min | 18 | 18 | **10** | nenhum 404; só ele trouxe MeanVC (troca do RVC zero-shot), FireRedTTS3 (pt/es + velocidade/tom por instrução), alexandria-audiobook (roteiro anotado por fala), woys (RVC ONNX CUDA Linux) | **9,0** (caro: gasta a cota do Opus) |
| **argon-pesquisa (Argon)** | 454 s | 17 | 17 | 5 | chamou F5-TTS de "MIT 100% comercial" (falso) e errou estrelas do Qwen3-TTS; bom em detalhe prático (cache de voz do Qwen3, SDPA na T4) | **7,5** |
| **gemini-pro-pesquisa (3.1 Pro)** | ~216 s | 16 | 16 | 5 | arquivo dele não é bruto confirmado | **7,0** |
| **opus-ajudante (Opus 4.6)** | 529 s | 15 | 15 | 6 | F5 "comercial" (falso); metade velho (coqui 2024, piper) | **6,5** |

Na rodada do Argon (resumo antigo) havia 4 repos INEXISTENTES (404): luoyily/RVC-ONNX-Infer, OpenBMB/nanovllm-voxcpm,
Seatop/nanovllm-voxcpm, ConfigureNode/RVC-C. **Conclusão:** o Argon NÃO é o melhor pesquisador; é o mais barato.
Para o motor contínuo: Argon busca em volume + Sonnet revisa licença/fatos de cada lote (ele erra pouco) + verificador da API derruba 404.
Opus 5.5 só em rodada especial (mais achados exclusivos, mas gasta a cota principal).

### 29/10 17:45–18:40 — CORTES — MELHORADOR NO CENÁRIO REAL (mesmo lote, aplica → confere → desfaz)
Pedido da dona: "teste qual a melhor versão pra atuar no cenário real... você mesmo faz e vê qual teria melhor nota;
o Gemini puro é só referência". Lote REAL do melhorador dos Cortes (júri de 4 Shorts: 16de72, d9bb92, 6dd484, b0c0f3),
mesmo pedido (`cortes_melhorador._prompt`) para cada modelo, 1 por vez, Claude Code CLI com Read (abre júri/quadros).
Gabarito da sessão (Opus 5.5) gravado ANTES de ler as respostas: `D:\tmp\bancada_real\gabarito_opus55.json`;
respostas em `D:\tmp\bancada_real\fase1\`. Cada achado foi conferido no quadro e no log do Short.

| Modelo | Tempo | Nota | Por quê |
|---|---|---|---|
| **argon-pro** (Argon decide, Gemini executa) | 265 s | **8,5** | legenda baixa com arquivo certo (fx_subtitles); o ÚNICO que abriu júri/quadro por conta própria e achou um defeito que não estava no pedido ("cai no rio e desviver todos", d9bb92 q11). Mas propôs regra de roteiro, que não conserta: o "desviver" vem do `viralizador.anti_ban`, DEPOIS do roteiro |
| gemini-4-argon (puro) | 68 s | 7,5 | legenda + repetição de clipe; "onde" vago ("gerador de legendas ASS") |
| agy/gemini-3.8-flash-high | 243 s | 7,5 | legenda com arquivo certo; não viu a repetição |
| argon-flash (Flash + Argon) | 422 s | 7,5 | = Gemini 3.8 (o argon.log mostra o Argon servindo **Flash-Lite**: na prática foi o Flash sozinho) |
| gweb/gemini-3.1-pro | 37 s | 7,5 | igual ao Argon puro, "onde" vago; o mais rápido |
| argon-gemini | 1502 s | ✗ | estourou 1500 s (Argon também em Flash-Lite no log) |
| (gabarito Opus 5.5) | — | 8,5 | acertou nenhuma alavanca + legenda + sincronia; NÃO viu o "desviver" nem a repetição |

**Comuns a todos (bom):** ninguém mexeu nos testes A/B por nota de júri (D1/D3) e ninguém repetiu os erros proibidos (fala
cortada no fim, tarja sem prova). **Erros comuns:** todos puseram o card VORIN do topo na nossa conta (é a própria
FONTE vorin25); os que explicaram a "repetição/rewind" culparam o nosso montador por reusar trechos, mas o log mostra cortes
em ordem (0/6/9/14 s, fonte 23 s, narração 25 s): quem repete o clipe é a edição da fonte. Ninguém viu a sincronia
fala × imagem (3 Shorts).

**Aplicar e medir (fase 2):** a única alavanca proposta (argon-pro, regra de roteiro "conjugue os verbos") não muda a
saída: `anime_script` passa cada frase pelo `anti_ban` depois do modelo (linhas 714/721/752), e era essa troca fixa
`matou|morreu|mortos → "desviver"` que quebrava a frase. Por isso a regra não foi aplicada; consertei a causa no código
(`viralizador._tirar_vida`: "tirou a vida de todos/do dragão", "me matou" → "tirou a minha vida", "morreu" → "desviveu",
"a mata/na mata" não muda mais). A proposta em que todos concordaram (legenda) foi aplicada: base 85% → 80% da altura,
teto de 82% com SUB_Y_CENTER (`fx_subtitles`); medido no cartão real: o fim da 2ª linha agora fica em 0,80–0,83 da altura.

**29/10 ~20h — mais 3 (dona: "gweb no pensamento máximo, Sonnet web e argon-sonnet"), MESMO prompt salvo
(`fase1\prompt.md`), respostas em `D:\tmp\bancada_real\fase3\`:**

| Modelo | Tempo | Nota | Por quê |
|---|---|---|---|
| **cw/claude-sonnet-5-5** (Sonnet web) | 26 s | **8,0** | o melhor raciocínio sobre as REGRAS: nenhuma alavanca e diz por quê, separa o que é de 1 Short só, é o ÚNICO que cita a sincronia fala × imagem, admite "não tenho o roteiro.txt nem o log [hardsub], não confirmo". Mas não abre arquivo (a ponte web não entrega conteúdo lido) → não acha nada fora do pedido (sem "desviver") |
| gweb/gemini-3.1-pro (pensamento máx.) | 23 s | 7,5 | igual à 1ª rodada (que era nível padrão): pensamento máximo não mudou a resposta. No argon.log, 1 conta serviu Flash-Lite e o rodízio passou para a próxima; não dá para garantir que a resposta final veio do Pro |
| argon-sonnet | 31 s | 7,0 | genérico, "onde" vago ("script de renderização", "módulo seletor"); = Argon puro sem nada a mais |

Erros que se repetem: os 3 culpam o nosso montador pela repetição (é a fonte) e o card VORIN (é a fonte).

**+ híbridos Argon × Sonnet web (dona 29/10), mesmo prompt, `fase3\hx-*-sonnet.json`:**

| Modelo | Tempo | Nota | Por quê |
|---|---|---|---|
| **hx-revisor-sonnet** (Sonnet faz, Argon revisa) | 58 s | **8,5** | o melhor da família: nenhuma alavanca com motivo; conserto da legenda CERTO no desenho ("ancorar o bloco, subir em vez de empurrar a 2ª linha" = o que foi aplicado); sincronia como proposta com hipótese; separa 1-Short; usa os números do brief. Sem nome de arquivo; repetição culpa o nosso corte (é a fonte) |
| hx-erro-sonnet (Sonnet faz, Argon no erro) | 41 s | 8,0 | parecido; sincronia proposta; "conferir o log se o card é nosso" (cuidado certo); arquivos não confirmados |
| hx-maos-sonnet (Argon decide, Sonnet executa) | 37 s | 7,0 | = argon-sonnet: genérico, "template Remotion" (a legenda não é Remotion) |
| hx-plano-sonnet (Argon planeja) | 53 s | 6,0 | APLICOU regra de roteiro para resolver layout/sincronia ("frases curtas para a legenda caber numa linha") = erro clássico; argon.log com Flash-Lite servido |

Nenhum dos Sonnet abriu quadro nem achou nada fora do pedido (a ponte web não entrega arquivo lido): o "desviver" só o
argon-pro achou. Quando o Sonnet escreve a resposta final (revisor, erro), o raciocínio sobre as regras melhora; quando o
Argon manda (mãos, plano, socorro), cai para o nível do Argon puro ou pior.
**Placar do melhorador (mesmo lote):** argon-pro 8,5 = hx-revisor-sonnet 8,5 > Sonnet web 8,0 = hx-erro-sonnet 8,0 >
Argon puro / Gemini 3.8 / gweb 7,5 > argon-sonnet / hx-maos-sonnet 7,0 > hx-plano-sonnet 6,0.
Sonnet web = melhor custo (26 s) para DECIDIR; argon-pro = único que INVESTIGA (abre quadro). Combinação sugerida (não
ligada): argon-pro decide, Sonnet web como revisor das regras (rápido e não compra prova fraca).

**Conclusão (1 lote = indicação):** para o melhorador vale o **argon-pro** (investiga sozinho; 4 min); reserva
gemini-4-argon (68 s) e Gemini 3.8. O Argon puro e o gweb 3.1 Pro empatam com o Gemini 3.8 quando o defeito já vem
mastigado no júri; a diferença aparece quando é preciso abrir o quadro. `cortes_melhorador.json` decisor =
argon-pro → gemini-4-argon → agy (fora do central; dentro dele vale o botão do painel).

### 27/10 21:55 — CORTES — PRODUÇÃO REAL: Argon vs Gemini 3.8 no texto do vídeo (roteiro, título, gancho)
Dados de `workspace/modelo_texto.jsonl` do PC1 (111 chamadas ao longo do dia 27/10). O Argon roda com raciocínio Alto
desde ~15:50; chamadas anteriores podem ter sido nível padrão ou Flash-Lite (antes das 10:10).

| Modelo | Chamadas | OK | Falhas | Mediana (s) | Min (s) | Max (s) |
|---|---|---|---|---|---|---|
| gemini-4-argon | 85 | 78 | 7 | 20 | 8 | 319 |
| agy/gemini-3.8-flash-high | 26 | 26 | 0 | 7 | 2 | 101 |

**Por tipo de pedido (só os que deram OK):**
| Tipo | Argon mediana | Argon n | Argon falhas | Gemini mediana | Gemini n | Gemini falhas |
|---|---|---|---|---|---|---|
| roteiro | 26 s | 30 | 2 | 7 s | 11 | 0 |
| título (tarja) | 14 s | 16 | 1 | 4 s | 4 | 0 |
| gancho | 16 s | 15 | 3 | 22 s | 6 | 0 |

**Falhas do Argon**: 6 TimeoutError (420 s, 120 s) + 1 HTTP 502 Bad Gateway — todas caíram no fallback Gemini 3.8.
**Falhas do Gemini**: nenhuma.

**Leitura**: Argon é ~3× mais lento que o Gemini 3.8 mas produz texto mais criativo (nota 8.0 vs 7.0 na análise de
roteiro do melhorador [4]). A taxa de falha de 8% (7/85) é aceitável com o fallback automático. Custo real de tempo:
no roteiro, 26 s de mediana (Argon) vs 7 s (Gemini). Num Short de ~90 s que demora ~12 min, o Argon adiciona ~40 s
ao pipeline (~5%), desprezível. O gancho é o único tipo onde o Gemini demorou mais (22 s vs 16 s) — suposição: os 6
ganchos do Gemini foram fallbacks de timeouts do Argon, logo pedidos mais difíceis.

**Decisão (dona 27/10)**: Argon curto com fallback Gemini 3.8 — implementado e medido. Mantém.

### 27/10 ~17h — gemini-argo — CÓDIGO como agente: Argon x Gemini 3.8 e as duplas (Argon já no raciocínio ALTO)
3 tarefas REAIS do nosso código (`captura/hibridos_real.py`): conserto da fila do hipercool (bug de 22/10, 11 testes),
conserto do `_numero` do youtube_http (bug de 27/10, 15) e microcortes dos Shorts (melhoria de 22/10, 11). Nota = testes
ESCONDIDOS montados a partir da solução de referência do Opus 5.5 (o agente não vê o teste). Claude Code CLI pelo proxy
:20133, máx. 30 turnos e 20 min por tarefa, 2 em paralelo, modelo servido conferido ("4 Argon").

| Modelo | Nota | Tempo total | Observação |
|---|---|---|---|
| **hx-maos-gemini** (Argon decide, Gemini executa) | **37/37** | **559 s** | o melhor e o mais rápido |
| hx-socorro-gemini / argon-gemini (Argon faz, Gemini socorre) | 37/37 | 1236 s | |
| gemini-4-argon (puro) | 36/37 | 677 s | errou só "2 meses atrás" |
| hx-erro-gemini (Gemini faz, Argon no erro) | 33/37 | 991 s | youtube_http: estourou 30 turnos sem consertar |
| hx-plano-gemini (Gemini faz, Argon planeja) | 33/37 | 1044 s | idem |
| hx-revisor-gemini (Gemini faz, Argon revisa) | 22/37 | 838 s | idem + microcortes 0 |
| **agy/gemini-3.8-flash-high (sozinho)** | **22/37** | 1617 s | youtube_http sem consertar (30 turnos); microcortes estourou 20 min |
| argon-flash (Flash + ask_argon) | 16/37 | 3600 s | estourou 20 min nas 3 |

**Conclusão:** para código a dupla VALE: quando o ARGON decide (mãos/socorro/puro) sai 36–37/37; quando o GEMINI decide
(sozinho, plano, revisor, erro, argon-flash) ele fica preso no bug do youtube_http (float 3,4 mi / "2.3M") e não sai.
`argon-pro` passou a ser `hx-maos-gemini` (27/10 ~18h). 1 rodada por modelo = indicação. Kiro e Opus não testados
(Kiro sem crédito; dona: sem Opus/Kiro por agora). As notas da manhã com Kiro ficaram em
`hibridos_real_placar_manha_invalido.json` (Argon podia ser Flash-Lite e estava no nível padrão).

### 27/10 12:45 — CLAUDE-CODE-VIDEO — Gemini 3.8 x Argon CRIANDO o vídeo (em medição, atualizo a cada vídeo)
Pedido da dona: trocar o Gemini 3.8 pelo Argon na produção de vídeo (não no melhorador) e medir a diferença.
Desde 12:45, `argon-gemini` (o Argon que não depende do Kiro e usa ferramentas) faz roteiro, editor (Remotion),
corretor e aprendiz. O **júri continua no Gemini 3.8** (4 verificadores, mesmos focos): mudar o juiz junto
tornaria as notas incomparáveis. Métrica = nota da 1ª versão (antes do corretor), por foco, + horas por vídeo.
Custo medido antes de soltar: o argon-gemini leva ~200 s por passo (Gemini 3.8 ~56 s) → prazo do editor 1h30 → 4h,
correção 45 → 90 min. Ele roda 1 por vez (ver Disponibilidade: em paralelo bloqueia as contas).
Viés a descontar: o karaokê pronto (`lib/karaoke.tsx`) entra junto, o que pode subir a LEGIBILIDADE por si só.
Compare movimento, roteiro/diretor e história/retenção com mais peso.

| Vídeo | Tipo | Quem criou | 1ª versão | legib. | mov. | roteiro·diretor / história·retenção | graves | final | horas |
|---|---|---|---|---|---|---|---|---|---|
| Cardápio Digital | anúncio | Gemini 3.8 tiered | 5,62 | 5,5 | 4 | 7 · 6 | 8 | 7,62 | 3,7 |
| Disparo em Massa | anúncio | Gemini 3.8 | 6,25 | 7 | 5 | 7 · 6 | 6 | 6,55 | 8,1 |
| Agenda IA | anúncio | Gemini 3.8 | 6,5 | — | — | — · 5 | — | 6,75 | — |
| Follow-up IA | anúncio | Gemini 3.8 | 6,0 | 7 | 5 | 7 · 5 | 5 | 6,0 | 2,2 |
| VPS Blindada | anúncio | Gemini 3.8 | 6,0 | 6 | 6 | 7 · 5 | 9 | 6,0 | 4,7 |
| Fato ou Fake (emus) | entret. | Gemini 3.8 | 6,5 | 6 | 6 | 8 · 6 | 5 | 6,5 | 6,1 |
| Tumba de Qin | entret. | Gemini 3.8 | 5,5 | 5 | 5 | 6 · 6 | 16 | 7,62 | 4,4 |
| **Média Gemini 3.8** | anúncio | | **6,07** | | | | | | |
| **Média Gemini 3.8** | entret. | | **6,0** | | | | | | |
| Fábrica de Conteúdo | anúncio | **argon-gemini** | **6,25** | 6 | 6 | 7 · 6 | 5 | 6,95 | 5,7 (com 2 estouros do roteiro e o render perdido) |
| Recenas (violão de R$ 200 mil) | entret. | **argon-gemini** | **6,5** | 6 | **7** | 7 · 6 | 6 | **7,5** | 2,8 |
| Inovare (Hermes Call) | anúncio | argon-gemini (fallback editor: argon falhou 20:38, agy completou em 37 min) | **6,05** | 7 | 5 | 7 · 5,2 | 4 | em andamento | ~58 min editor (21 perdidos no Argon) |
| (próximos, desde 20:55) | ambos | editor/corretor **hx-maos-gemini** (mas proxy 20141 FORA → fallback agy), roteiro argon-gemini | | | | | | | |

**Tempo a mais do Argon na CRIAÇÃO, por etapa** (Gemini 3.8 = vídeos de 27/10; argon-gemini = Fábrica):

| Etapa | Gemini 3.8 | argon-gemini | Obs. |
|---|---|---|---|
| Roteiro | 48 s – 2,5 min | Fábrica: 10 min/tentativa, 2 estouros → 50 min · Recenas: **5 min 20 s** | 15:45: Argon com prazo 300 s e depois o Gemini (fallback) |
| Editor | 1h25 – 1h30 (bate no prazo/90 passos) | **16 min** (Fábrica) · **27 min** (Recenas) — MAIS RÁPIDO | o teste curto (200 s/passo) enganava: no editor ele faz muito por passo |
| Correção (por rodada) | 40 – 45 min | (medindo; prazo 90 min) | |
| Vídeo inteiro | 2,2 – 8,1 h (média ~4,9 h) | (medindo) | |

### 27/10 11:20 — CORTES (Shorts de parceiro, recapd bin) — melhorador, roteiro e título do Short
Nota minha (Opus 5.5) contra gabarito, NÃO às cegas. Mesma entrada para todos, proxy :20133, 1 rodada por tarefa.
Detalhe: `D:\gemini-argo\analises\2026-10-27_CORTES.md`; dados: `analises\dados\2026-10-27_CORTES_juiz\` e `_criacao\`.
Para repetir o melhorador: `cortes_melhorador.py --bancada m1,m2,...` (mesmo pedido, nada aplicado).

**Tarefa 1, juiz do melhorador** (júri de 4 Shorts → o que mudar; só alavancas do cortes_ajustes.json). Gabarito: achar
o que é de CÓDIGO (botão INSCREVA-SE nos rostos, texto do topo colidindo com o da fonte, tela final parada) sem repetir
o que já foi corrigido (@ no rosto, tarja sem legenda) nem as lições (fim em gancho é proposital).
**Validade:** as 4 com * rodaram às 10:03, ANTES da conferência do Argon servido (gemini_http, 10:10) — podem ter sido
Flash-Lite; não valem como nota do Argon.

| Modelo | Tempo | Nota | Por quê |
|---|---|---|---|
| Argon puro * | 122 s | 7,0 | INSCREVA-SE nos rostos + erro "SOCOMANDO" no título |
| Flash + Argon | 356 s | 6,5 | = Gemini 3.8; arquivos certos; repetiu a @ no rosto (já corrigida) |
| Gemini 3.8 Flash high | 327 s | 6,5 | igual ao Flash + Argon |
| Argon Pro * | 31 s | 5,5 | só coisa já corrigida; regra de título na alavanca de roteiro |
| Argon + Opus * | 115 s | 5,0 | só coisa já corrigida; arquivo inventado (pipeline/renderer.py) |
| Argon + Kiro * | 36 s | 4,5 | idem; arquivo inventado (pipeline/composicao.py) |
| Argon + Gemini | 509 s | ✗ | "Todas as contas estão bloqueadas" (7 em paralelo esgotaram o Argon) |

Erro de TODOS: puseram regra de layout ("não sobrepor") na alavanca de título, que só muda o texto do título.

**Tarefa 2, roteiro com tempo + título de Short real** (zapc2YyZp0Y, menino entre lobos, 49 s, filme em 1ª pessoa).
O pedido da produção (anime_script.rewrite_curto_com_tempo + seo_generator.gerar_seo_anime), 1 modelo por vez, depois
das 10:10 (Argon conferido). Roteiro: fiel à legenda, 1ª pessoa, fluido, sem palavra inventada. Título: regra "não
entregar o final" + palavras buscadas. Títulos refeitos sem cache (a 1ª volta passou todos pelo mesmo cache).

| Modelo | Roteiro (tempo / nota) | Título (tempo / nota) | Obs. |
|---|---|---|---|
| Argon puro | 195 s / **8,0** | 156 s / 5,0 | título entrega o final ("os LOBOS decidem enfrentar a BATALHA") |
| Argon + Opus | 97 s / **8,0** | 96 s / 5,5 | título truncado ("DESCOBRIU proteção") |
| Argon Pro | 48 s / **8,0** | 23 s / 5,0 | título entrega o final ("encara TIGRE FEROZ com uma matilha") |
| Argon + Kiro | 17 s / 7,5 | 151 s / 7,0 | o mais equilibrado — mas o Kiro acabou |
| Gemini 3.8 Flash high | 6 s / 7,0 | 8 s / **7,5** | roteiro com "sem vergonha" e "pai biológico" inventado |
| Flash + Argon | 6 s / 6,5 | 8 s / **7,5** | = Flash (o Argon não entrou); "Olha isso." solto |
| Argon + Gemini | 162 s / 6,0 | 191 s / 4,0 | "bicho desviver meu pai"; "VINGANÇA do tigre" (falso) |

**Conclusão (1 rodada, 1 fonte = indicação):** roteiro de entretenimento = Argon puro / Argon + Opus (8); título curto
= Gemini 3.8 (6-8 s, sem spoiler). No juiz do melhorador as notas do Argon desta linha não valem (Flash-Lite possível):
os outros chats deram Argon puro 9,5 [2]. Combinação sugerida para os Shorts (não ligada): Argon puro no roteiro e no
juiz, Gemini 3.8 no título.

### 27/10 11:10 — LONGOS (recapd producao\colab, melhorador_longo) — código na caixa e texto do vídeo
Nota minha (Opus 5.5) comparando com o conserto real que eu fiz e com o gabarito que achei no log real. Mesma
entrada para todos, gateway :20133. Detalhe e dados: `D:\gemini-argo\analises\2026-10-27_LONGOS.md` e
`analises\dados\2026-10-27_LONGOS_*`.

**Tarefa 1, código na caixa (cópia isolada, sem ler o original).** Karaokê do recap deitado (fx_subtitles,
libass + Impact) com palavras grudadas ("atingir o" = "atingiro"). Régua: queimei "atingir o" em cada versão e MEDI o
vão entre as palavras no quadro — hoje 0 px. Meu conserto real: 2 espaços no cartão = 9 px, letras intactas (no ar).
⚠ A 1ª rodada (tabela logo abaixo) foi 09:58–10:13, ANTES da conferência do modelo servido (10:10) e com 8 em
paralelo: as notas dos Argon nela NÃO valem (podiam ser Flash-Lite). REFEITA 1 por vez 11:04–12:02, sem nenhum "servido
Flash Lite" no argon.log, mesma tarefa e mesmo arquivo de antes do conserto. `\h\h` também mede 9 px (= o meu):

| Modelo (2ª rodada, vale) | Tempo | Nota | O que fez |
|---|---|---|---|
| Flash + Argon | 645 s | 10 | 2 espaços (= o meu) |
| Argon puro (arquivo no prompt) | 208 s | **10** | `\h\h` (9 px) — certo e o mais rápido; na 1ª rodada o 1/18 s era Flash-Lite |
| Argon + Opus | 785 s | 10 | `\h\h` (9 px) |
| Argon + Gemini | 1098 s | 10 | `\h\h` (9 px), o mais lento |
| Argon puro (ferramentas) | 693 s | 2 | achou a linha certa mas acabaram os turnos antes de gravar |

1ª rodada (só Gemini 3.8 e os do Kiro valem):

| Modelo | Tempo | Nota | Por quê |
|---|---|---|---|
| Flash + Argon | 459 s | 10 | 2 espaços (= o meu), 9 px |
| Gemini 3.8 Flash high | 506 s | 10 | 2 espaços (= o meu), 9 px |
| Argon + Gemini | 908 s | 8 | `\h\h\h`: funciona, mas largo (18 px) e o mais lento |
| Argon + Opus | 443 s | 3 | não editou; só sugeriu `\fsp8` (funcionaria, 8 px) |
| Argon Pro | 157 s | 2 | Spacing 15 = espaçou as LETRAS ("a t i n g i r"), contra a tarefa |
| Argon puro (arquivo no prompt) | 18 s | 1 | espaçou letras e trocou "BackColour" por "BackCloth" (quebraria o ASS) |
| Argon + Kiro | 492 s | 0 | não editou (acabaram os turnos) |
| Argon puro (ferramentas) | 254 s | 0 | "I seem to be encountering an error" |

**Tarefa 2, texto do vídeo pronto (análise + reescrita).** As 9 passagens de vez do recap KwdN (revezamento de
narradores). Achar os problemas e reescrever no jeito de cada personagem (≤ 25 palavras). Gabarito do log real:
"caralho", "Capiroto", "Alexandre Moreno" (pessoa real), "meu chapa" repetido. Nota da reescrita = minha leitura
(graça, personagem, história, tamanho) — NÃO foi às cegas.

| Modelo | Tempo | Nota | Gabarito | Obs. |
|---|---|---|---|---|
| Argon puro | 274 s | 9,0 | 3/4 | a mais engraçada e mais no personagem; 1 fala passou de 25 palavras |
| Argon + Kiro | 178 s | 8,5 | 3/4 | presa à história |
| Argon Pro | 178 s | 8,5 | 3/4 | 16 problemas, o mais completo |
| Flash + Argon | 31 s | 8,0 | **4/4** | curta e certeira; melhor revisor de regra |
| Argon + Opus | 342 s | 7,5 | 3/4 | longa (2 passaram de 25) e soltou "bastardos" |
| Argon + Gemini | 210 s | 7,5 | 3/4 | longa (média 24 palavras) |
| Gemini 3.8 Flash high | 32 s | 7,0 | 4/4 | limpa, mas genérica |

**Conclusão (corrigida 12:05, depois da 2ª rodada):** código = todos acertaram (10) quando servidos de verdade; o
Argon puro com o ARQUIVO NO PROMPT foi o mais rápido (208 s), com ferramentas ele não termina. Gemini 3.8 / Flash + Argon
seguem bons e baratos. Escrita longa e criativa (passagens, jeito do narrador) = Argon puro. Revisor rápido de palavrão/nome proibido
= Flash + Argon. Bate com PRODUTOS na análise; no texto CURTO de anúncio o Argon não ganha (CLAUDE-CODE-VIDEO, PRODUTOS)
— aqui, no texto criativo e longo, ganhou.

**Tarefa 3 (15h), produção de verdade: tempo x qualidade no vídeo longo.** Mesmo trecho (80 frases do recap gF-1,
4 narradores, 2 parceiros), código de produção (anime_tts.revezar), texto cru antes do filtro:

| Combinação | Tempo do trecho | Palavrão cru | Obs. |
|---|---|---|---|
| Gemini 3 Flash (o de antes) | 20 s | "caralho" + "mijada" | rápido, mas suja |
| Gemini 3.8 sozinho | 48 s | 0 | limpo |
| Argon em tudo | 743 s | 0 | blocos de 40 linhas levavam 1–5 min; o 4º estourou 300 s |
| **Argon só na passagem + Gemini 3.8 no resto** | **205 s** | 0 | ESCOLHIDO (dona: "Argon só no curto") |

Num vídeo inteiro (≈1000 frases, 10 narradores): Argon em tudo = +1 h ou mais; Argon só nas 9 passagens = +10–15 min.

### 27/10 11:05 — PRODUTOS (postador-de-videos\bin\produto) — melhorador, roteiro e código na caixa
Nota minha (Opus 5.5), comparando com o que eu mesmo achei e consertei de verdade. 8 modelos, a mesma entrada para
todos, pelo proxy :20133. Dados e scripts (para repetir): `D:\gemini-argo\analises\dados\2026-10-27_PRODUTOS_*`.

**Tarefa 1, melhorador (ensaio: analista → decisor → revisor, nada aplicado).** Vídeo `vpsblindada_ia_20261026_165626`
(júri 6,25). Gabarito: o que consertei depois dele = cartão final parado (→ botão pulsando) e cenas de vídeo paradas
(→ aproximação lenta). Nota: achou o cartão parado 3 · achou as cenas paradas 2 · propostas úteis que passaram no
revisor E na trava em Python 3 · achado que o júri não deu 1 · respondeu em < 200 s 1.

| Modelo | Tempo | Nota | Por quê |
|---|---|---|---|
| Argon puro | 170 s | 9,5 | único que propôs o meu conserto real (aproximação 0,06 → 0,10); viu o corte seco da abertura; 2/2 aprovadas |
| gweb/gemini-4-argon | 258 s | 8,0 | cartão + falta de movimento; 2/2 aprovadas |
| Flash + Argon | 302 s | 8,0 | movimento nas transições; 2/2 aprovadas |
| Argon + Opus * | 379 s | 7,0 | achou o gancho parado; 2/2 aprovadas; não viu as cenas paradas |
| gweb/gemini-3.1-pro | 377 s | 6,5 | pulso 0,06 → 0,12 de uma vez: a trava em Python barrou (máx. 35% da faixa) |
| Argon + Gemini * | 353 s | 5,5 | 1/2 aprovada (a outra era gosto; o revisor vetou) |
| Gemini 3.8 Flash high | 545 s | 5,0 | viu o apresentador parado, não o cartão; 1/2 |
| Argon + Kiro * | 132 s | 4,0 | nenhuma proposta |

\* = rodou antes das 10:10 (conferência do Argon servido): pode ter sido Flash-Lite. O Argon puro começou ~10:10 e o
Flash-Lite das 10:13 (argon.log) foi pego e trocado de conta. Rodei 1 modelo por vez no ensaio.

Todos repetiram os defeitos que o júri já tinha dado (legenda escura sobre a camisa, óculos diferentes entre cenas).

**Tarefa 2, roteiro do anúncio.** O roteirista da produção (`agentes.roteiro`, até 4 tentativas) com o modelo trocado;
o REVISOR de fatos é o de sempre (Gemini 3.8), igual para todos. Mesma pauta por produto: Hermes Call "lead frio
parado", Disparo "envio individual demorado", Agenda IA "confusão de horários". Nota = aprovado + aprovado de 1ª +
tempo + minha leitura do texto (NÃO foi às cegas — suposição de qualidade minha).

| Modelo | Aprovados (de 3) | De 1ª | Tempo médio | Nota | Obs. |
|---|---|---|---|---|---|
| Argon + Gemini | 3 | 2 | 152 s | 7,5 | "clientes antigos ficarem esquecidos" |
| gweb/gemini-4-argon | 3 | 2 | 216 s | 7,5 | "contatos antigos esfriando" |
| Gemini 3.8 Flash high | 3 | 2 | 24 s | 7,0 | na Agenda não diz o nome do produto ("A ferramenta") |
| Argon + Kiro | 3 | 2 | 146 s | 7,0 | |
| Flash + Argon | 3 | 2 | 14 s | 6,5 | sem ferramentas no pedido é só o Flash; jargão "rotação de instâncias" |
| Argon puro | 3 | 1 | 431 s | 6,0 | 2 estouros de tempo; inventou "custa 2500 por mês" na 1ª (barrado) |
| Argon + Opus | 3 | 1 | 307 s | 6,0 | 1 estouro de tempo |
| gweb/gemini-3.1-pro | 2 | 1 | 503 s | 5,5 | a melhor frase ("falta braço para ligar para quem ficou parado"); Disparo: timeout + 502 x2 |

Os textos saíram muito parecidos entre os modelos: no texto curto o Argon não escreve melhor e custa 10–25x mais tempo.
Bate com o [1]: o Argon puro não é o melhor em texto.

**Tarefa 3, código na caixa (cópia do código; só Read/Edit, sem Bash).** Ideia igual para todos: a cena de conversa
(`chat_ui.render`) mediu 1,98% de movimento (limite 4%) → zoom lento no fundo + cartão subindo. Medido com a régua do
júri (`lapidar.movimento`) num render de 8 s. Minha mudança real: 6,4% (antes 3,6%), render 96 s.

| Modelo | Linhas de diff | Quebrou? | Movimento | Obs. |
|---|---|---|---|---|
Nota da caixa: chegou a ≥ 4% 5 · botão em ajustes.py 1 · sombra acompanha o cartão 1 · pula o zoom quando o fundo é
cor lisa 1 · modelo em < 400 s 1 · não mentiu 1. (Caixas rodaram 10:39–11:11, depois da conferência do Argon; 3 em
paralelo.)

| Modelo | Tempo | Diff | Movimento | Nota | Obs. |
|---|---|---|---|---|---|
| Argon + Gemini | 328 s | 55 linhas | 6,4% | **10** | tudo certo, inclusive pular zoom no fundo liso |
| Argon + Opus | 197 s | 55 | 6,4% | 9 | o mais rápido; não pula o zoom no fundo liso |
| Flash + Argon | 659 s | 60 | 6,4% | 9 | certo; lento |
| Argon puro | 1395 s | 58 | 6,4% | 9 | certo; o mais lento (23 min) — aqui o Argon puro editou bem (no [3] não) |
| gweb/gemini-4-argon | 671 s | 53 | 6,4% | 8 | certo; não pula o zoom no fundo liso |
| Gemini 3.8 Flash high | 496 s | 54 | 6,4% | 8 | certo; não pula o zoom no fundo liso. O 1º render de teste passou de 15 min com o PC carregado; sozinho levou 123 s (era a carga, não o código) |
| gweb/gemini-3.1-pro | 1073 s | 0 | — | 1 | não mudou nada (e disse que não fez) |
| Argon + Kiro | 169 s | 0 | — | 0 | **disse "feito" sem mudar nada (resposta falsa)** |

Os 6 que mexeram escreveram quase o MESMO código (botão novo, sombra do tamanho do cartão, zoom no fundo, cartão
subindo). Duas ideias deles eram melhores que a minha. Levei uma para a produção: pular o zoom no fundo liso.
Conferido com foto de fundo (o caso real): 7,05% de movimento.

**Conclusão (1 rodada por tarefa):** na ANÁLISE do melhorador o Argon puro foi o melhor, e rápido. Isso diverge do [1]
(6,5 lá); a diferença é que aqui o gabarito era um conserto de movimento já medido. No ROTEIRO deu empate técnico e o
Gemini 3.8 fica pela velocidade. No CÓDIGO (caixa) quase todos acertaram (8–10); o Argon + Gemini fez o mais completo.
O Argon + Kiro sai do melhorador (resposta falsa). O roteiro rodou 8 em paralelo (10:25–10:55): os timeouts do Argon
podem ser por isso.

### 27/10 10:55 — CLAUDE-CODE-VIDEO (D:\claude-code-video) — melhorador e roteiro
**ATENÇÃO (conferido 14:55):** a Tarefa 1 rodou das 09:46 às 09:56, ANTES da conferência do modelo servido
(10:13), com as contas no limite → as notas [1] do MELHORADOR para as variantes com Argon podem ser do Flash-Lite e
NÃO valem como nota do Argon. A Tarefa 2 (roteiro, 10:28) foi depois da conferência e vale.

**Tarefa 1, melhorador (sombra, nada aplicado):** os 3 papéis do `melhorador.py`: o ANALISTA ranqueia os defeitos
que se repetem nos anúncios, o PROPOSITOR propõe 1 mudança no manual do editor e o CRÍTICO veta ou aprova.
Mesma evidência para todos: a 1ª versão dos 4 últimos anúncios, com notas e defeitos do júri. A nota é minha
(Opus 5.5), comparando com os defeitos REAIS do anúncio de 27/10 (VPS Blindada: card em cima da cabeça do dono,
cenas 2 e 4 iguais, gancho fraco, "100%" e "garantido" inventados, caixa de legenda vazia).

| Modelo | Tempo | Análise | Decisão | Nota |
|---|---|---|---|---|
| Argon Pro | 218 s | 8 | esperar (regra nova medida em só 1 vídeo) — correto | 7,5 |
| Argon + Gemini | 192 s | 8 | esperar (viu que a regra de rosto já existe) — correto | 7,5 |
| Argon puro | 138 s | 7 | proibir molde repetido: alvo certo, regra vaga | 6,5 |
| Argon + Kiro | 451 s | 7 | esperar, motivo fraco | 6,5 |
| Flash + Argon | 311 s | 7 | movimento contínuo: concreta, mas não era o problema principal | 6,0 |
| Argon + Opus | 278 s | 8 | regra que JÁ existe no manual; o crítico dele aprovou sem ver | 5,5 |

Nenhum achou o texto inventado nem a legenda vazia; esses só a trava de texto e o júri pegaram.

**Tarefa 2, roteiro do anúncio (VPS Blindada):** o mesmo prompt da produção (`gerar.prompt_roteiro`). Nota às
cegas (embaralhei, dei a nota e só depois abri a chave), olhando gancho, fala natural, nome da marca, texto de tela
forte, só os fatos permitidos e imagem por cena.

| Modelo | Tempo | Nota | Por quê |
|---|---|---|---|
| Argon Pro | 31 s | 8,0 | melhor gancho ("vive com medo do servidor cair"), texto de tela concreto, só fatos |
| Argon + Kiro | 87 s | 7,5 | gancho de dor forte, imagens com pessoas do público; cena 3 cheia demais |
| Argon + Gemini | 203 s | 7,0 | bom; exagera um pouco ("o tempo todo", "sempre protegida") |
| Argon puro | 101 s | 6,5 | correto, mas NÃO diz "VPS Blindada" em nenhuma cena ("Nós entregamos"); texto de tela genérico |
| Argon + Opus, Flash + Argon, Gemini 3.8 | > 15 min | ✗ | travaram quando o Kiro acabou |

Roteiro de entretenimento: nenhum terminou (mesmo horário).

**Conclusão (pouca amostra: 1 rodada por tarefa):** o melhor nos dois testes foi o Argon Pro, mas hoje ele
depende do Kiro. Sem o Kiro, o mais equilibrado é o **Argon + Gemini 3.8**. O Argon puro não foi o melhor em texto.
Falta a nota de VÍDEO: pôr o roteirista escolhido num vídeo real e comparar a nota da 1ª versão com a dos últimos
anúncios do Gemini 3.8 (6,0–6,5).
Detalhe e dados: `D:\gemini-argo\analises\2026-10-27_CLAUDE-CODE-VIDEO.md` e
`analises\dados\2026-10-27_CLAUDE-CODE-VIDEO_*` (respostas, roteiros, chave do teste às cegas, scripts para repetir).


### 29/10 07:11 — CENTRAL — bancada do decisor dos Cortes (juiz: Opus 5.5)
Pasta: `D:\video-fila\estado\central\bancada\20261029_0703`. Mesma tarefa real para todos; nada aplicado.

| modelo | s | erro | alavancas (passam trava) | diagnóstico | alavancas | risco | distância do Opus | NOTA | ideia |
|---|---|---|---|---|---|---|---|---|---|
| argon-flash | 220 |  | 0/0 | 7 | 4 | 9 | 6 | **6.5** | Exigir no prompt que o modelo cruze o lote com o dado medido D1 (duração 13–24 s e ≥65% assistido) para propor a alavanca de roteiro curto com loop, e que só af |
| agy/gemini-3.8-flash-high | 198 |  | 1/1 | 7 | 2 | 3 | 5 | **4.25** | Proibir no prompt mexer em alavanca em teste A/B (legenda_impacto) com base em 1 Short ou em preferência da dona sem pct_media dos elegíveis, e lembrar que defe |
| antigravity/gemini-3-flash | 12 |  | 1/1 | 5 | 4 | 5 | 4 | **4.5** | Obrigar que todo 'porque' cite métrica medida dos elegíveis (D1: duração curta e loop), nunca o júri, e que o diagnóstico separe defeito repetido em 2 ou mais S |
| cc/claude-opus-5-5 | 50 |  | 1/1 | — | — | — | — | **—** |  |


### 29/10 16:20 — PRODUTOS — melhorador inteiro (analista + decisor + revisor) no mesmo vídeo real (juiz: Opus 5.5)
Vídeo `inovarecom_ia_20261029_044101` (Hermes, variante dono_tres, júri 5,5). Gabarito escrito ANTES e conferido nos
quadros: `D:\video-fila\linhas\PRODUTOS\teste_modelos\GABARITO_opus.md` (causa = formato dono_tres; falsos do júri =
"legenda sem caixa" e "corte seco"). Régua: causa 4 + não comprar falso 2 + mudanças válidas 2 + tempo 2. Ensaio, nada
aplicado; respostas em `teste_modelos\*.json`.

| modelo | prompt antigo (s / nota) | prompt novo (s / nota) | o que fez com o prompt novo |
|---|---|---|---|
| gweb/gemini-3.1-pro | 545 / 6,5 (único a nomear dono_tres, mas comprou os 2 falsos) | **157 / 10** | peso dono_tres 0,3 + respiro da cabeça |
| argon-pro | 511 / 6,5 | 328 / 9,5 | igual; ainda cita "tarja do Call" no motivo |
| argon-flash | — (erro de leitura do motor) | 711 / 9,5 | peso 0,4 + respiro; só 2 achados |
| argon-gemini | 711 / 6 | 378 / 9,5 | peso dono_tres 0,4 + respiro da cabeça (as 2 aprovadas); achou também o cartão final parado; 6,3 min, quase 2× mais lento que o Argon puro |
| gemini-4-argon (Argon puro) | — | 213 / 9,5 | peso dono_tres 0,3 + respiro da cabeça (as 2 aprovadas); sem alarme falso; não citou o cartão final como achado separado; 3,5 min (analista 67 s, decisor 16 s, revisor 95 s) |
| agy/gemini-3.8-flash-high | 716 / 6,5 | 1490 / 7,5 | causa certa + peso dono_tres 0,3, mas só 1 mudança e 25 min (decisor 854 s) |
| hx-erro-gemini | — | 1180 / 9 | gabarito inteiro (peso dono_tres 0,4 + respiro da cabeça, as 2 aprovadas); revisor lento (656 s) |
| hx-plano-gemini | — | 717 / 8,5 | causa certa + peso 0,3; a regra do respiro foi vetada pela trava em Python por falso positivo ("10%") — trava corrigida 29/10 |
| hx-revisor-gemini | — | 678 / 8 | causa certa + peso 0,3, só 1 mudança; 1 achado de efeito na troca para o cartão (sobreposição) |
| cw/claude-sonnet-5-5 (Sonnet web) | — | 203 / sem nota | NÃO avaliável: a ponte web não entrega imagem nem conteúdo de arquivo lido ("só marcadores vazios"); 0 achados honestos. Bug anotado em `D:\sonnet web\PROGRESSO.md` |

**Conclusão (1 vídeo só):** o salto veio do PROMPT (6 -> 9,5–10), não do modelo. Com o prompt novo, gweb/gemini-3.1-pro
foi o mais certeiro e rápido, argon-pro e argon-flash empatados logo abaixo. Dona ligou o melhorador dos produtos com
gweb -> argon-pro -> argon-flash (sem Gemini puro). Cuidado: em 27/10 o gweb levou 377–1073 s e deu 502; reavaliar
com o placar do melhorador (`python -m produto.melhorador --status`) depois de alguns dias.
