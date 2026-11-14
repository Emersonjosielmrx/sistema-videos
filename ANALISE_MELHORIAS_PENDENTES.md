# Análise de melhorias pendentes — do agente online para o agente do D:

Arquivo vivo: vou acrescentando achado por achado e enviando ao ramo `claude/optimistic-rubin-8buena` a cada bloco.
**O que está aqui NÃO foi consertado** — é para você (agente do D:) pegar, conferir no código real e num vídeo, e
decidir. O que eu já consertei está em `MELHORIAS_AGENTE_ONLINE.md`.

Como ler cada achado:
- **Onde:** arquivo e linha na cópia do GitHub (no D: a linha pode variar um pouco).
- **Prova:** o que eu rodei/li aqui. "Rodado" = executei a função com o texto de exemplo; "Lido" = só leitura do código.
- **Efeito no vídeo:** o que o espectador vê/ouve.
- **Conserto sugerido:** o menor que resolve.
- **Confiança:** alta (reproduzi), média (li e a lógica é clara), baixa (suspeita — conferir antes).

Não analisei postagem, horários, narradores, fontes e nicho (são seus).

## Estado dos achados (atualizado 14/11 — o que o agente do D: já respondeu)
| Achado | Estado |
|---|---|
| A1 impacto/tensão por pedaço de palavra | **aplicado** no recapd (13/11 14:45, `_casa_lista`); cópias de hipercool/historias paradas pela dona |
| A2 `is_sensual_panel` | código morto, confirmado no D: — nada a fazer |
| A3 regra de gore frouxa | **aplicado** (13/11 14:45, `teste_gore_e_impacto.py`) |
| A4 "Senhora" com voz de homem | aberto |
| A5 narrador com voz de telefone/eco | aberto |
| A6 efeito de painel por pedaço de palavra | aberto |
| A7 gatilho de meme (precisa do catálogo) | aberto |
| A8 linhas dobradas em 4 arquivos | **resolvido** no `main` (anime_script.py voltou a ~1.100 linhas) |
| A9 notas menores | aberto |
| A10 em diante | abertos (escritos em 14/11) |

---

## A1. Impacto/tensão do painel: quando a IA não responde, vale lista que casa pedaço de palavra
- **Onde:** `fx_detect.py` em `recapd-ambientes/producao/bin` (`is_impact_panel` linha ~35, `is_tension_panel` ~574,
  listas `IMPACT_KEYWORDS` linha 23 e `TENSION_KEYWORDS` ~563). Mesma função em `historias-em-frames/*/bin/fx_detect.py`,
  `hipercool-videos/bin*/fx_detect.py`, `postador-de-videos/bin/effects_engine.py` (linhas 321 e 843) e
  `historias-em-frames/*/bin/diretor_cena.py:154`. Quem usa: `fx_clips.py:946-947`, `fx_detect.py:625-626`,
  `hiper-pipeline.py:550-551`.
- **Prova (rodado, com a IA fora do ar):** "O gato caiu da **cai**xa" → impacto (casa `cai`); "Eles de**bate**ram o
  plano" → impacto (`bate`); "Ele **tiro**u a espada" → impacto (`tiro`). Outras da lista que são pedaço de palavra
  comum: `ko` (pouco, koreano), `hit`, `cut` (executou), `cai` (caixa, caiu), `luta` (absoluta, resoluta), `corta`
  (cortava ok; "es**corta**"), `faca` (**faça**? não — sem cedilha; "o**faca**" não; mas "**faca**da" ok), `drop`,
  `shot`, `rip` (t**rip**a, desc**rip**), `pow` (**pow**er), `rage` (ga**rage**m, co**rage**m), `destr` (a**destr**ado).
  Na tensão: `medo` (re**médio** não, mas "**medo**nho" ok), `sombr` (as**sombr**o ok), `escuro`, `revela`, `choqu`,
  `mentir`.
- **Quando acontece:** só quando `haiku_helpers.classify_action` devolve `None` (IA sem resposta, descrição com menos
  de 6 letras). Com a IA respondendo, a lista não é usada. **Preciso que você diga com que frequência a IA falha** —
  se o gateway cai (como o Groq caiu hoje), TODO painel passa pela lista.
- **Efeito no vídeo:** tremor/zoom/SFX de impacto em cena calma ("caixa", "debate"), e a cena deixa de ser tratada como
  tensão quando deveria.
- **Conserto sugerido:** trocar `any(kw in desc_lower for kw in LISTA)` por casar no COMEÇO da palavra (radical) e as
  curtas só inteiras — o mesmo `_rx_elemento`/`_SO_INTEIRA` que pus em `elemental_transitions.py` (item 2e). Curtas
  que têm de ser palavra inteira aqui: `ko hit cut cai rip pow rage drop shot tiro bate luta faca soco medo`.
  O `fx_detect.py` já tem `_kw_match` (linha ~439) com fronteira de palavra — dá pra usar ele direto nas duas funções.
- **Confiança:** alta no defeito da lista; média no impacto real (depende de quanto a IA falha).

## A2. `is_sensual_panel` casa "colocou", "respeito", "escola" — hoje não é chamado por ninguém
- **Onde:** `recapd-ambientes/producao/bin/fx_detect.py` ~linha 601 (`SENSUAL_KEYWORDS` ~591); cópias em
  `historias-em-frames/*/bin/fx_detect.py:535`, `hipercool-videos/bin*/fx_detect.py`, `postador-de-videos/bin/effects_engine.py:867`.
- **Prova (rodado):** "Ele **colo**cou o livro na mesa da es**cola**" → sensual; "A res**peito** do rei" → sensual.
  Pedaços perigosos: `colo` (colocou, escola, colorido), `peito` (respeito), `toca` (tocaia), `pele` (apelou),
  `cama` (camada, camarada), `intim` (intimou, intimidar), `corpo` (corporação), `quente`, `vermelh`, `nervos`.
- **Estado:** no espelho **nenhum arquivo chama** `is_sensual_panel(` (só a definição). Se no D: algum pipeline
  usa (voz sensual no TTS, censura), quase toda frase vira "sensual". Se não usa, é código morto: pode apagar.
- **Conserto sugerido (se for usado):** mesma regra do A1; `colo`, `peito`, `toca`, `pele`, `cama`, `corpo` só inteiras.
- **Confiança:** alta no defeito; a relevância depende de existir chamada no D:.

## A3. "Só troca com gore pesado" dispara com "membros da guilda", "banho", "coberto de neve" — morreu vira "desviveu" em frase normal
- **Onde:** `viralizador.py` (recapd e postador, iguais), regex `_GORE` (~linha 37) usada por `_so_gore`.
- **Regra da dona (30/10, comentário no código):** matar/morrer/morto/assassino/sangue/tortura só trocam quando a
  FRASE tem gore pesado.
- **Prova (rodado no código atual):**
  | Frase | Sai |
  |---|---|
  | Os **membros** da guilda choraram quando ele morreu. | ...quando ele **desviveu**. |
  | Depois do **banho**, ela viu sangue na toalha. | ...viu **suco de tomate** na toalha. |
  | Ele **arranc**ou o carro e o pai morreu de susto. | ...o pai **desviveu** de susto. |
  | O rei morreu e o reino ficou **coberto de** neve. | O rei **desviveu**... |
  | Ela **lavou** a roupa e o sangue saiu. | ...o **suco de tomate** saiu. |
  | Ele foi morto no **Rio de** Janeiro. | Ele **perdeu a vida** no rio de Janeiro. |
  | O assassino **esmag**ou a concorrência nas vendas. | O **criminoso** esmagou... |
  | Ela **cuspi**u o chá quando soube que ele morreu. | ...que ele **desviveu**. |
- **Causa:** `_GORE` tem palavras soltas que não são gore sozinhas: `banho`, `rio de`, `litros`, `po[çc]a`,
  `cobert[oa]s? de`, `lav(ad|ou)`, `cuspi`, `vomit`, `membros`, `arranc`, `esmag`, `rasgad`, `encharc`, `ensopad`.
  "Membros da guilda/do clã/da equipe" aparece em quase todo manhwa de sistema.
- **Efeito no vídeo:** "desviveu", "suco de tomate", "criminoso", "interrogação intensa" em cena sem violência —
  exatamente o que a dona pediu pra parar em 29-30/10.
- **Conserto sugerido:** as palavras soltas só valem coladas no que as torna gore. Regex pronta (testar no D:):
  ```python
  _GORE = re.compile(
      r"jorr|espirr|esguich|"
      r"(?:po[çc]a|banho|rio|litros|mar) de sangue|"
      r"(?:encharcad|ensopad|cobert|lavad|banhad)[oa]s? (?:de|em) sangue|"
      r"(?:cusp|vomit)\w+ sangue|"
      r"\btripas?\b|v[íi]sceras?|entranhas?|"
      r"arranc\w+ (?:(?:a|o|as|os|um|uma|seu|sua|seus|suas|d?el[ea]) )?(?:cabe[çc]a|bra[çc]o|perna|cora[çc][ãa]o|olho|"
      r"l[íi]ngua|membro|pele|unha|dente|m[ãa]o|dedo)|"
      r"esmag\w+ (?:(?:a|o|as|os|seu|sua) )?(?:cabe[çc]a|cr[âa]nio|corpo|peito|m[ãa]o|osso)|"
      r"membros (?:arrancad|decepad|espalhad|cortad|dilacerad)|"
      r"rasgad[oa]s? ao meio|partid[oa]s? ao meio|"
      r"despeda[çc]|dilacer|mutil|esquartej|decapit|degol|perder a cabe[çc]a|cabe[çc]a rol|"
      r"carnific|massacr|chacin", re.IGNORECASE)
  ```
  Atenção: o contexto é olhado no texto JÁ parcialmente trocado (as regras rodam em ordem) — "sangue" ainda está lá
  quando as regras de morte rodam (a de sangue vem depois), então "poça de sangue" continua valendo.
  Pôr no `teste_viralizador.py`: as 8 frases acima têm de sair iguais; "Sangue jorrou do peito dele e formou uma
  poça" e "arrancou a cabeça do monstro e o matou" têm de continuar trocando.
- **Confiança:** alta (reproduzido). Não consertei porque você mexeu no `viralizador.py` hoje e a lista de gore é
  gosto da dona.

## A4. Manhwa com várias vozes: "Senhora Kim", "Sereia", "Freira", "Mascarada" recebem voz de HOMEM
- **Onde:** `edge_tts_engine.py` `_infer_gender` (~linha 231) em `recapd-ambientes/producao/bin` e
  `hipercool-materiais/comum/edge_tts_engine.py`; mesma lógica em `gemini_tts.py` (~linha 280, `_MASC`/`_FEM`).
- **Prova (rodado):** `_infer_gender("Senhora Kim")` → `M`; "a senhora da casa" → M; "Sereia" → M; "Freira" → M;
  "Mascarada" → M; "Paisana" → M. (Rainha, Princesa, Garota, Tia → F, certos.)
- **Causa:** `any(w in pl for w in MASC)` casa pedaço e a lista masculina é testada PRIMEIRO: `senhor` está dentro de
  "senhora", `rei` dentro de "sereia"/"freira", `cara` dentro de "mascarada", `pai` dentro de "paisana".
- **Efeito no vídeo:** mulher falando com voz de homem (o próprio comentário da função diz que ela existe pra evitar
  o contrário).
- **Conserto sugerido:** casar palavra inteira e testar o feminino antes:
  ```python
  pal = set(re.findall(r"[a-zà-ÿ]+", pl))
  if pal & set(FEM): return "F"
  if pal & set(MASC): return "M"
  ```
  e acrescentar em FEM: "sereia", "freira", "bruxa", "deusa", "imperatriz", "duquesa", "condessa", "esposa", "filha",
  "avó", "noiva"; em MASC: "imperador", "duque", "conde", "marido", "filho", "avô", "noivo", "deus", "bruxo".
- **Confiança:** alta (reproduzido). Vale só quando o ensemble manda `gender=None`.

## A5. Narração ganha filtro de TELEFONE ou ECO só por citar "celular", "telefone", "pensando"
- **Onde:** `recapd-ambientes/producao/bin/tts_stage.py` `_voice_context` (linha 27) → `_apply_voice_context`
  (usado nas linhas 135, 141, 170, 186).
- **Prova (rodado):** persona "Narrador": "Ele pegou o **celular** e saiu de casa." → `phone`; "O **telefone** tocou
  na sala." → `phone`; "Ela ficou **pensando** no que fazer." → `thought`; "**Internamente** a empresa estava
  falida." → `thought`.
- **Efeito no vídeo:** a frase inteira do narrador sai com voz de rádio/telefone (banda estreita) ou com eco de
  pensamento, só porque a palavra aparece na história.
- **Conserto sugerido:** o filtro só vale quando a marca vem do roteiro como MARCA — `(telefone)`, `(pensando)`,
  `(rádio)` entre parênteses no texto ou na persona — e nunca para a persona "Narrador"/"Narradora". Tirar da lista as
  palavras soltas `pensando`, `pensamento`, `internamente`, `telefone`, `celular`, `ligação`, `walkie`, `interfone`.
- **Confiança:** alta no comportamento da função; o efeito depende de `tts_stage` estar no caminho do manhwa
  (`hiper-pipeline.py` importa ele).

## A6. Efeito do painel escolhido por pedaço de palavra ("barco" → pan lateral, "sorriu" → zoom no rosto)
- **Onde:** `recapd-ambientes/producao/bin/panel_effects.py` `pick_effect` (~linha 277, `FX_KEYWORDS`, 46 efeitos);
  cópias nos outros projetos que têm `panel_effects.py`.
- **Prova (rodado):** "Ele subiu no **bar**co e **seguiu** viagem" → `panLR` (bar), `panUP` (subiu), `handheld`
  (seguiu); "Ele decidiu ficar na **sala**da" → `panLR` (sala); "Ela sor**riu**" → `facezoom` (riu); "O garoto
  **viu** o mapa" → `facezoom`. Curtas que casam dentro de outras palavras: `bar` (barco, barulho, barreira, embarcou),
  `riu` (sorriu, abriu, cobriu, descobriu, feriu), `viu` (serviu, ouviu, moviu, enviou não), `saiu`, `caiu`
  (decaiu), `rua` (ruas ok; "cruzar" não, "t**rua**" não; "ab**rua**" raro), `alto` (asf**alto**, s**alto**),
  `sala` (salada, assalariado), `eco` (**eco**nomia, r**eco**mpensa!), `medo` (re**medo**), `onda` (redonda),
  `céu/ceu`, `fixo` (pre**fixo**), `lago` (ma**lago**), `tapa` (e**tapa**!), `soco` (**soco**rro).
- **Efeito no vídeo:** o efeito "de contexto" sai errado e, como vale o PRIMEIRO da lista que casar, tira a vez do
  efeito certo. "Recompensa" (toda hora em manhwa de sistema) casa `eco`; "etapa" casa `tapa`.
- **Conserto sugerido:** mesmo de A1 — começo de palavra para radicais e palavra inteira para as curtas
  (`bar riu viu saiu caiu rua alto sala eco medo onda céu ceu fixo lago tapa soco poça slow agua água`).
- **Confiança:** alta (reproduzido).

## A7. Meme de série no longo dispara por pedaço de palavra — não consegui ver os gatilhos
- **Onde:** `recapd-ambientes/producao/bin/anime-pipeline.py` `_memes_series` (~linha 906):
  `any(g in t for g in m.get("gatilhos", []))`, com `t` = frase da narração em minúsculas.
- **Lido (não rodado):** o catálogo `workspace/assets/memes_series/memes_series.json` não vem no espelho (pasta
  `assets` fica de fora), então não sei quais gatilhos existem.
- **Risco:** se houver gatilho curto ("não", "pai", "caro", "rua", "mãe", "casa"), o meme entra em frase que não tem
  nada a ver ("**pai**sagem", "**caro**ço", "**casa**mento").
- **O que fazer no D::** listar os gatilhos de até 5 letras:
  `python -c "import json;d=json.load(open(r'D:\recapd-ambientes\producao\workspace\assets\memes_series\memes_series.json',encoding='utf-8'));print(sorted({g for m in d.values() for g in m.get('gatilhos',[]) if len(g)<=5}))"`
  Se aparecerem curtos, trocar por `fx_detect._kw_match(t, g)` (já tem fronteira de palavra; frase com espaço
  continua valendo por trecho).
- **Confiança:** baixa (suspeita; depende do catálogo).

## A8. URGENTE (não é do vídeo, é do código): 4 arquivos do `main` das 13:41 estão com uma linha em branco entre TODAS as linhas
- **Onde (no `main` eb49ef6 / 5a164a2):**
  `recapd-ambientes/producao/bin/anime_script.py` (2.198 linhas; era 1.099 no `main` das 10:45),
  `recapd-ambientes/producao/bin/claude_client.py` (1.237), `recapd-ambientes/producao/_pc2_claude_client.py` (779),
  `video-fila/linhas/LONGOS/LONGOS_MELHORIAS.md` (261).
- **Prova (rodado):** `git show c79ea97:.../anime_script.py | wc -l` = 1099; `git show origin/main:...` = 2198;
  `git diff -w --ignore-blank-lines c79ea97 origin/main -- anime_script.py` não mostra NENHUMA outra mudança —
  é só a linha em branco intercalada. Nenhum `\r` no arquivo.
- **De onde veio:** não do meu ramo (lá e no `main` das 10:45 o arquivo está normal). Os 4 são arquivos que no D: têm
  fim de linha do Windows (CRLF) e que passaram pelo `git apply` do meu lote. Padrão típico: alguma etapa leu o
  arquivo com `\r\n` preservado e gravou em modo texto no Windows — cada `\r\n` vira `\r\r\n`, que depois é lido como
  duas quebras. Suspeitos: o `github_agora.py`/`salvar_github.py` novo (leitura com `newline=""` + `write_text`) ou o
  próprio `git apply` com `core.autocrlf` ligado. **Confira se no D: o arquivo também está dobrado** (abra
  `D:\recapd-ambientes\producao\bin\anime_script.py`: se tem linha vazia entre todas, está) ou se é só a cópia.
- **Efeito:** o Python ainda compila (testei) e os prompts não mudaram (só docstrings têm `"""` de várias linhas —
  11 em cada arquivo). Mas: (1) o próximo `git apply` do meu ramo nesses arquivos falha ou aplica no lugar errado;
  (2) qualquer número de linha citado em recado/erro fica dobrado; (3) se a etapa culpada rodar de novo, quadruplica.
- **Conserto sugerido (só nos arquivos com o padrão):**
  ```python
  from pathlib import Path
  for p in [r"D:\recapd-ambientes\producao\bin\anime_script.py", r"D:\recapd-ambientes\producao\bin\claude_client.py",
            r"D:\recapd-ambientes\producao\_pc2_claude_client.py", r"D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md"]:
      b = Path(p).read_bytes()
      ls = b.replace(b"\r\n", b"\n").split(b"\n")
      if len(ls) > 40 and all(l.strip() == b"" for l in ls[1::2][:-1]):   # toda linha ímpar vazia = dobrado
          Path(p).write_bytes(b"\r\n".join(ls[0::2]))                    # volta ao CRLF do Windows
  ```
  (conferir com `python -m py_compile` e `git diff -w` depois). E achar a etapa que dobra antes de rodar de novo —
  sugiro um teste no `teste_salvar_github.py`: arquivo com `\r\n` entra, sai com o MESMO número de linhas.
- **Confiança:** alta no fato; média na causa.

## A9. Notas menores (não reproduzi efeito no vídeo; para quando sobrar tempo)
- `recapd-ambientes/producao/bin/classificar_tema.py:61` — canal vira categoria "ia" se o NOME contém "ia" em qualquer
  lugar ("Histor**ia**s", "Famíl**ia**", "Notíc**ia**s", "Curiosidades" não). É roteamento de canal (seu terreno):
  trocar por palavra inteira (`re.search(r"\bia\b", nome)`).
- `recapd-ambientes/producao/bin/anime_publish.py:208` `_CAPA_GENEROS` — gênero da capa por pedaço: `mago` casa
  "es**mago**u", `amor` casa "cl**amor**"/"**amor**tecer", `rank` casa "f**rank**", `humor` ok. Efeito pequeno (só
  muda o tratamento B/C da capa).
- `recapd-ambientes/producao/bin/anime_script.py` `rewrite_curto_com_tempo` (fim da função): quando a 2ª resposta
  ainda vem longa, fica com as N-1 primeiras frases + a ÚLTIMA. O meio-fim da história some e a imagem pula do
  segundo da frase N-1 direto pro fim. Alternativa: pedir à IA para JUNTAR frases (3ª tentativa curta) ou escolher
  as frases por espaçamento no tempo em vez de cortar o miolo.
- `recapd-ambientes/producao/bin/fx_subtitles.py` `_wrap_lines`: `return lines[:3]` — texto que não cabe em 3 linhas
  é cortado sem aviso (palavras somem da legenda/cartão). Hoje os cartões têm 1-3 palavras, então só afeta textos
  longos (gancho, título na tela). Sugestão: diminuir a fonte até caber, em vez de cortar.
- `recapd-ambientes/producao/bin/haiku_helpers.py` `classify_action`: `_cache[key] = res` guarda também `None`
  (IA sem resposta). Enquanto o processo viver, aquele painel nunca mais pergunta à IA e fica na lista de palavras
  (A1). Pela sua regra "sem resposta = não conferi": não guardar `None`.


---

# Análise profunda por módulo (14/11)

## A10. Clima da voz no LONGO: a IA recebe as 1.500 frases numa chamada só e precisa devolver EXATAMENTE 1.500 nomes — quase certo que cai na reserva por palavras
- **Onde:** `recapd-ambientes/producao/bin/climas_voz.py`, `_pelo_llm` (linha ~96) e `_escolher` (~127). (Mesmo arquivo
  nas cópias de `hipercool-materiais/comum` se existir.)
- **Lido:** `_pelo_llm` monta um prompt com TODAS as frases numeradas, pede `max_tokens = 40 + 8 × n` (12.040 para
  1.500 frases), `timeout=90`, e só aceita a resposta se `len(lst) == len(linhas)` e todos os nomes forem válidos.
  Qualquer coisa diferente → `None` → `_heuristica` para o vídeo inteiro. O resultado fica em `_climas_voz.json`.
- **Por que falha no longo:** (1) 12 mil tokens de saída em 90 s não fecham na maioria dos modelos; (2) modelo
  nenhum conta 1.500 itens sem errar por 1 — e 1 a mais ou a menos invalida tudo. É o mesmo defeito que consertei no
  `narracao_curva.escolher_impactos` (item 2c): lá virou escolha por janela.
- **Como conferir no D::** abrir o `_climas_voz.json` de 3 longos recentes e ver `"origem"`. Aposto em
  `"palavra-chave"` em todos. O log tem `[climas] (palavra-chave) {...}`.
- **Efeito no vídeo:** o longo inteiro tem o clima decidido pela lista de palavras do A11 — que erra muito.
- **Conserto sugerido:** janelas de ~80 frases (`_pelo_llm(linhas[ini:fim])`, cada uma tem de devolver o tamanho da
  janela), 1 falha = reserva só NAQUELA janela (e, pra não esperar vários prazos, depois de 2 falhas seguidas o resto
  vai de reserva). Passar na janela as 2 últimas frases+clima da anterior como contexto ("vinha assim: ...") pra não
  quebrar uma luta no meio. O teste pode ser igual ao `teste_impactos_longo.py` (LLM de mentira).
- **Confiança:** média-alta (lido; a taxa real de falha você vê no `origem`).

## A11. Reserva do clima da voz: palavras que casam errado, e frase isolada de "ação" recebe o tratamento de GOL
- **Onde:** `climas_voz.py`, `_PALAVRAS` (~linha 62), `_heuristica` (~83), `ajustes` (~187).
- **Prova (rodado, `_heuristica`):**
  | Frase | Clima que saiu | Por quê |
  |---|---|---|
  | A **soc**iedade **investi**u no garoto. | acao | `soc\w*`, `investi\w*` |
  | Ele **investi**gou o caso. | acao | `investi\w*` |
  | Ela **acert**ou as contas com o banco. | acao | `acert\w*` |
  | O **pul**so dele estava normal. | acao | `pul\w*` (pulso, pulmão, pulseira) |
  | Ele pulou o muro e **soc**orreu a irmã. | acao | `soc\w*` (socorro, social, sócio) |
  | Tinha **algo** na mesa. | tensao | `algo` sozinho |
  | Foi um **tremend**o sucesso. | terror | `tremend\w*` |
  | Eles são do mesmo **sangue**. | terror | `sangue` |
  | Ele **perdeu** o ônibus. | triste | `perdeu` |
  | O **inseto** pousou na flor. | vilao | `inseto` |
  | **Rapaz**, que dia bonito. | engracado | `rapaz`, `mano` |
  | O **sistema** mostrou o **nível** e a **habilidade** dele. | epico | em manhwa de sistema, quase toda frase |
- **O que cada erro faz na voz (tabela `CLIMAS`):** `acao` troca a base pra Kokoro e acelera; `terror` = 16% mais
  lento, 2 semitons abaixo, pausa de 0,45 s; `vilao` = **8 semitons abaixo** (homem) e 12% mais lento; `epico` = 6%
  mais lento, +2 dB e pausa de 0,35 s depois de CADA frase (num manhwa de sistema isso vira o vídeo todo arrastado);
  `triste` = 10% mais lento.
- **Segundo defeito, vale também quando a IA acerta:** em `ajustes`, sequência de ação com 1 frase só (`n == 1`)
  recebe `f = 1.0` — o MÁXIMO da curva: velocidade 1,30x, +4 dB, +1 semitom e pausa de 0,45 s (o "gol"). Uma frase
  de ação sozinha no meio de narração calma sai 30% mais rápida e 4 dB mais alta que as vizinhas.
- **Conserto sugerido:**
  1. Em `ajustes`: `f = (k / (n - 1)) ** 2 if n > 1 else 0.25` e o "gol" (`+1 st`, pausa) só com `n >= 3`.
  2. Na reserva, exigir pelo menos 2 sinais do mesmo clima na frase (ou 1 sinal + a vizinha no mesmo clima) e tirar o
     que é palavra comum: `algo`, `perdeu`, `rapaz`, `mano`, `inseto`, `sangue`, `sistema`, `nível`, `habilidade`,
     `rank`; trocar radicais largos por formas fechadas: `soc(o|os|ou|ando|ar)\b`, `pul(ou|a|ando|ar|o)\b`,
     `investi(u|da|ndo)\b` + "contra", `acert(ou|a) (um|o|em)`, `tremend[oa] de`, `respira\w* (fundo|pesad)`.
  3. Empate: hoje vence o primeiro do dicionário (`acao`). Empate deveria dar `normal`.
- **Confiança:** alta (reproduzido). Pesa mais por causa do A10 (no longo a reserva é quem decide).

## A12. Cartões animados: "ERA", "DURANTE", "FOI" viram cartão de PERSONAGEM; "comentou"/"curto" dispara o cartão de LIKE; a prioridade quase não vale
- **Onde:** `recapd-ambientes/producao/bin/anime_cartoes.py` — `candidatos` (~linha 550), `_PARADA` (~511), as
  `_RE_*` (~517-533) e a escolha em `gerar` (~634).
- **Prova (rodado: `candidatos` com 40 s de narração de mentira, palavras a cada 0,4 s):**
  ```
   0.0s pri 8 personagem  {'nome': 'ERA', 'selo': 'IMPORTANTE'}
   6.8s pri 6 lugar       {'texto': 'ESCOLA DURANTE'}
   7.2s pri 7 personagem  {'nome': 'DURANTE', 'selo': 'IMPORTANTE'}
  12.8s pri 6 personagem  {'nome': 'NAQUELE', 'selo': 'PERSONAGEM'}
  14.8s pri 6 lugar       {'texto': 'MUNDO'}
  19.2s pri 6 triunfo     {'palavra': 'CONSEGUIU'}      <- a frase era "Ele NÃO conseguiu passar na prova"
  21.2s pri 3 alerta      {'palavra': 'CHEFE'}          <- "O chefe dele comentou..."
  22.0s pri 8 like        {}                            <- "comentou"
  24.0s pri 8 like        {}                            <- "o prazo era curto"
  24.8s pri 4 chat        {'baloes': [(25.2, 'que ia embora da'), (26.8, 'cidade')]}   <- "disse que ia embora" (fala indireta)
  27.6s pri 5 antes_agora {'antes': 'DA CIDADE ELE', 'agora': 'AS COSTAS E'}           <- "virou as costas"
  30.0s pri 4 gps         {'palavra': 'SEGUIU'}         <- "seguiu em frente"
  31.6s pri 5 sistema     {'cabeca': 'STATUS', 'linha': 'CLASSE MÉDIA DO REINO'}
  33.6s pri 4 seta        {'palavra': 'OLHA ISSO'}      <- "Olha, eu não esperava"
  38.8s pri 5 personagem  {'nome': 'FOI', 'selo': 'PERSONAGEM'}
  ```
- **Causas, uma por uma:**
  1. **Personagem falso.** `_RE_NOME` aceita qualquer palavra com inicial maiúscula e a contagem NÃO descarta a
     1ª palavra da frase (a lista `inicio` é calculada na linha seguinte mas só é usada pro comentário). Basta a
     palavra abrir 3 frases: "Era", "Foi", "Durante", "Naquele", "Antes", "Ninguém", "Alguém", "Finalmente", "Aquele",
     "Porque", "Sinceramente", "Convenhamos", "Imagina", "Repara". O `anime_formatos._cores_dos_nomes` já faz certo
     (ignora começo de frase) — é copiar a regra: só conta ocorrência que NÃO abre frase; nome que só aparece abrindo
     frase precisa de 5+.
  2. **Lugar + palavra seguinte.** "escola. Durante" virou "ESCOLA DURANTE": o `elif` que gruda a próxima palavra
     maiúscula não olha se a palavra do lugar fechou a frase. Conferir `_FIM_FRASE.search(pal[i][2])` antes de grudar.
  3. **Triunfo em derrota.** `conseguiu` é verbo comum e vem muito com "não". Tirar `conseguiu`; nos outros, pular se
     uma das 2 palavras anteriores for "não", "nunca", "quase", "nem".
  4. **Like fora de hora.** `curt\w*` casa "curto", "curta" (distância), "curtiu"; `coment\w*` casa "comentou",
     "comentário" (o do narrador!). E o like **sempre sai** (até 3 por vídeo) e ainda derruba o cartão que estiver na
     frente, trazendo a mascote. Trocar por formas de pedido: `^(curte|curta|inscreva|inscreve|comenta|comente)$` só
     quando a frase tem "like", "canal", "vídeo", "aí" (ou, mais simples: só nas 3 últimas frases do vídeo e na
     frase do CTA que o roteiro já marca).
  5. **Chat em fala indireta.** "disse que ia embora" vira balão "QUE IA EMBORA DA". Só abrir chat se a palavra
     seguinte NÃO for "que"/"pra"/"para"/"a"/"ao" ou se houver aspas/dois-pontos/travessão logo depois.
  6. **Antes/agora sem sentido.** "virou as costas" → ANTES "DA CIDADE ELE" / AGORA "AS COSTAS E". `virou`/`tornou`
     só valem quando a próxima palavra é "um", "uma", "o", "a", "rei", "lenda"... ("virou um monstro", "tornou-se rei")
     e nunca com "as costas", "a esquina", "o rosto", "a cabeça", "de lado".
  7. **Palavras do dia a dia nas listas:** lugar `mundo`, `cidade`, `escola`, `capital`, `ilha`; sistema `classe`,
     `status`, `missão`, `recompensa`; alerta `chefe`; gps `seguiu`, `procurou`, `fugiu`; seta `olha`. Em `lugar`,
     exigir nome próprio depois ("Reino de Aldor", "Academia Solis") — "mundo" sozinho não é cartão.
  8. **A prioridade (`pri`) quase não é usada.** Em `gerar` os candidatos são ordenados por TEMPO e entra o primeiro
     que aparecer depois do intervalo (`t >= livre`); a prioridade só desempata dois no MESMO instante. Então o cartão
     fraco que vem 0,4 s antes ("SEGUIU") ganha do forte ("PROTAGONISTA"). Sugestão: ao abrir a vaga, olhar os
     candidatos dos próximos ~4 s e ficar com o de maior prioridade.
- **Efeito no vídeo:** cartão animado ocupando a tela com informação errada ("PERSONAGEM: FOI", "VITÓRIA: CONSEGUIU"
  num fracasso, like no meio da história). É dos elementos mais visíveis do vídeo.
- **Como conferir no D::** `marcas_visuais.json` / `pronto.json["marcas"]` de um longo recente lista os cartões e o
  rótulo de cada um — procurar por "ERA", "FOI", "DURANTE", "CONSEGUIU", "SEGUIU".
- **Confiança:** alta (reproduzido na função real). Posso escrever o conserto com teste se você me liberar o
  arquivo (avise no recado).

