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

## A13. Começo de cada corte (`_inicios`): sólido quando o original é maior que a narração; repete plano quando a narração passa do original
- **Onde:** `recapd-ambientes/producao/bin/anime_segments.py`, `_inicios` (~linha 86) e `_desprender` (~70).
- **Prova (rodado: 6.000 sorteios da função real, 8-40 frases de 2,5-6 s, tempos do roteiro com ±40% de folga, e de 0
  a 3 frases finais com o tempo do FIM do vídeo — CTA/gancho/comentário):**
  | original ÷ narração | casos com 2+ planos repetidos (o corte seguinte começa quase no mesmo ponto) |
  |---|---|
  | 0,8 (narração 25% MAIOR que o original) | **40% a 52%** |
  | 1,0 | 2% a 5% |
  | 1,2 | 0% a 1% |
  | 1,5 e 2,0 | 0% a 1% |
  Nunca saiu corte fora do vídeo nem exceção; ordem invertida só apareceu com tempos de roteiro absurdos.
- **Leitura:** as travas de 30/10 e 01/11 ("nunca volta", `_desprender`, a passada de trás pra frente com
  `RECUO_MAX_S = 8`) funcionam. O que sobra é o caso em que **não existe imagem suficiente**: narração mais longa que o
  trecho-fonte. Aí o fim do vídeo empilha as últimas frases no mesmo plano (exemplo do sorteio: 5 cortes entre
  143,5 s e 151 s de um original de 156,7 s).
- **Como conferir no D::** no log, a linha `[segments] cortes ... (original Xs, narração Ys)`. Contar em quantos
  Shorts recentes `Y > X` — é nesses que o júri vê "take repetido".
- **Conserto sugerido (escolher um):**
  1. Antes de narrar: se a soma estimada das falas (frases × ~4,5 s) passa de 95% do original, pedir ao roteiro
     menos frases (o `target_lines` já existe) — é a causa.
  2. Na montagem: quando `total > src_dur`, espalhar os cortes pela proporção (`t = acum × src_dur / total`) em vez
     de seguir os tempos do roteiro — a imagem anda mais devagar que a fala, mas não repete.
  3. Para as frases finais sem imagem própria (CTA/gancho): usar câmera lenta ou o quadro congelado com zoom do
     último plano, em vez de repetir o trecho.
- **Confiança:** alta na medida; a frequência real depende de quantos vídeos têm narração > original.

## A14. No Linux (Kaggle e STI), 20 chamadas do recap falham sempre por causa de `creationflags=0x08000000` — e o erro é engolido
- **Onde (recapd-ambientes/producao/bin):**
  | Arquivo | Funções | O que deixa de acontecer no Linux |
  |---|---|---|
  | `anime_tts.py` linhas 191 e 193 | `_abrir_com_trecho` | o vídeo NÃO abre com o trecho real do narrador (cai no `except` → "trecho original de X não entrou") |
  | `anime_formatos.py` ~454, ~494, ~496 | `aplicar_efeito_voz`, `_trecho_original`, `preparar_formato` | efeito de voz do formato e trechos originais das vozes não entram |
  | `conferir_audio.py` linha 24 (`SEM_JANELA = 0x08000000`) | `_duracao`, `_tem_som`, `_whisper_local`, `ouvir` | a conferência do áudio devolve sempre "não conferi" — nenhum Short feito no Linux é ouvido antes de subir |
  | `anime_testes.py` ~282 | `conferir` | o teste de voz não confere |
  | `capa_ia_anime.py` ~667 | `_gerar_com_ref` | capa com referência não é gerada por esse caminho |
  | `kaggle_baixar.py`, `parceiro_diario.py`, `recuperar_falsos_mudos.py` | — | só rodam no PC (Windows): sem efeito |
- **Prova (rodado aqui, Linux, Python 3.13):**
  `subprocess.run(["ffprobe","-version"], creationflags=0x08000000)` → `ValueError: creationflags is only supported
  on Windows platforms`. Com um mp4 de 3 s com som: `conferir_audio._duracao` → `0.0` e `_tem_som` → `None`.
- **A camada do Linux não cobre isso:** `recapd-ambientes/producao/colab/sitecustomize.py` traduz caminho `D:\...`
  e troca o encoder, mas não tira `creationflags`. (Se a camada do STI tira, o problema é só no Kaggle — você disse
  que `creationflags` sem `getattr` "quebra lá".)
- **Por que ninguém viu:** todas ficam dentro de `try/except` que registra um aviso e segue. O vídeo sai, só que
  sem o recurso. É o mesmo tipo de falha silenciosa do `color_filter` e do Groq.
- **Como conferir no D::** no `pipeline.log` de um longo do Kaggle, procurar `trecho original de` e
  `creationflags is only supported` (aparece no texto do aviso). No STI, ver se o `conferido_audio` dos Shorts feitos
  lá é sempre `"não conferi (ValueError)"`.
- **Conserto sugerido (um dos dois):**
  1. Central, sem tocar em 97 arquivos: na camada do Linux (`colab/sitecustomize.py` e a do STI), dentro do
     `if os.name != "nt":`, embrulhar `subprocess.Popen.__init__` para **tirar** `creationflags` e `startupinfo` dos
     argumentos. Cobre tudo de uma vez, inclusive o que ainda vai ser escrito.
     ```python
     _popen_init = _sp.Popen.__init__
     def _popen_sem_flags(self, *a, **kw):
         kw.pop("creationflags", None); kw.pop("startupinfo", None)
         _popen_init(self, *a, **kw)
     _sp.Popen.__init__ = _popen_sem_flags
     ```
  2. Nos arquivos: trocar o número fixo por `getattr(subprocess, "CREATE_NO_WINDOW", 0)` (como já fazem
     `climas_voz.py`, `narracao_curva.py`, `qa_video.py`).
  No repositório inteiro são 97 arquivos com o número fixo; a maioria só roda no Windows. A opção 1 resolve os que
  importam.
- **Confiança:** alta (reproduzido). Efeito no vídeo: médio — a abertura com o trecho real do narrador e a
  conferência de áudio são coisas que a dona pediu.

## A15. Conferência de áudio (`conferir_audio.ouvir`): dois jeitos de segurar vídeo bom que sobraram depois do conserto de 13/11
- **Onde:** `recapd-ambientes/producao/bin/conferir_audio.py`, `ouvir` (~linha 88).
- **Lido (a lógica):**
  1. "Quase nada se ouve": segura se `len(palavras) < max(8, duração × 0,6)`. O conserto de 13/11 cobre a
     transcrição VAZIA, mas não a transcrição PARCIAL. Se o Groq devolver só o começo (corte por tamanho, erro no
     meio, limite) num Short de 60 s, vêm 20 palavras → "quase nada se ouve (20 palavras em 60 s)" → segurado →
     `descartar_segurados` leva pro Drive. Pela regra "revisor sem resposta = não conferi": antes de segurar por
     pouca palavra, conferir `_tem_som` (se há som em mais de ~60% do tempo, é a transcrição que falhou) ou repetir
     com o Whisper local, e só segurar se os dois concordarem.
  2. "Só X% do roteiro aparece": compara com `roteiro.txt` da pasta de trabalho. Formatos com fala real do parceiro,
     trecho original do narrador na abertura, mascote ou várias vozes têm bastante áudio que NÃO está no roteiro;
     e o `anti_ban` troca palavras na fala. O limite de 30% é folgado, mas a conta divide pelo roteiro inteiro
     (`/ len(a)`): um Short em que a narração foi cortada pela metade por causa do `target_lines` (o roteiro.txt
     guarda o texto longo) pode cair abaixo. Sugestão: comparar com o que foi NARRADO (as frases que viraram
     `audio_N.wav`) e não com o roteiro bruto.
  3. O veredito `ok: None` é gravado em `conferido_audio` e a função `antes_de_subir` deixa subir — certo. Mas na
     próxima vez ela ouve de novo (só pula quando `ok is True`): Short que não dá pra conferir é transcrito a cada
     tentativa de postagem. Guardar a data e não repetir por algumas horas.
- **Confiança:** média (lido, não reproduzido — precisa de transcrição real).

## A16. Legenda MIX (modo "inteligente"): quase metade das palavras é tratada como palavra FORTE — o destaque perde o efeito
- **Onde:** `recapd-ambientes/producao/bin/legenda_mix.py`, `peso` (~linha 96), `EMOCAO` (~42), `plano` (~124).
- **Prova (rodado, `peso` palavra a palavra):** na frase "Naquele dia o rei morreu. Depois disso tudo mudou! Então Jin
  voltou para casa e ninguém acreditou nele." saem com peso 3 (o máximo): **Naquele**, rei, morreu., **Depois**,
  tudo, mudou!, **Então**, Jin — **8 de 18 palavras**.
- **Causas:**
  1. `lw[:1].isupper() and len(lw) >= 3` dá peso 3 a toda palavra com maiúscula — inclusive a 1ª de cada frase
     ("Naquele", "Depois", "Então", "Quando", "Durante"). A ideia era pegar NOME próprio.
  2. `EMOCAO` tem palavras muito comuns: `tudo`, `nada`, `nunca`, `verdade`, `rei`, `poder\w*` (pega "poderia",
     "poderiam", "poder" verbo), `deus\w*`, `am(ou|ava)`.
  3. Palavra que termina em "!" ou "?" ganha peso 3 mesmo sendo "nele?" ou "isso!".
- **O que o peso 3 faz (em `plano`):** desenho recorte/caixa, cor quente, pop de entrada 1,40x, giro maior em metade
  dos casos, sublinhado em metade. Com metade das palavras assim, a legenda inteira pula e gira — não há contraste
  entre a palavra que importa e as outras, que é a razão de existir do modo "inteligente" (e ele é medido contra o
  "livre" no placar: se os dois se comportam quase igual, o teste não mede nada).
- **Conserto sugerido:**
  1. Maiúscula só conta se a palavra NÃO abre frase (a anterior não termina em `.!?…` e não é a 1ª do vídeo) —
     mesma regra do `anime_formatos._cores_dos_nomes`. `blocos`/`plano` recebem as palavras em ordem, dá pra passar o
     índice ou a palavra anterior pro `peso`.
  2. Tirar de `EMOCAO`: `tudo`, `nada`, `nunca`, `jamais`, `verdade`, `rei`, `rainha`, `poder\w*` (deixar `poderoso`,
     `poderosa`), `am(ou|ava)`.
  3. Teto: no máximo 1 palavra forte a cada 4 (se a anterior forte foi há menos de 3 blocos, a atual desce pra 2).
  4. "!"/"?" no fim só sobe o peso se a palavra tiver 5+ letras e não estiver em `CURTAS`.
- **Observação (não é defeito, só registro):** cada adesivo fica no mínimo 0,3 s na tela; em fala rápida o próximo
  entra antes (13% dos blocos no sorteio, até 0,2 s juntos). Como cada um vai num lugar diferente, deve ser o
  "rastro" pretendido — conferir num vídeo se não encavalam.
- **Confiança:** alta no comportamento (rodado); o ganho visual você julga no vídeo.

## A17. Prompts do roteiro que brigam entre si (a IA obedece um e descumpre o outro)
- **Onde:** `recapd-ambientes/producao/bin/anime_script.py` — `_system()` (~linha 130), `rewrite_curto_com_tempo`
  (~659), `rewrite_longo_com_tempo` (~803), `_COMENTARIO_NARRADOR` (~758). **Atenção:** você avisou que `_ABERTURAS`
  e a 1ª frase do Short estão em teste (T13) — nada aqui mexe nisso.
- **Lido (4 contradições):**
  1. **Colchete proibido x colchete obrigatório.** O `_system()` diz, com "VIOLAÇÃO GERA FALHA CRÍTICA": "NÃO use
     marcações teatrais, **colchetes**, parênteses...". Os dois roteiros com tempo usam esse MESMO sistema e pedem no
     pedido: "Cada linha COMEÇA com o segundo... no formato **[12s]**". O próprio código registra o sintoma: comentário
     de 24-25/10 ("8 respostas com só 2 linhas marcadas"), a 2ª tentativa com "TODA linha começa com [Ns]", e o
     contador `sem_marca` do longo ("N bloco(s) sem marca, espalhados no trecho"). Bloco sem marca = frases
     espalhadas no chute = fala descolada da imagem (o que a dona reclamou em 21/10 e 25/10).
     **Conserto:** nas duas chamadas com tempo, somar ao sistema uma linha: "EXCEÇÃO À REGRA 1: a marca de tempo
     [12s] no começo de cada linha é obrigatória e não conta como colchete proibido." (ou tirar "colchetes" da regra 1
     e proibir só "rótulos como [Música], [Narrador]"). **Como medir:** contar no log `bloco(s) sem marca` e
     `veio com N frases marcadas` antes e depois.
  2. **"Condensada" x "NÃO condense demais".** O `_system()` manda contar "de forma envolvente, **condensada** e
     clara" em todos os nichos; o pedido do longo manda "NÃO condense demais, NÃO pule diálogos importantes". O
     comentário de 02/11 no código conta o resultado: o 1º recap de anime saiu com 60% do original. **Conserto:** o
     `_system()` receber um parâmetro (`longo=True`) e trocar "condensada" por "completa, sem pular cenas" no longo.
  3. **"Não invente fatos" x comentário obrigatório.** O sistema diz "Não invente fatos que não estão na transcrição";
     o `_COMENTARIO_NARRADOR` obriga 2 frases por trecho "que NÃO estão na história". Um modelo cauteloso corta os
     comentários (e aí a dona sente falta: "tem que colocar mais comentários"). **Conserto:** uma frase no sistema do
     longo: "Opinião e ironia do narrador não são fatos inventados — são pedidas abaixo."
  4. **"Nada de despedida, o vídeo roda em loop" x CTA no fim.** `_jeito_do_narrador` termina com "NADA de despedida
     ou encerramento... a última frase emenda na primeira", e o código tem `CTAS_FIM`/`cta_fim` ("Gostou? Segue o
     canal que amanhã tem mais", "Deixa seu like...") e o `fechar_loop`. Se os dois entram no mesmo Short, o loop
     quebra na frase do CTA. Conferir no D: qual dos dois está ligado por canal; se o CTA vale, ele devia vir ANTES
     da frase de loop, não depois.
- **Também no `_COMENTARIO_NARRADOR`:** todo comentário é obrigado a começar com uma de 10 aberturas fixas ("Cá entre
  nós,", "Sinceramente,", "Convenhamos,"...) porque é pela abertura que o `climas_voz.ABRE_COMENTARIO` e o cartão de
  balão reconhecem o comentário. Num longo de 1.500 frases (~50 trechos × 2) são ~100 comentários com 10 aberturas:
  cada uma aparece ~10 vezes — vira bordão involuntário, um a cada minuto. **Sugestão:** a IA marcar o comentário
  com um sinal que não é falado (ex.: a linha começa com `§`), o código guardar o índice e tirar o sinal antes do
  TTS/legenda; aí a abertura fica livre. `eh_comentario` passa a olhar o índice.
- **Miúdo:** "texto **totalment** incompreensível" (falta o "e") no fim do `_system()`.
- **Confiança:** alta em 1 (o código documenta o sintoma), média em 2-4 (lido).

