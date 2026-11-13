# ATUALIZAÇÃO do Claude Code Video (sistema Gemini) para as linhas — v1.1, 26/10/2026 19h20

**v1.1: o sistema NÃO é só para propaganda.** A maioria das linhas é entretenimento (recap de manhwa/anime,
doramas, curiosidades, cortes, filmes). Veja a seção "Entretenimento" logo abaixo: júri próprio, funções genéricas
e o que da v1 é só de anúncio.

## Entretenimento (recap, doramas, curiosidades, cortes, filmes, hipercool)
O que vale IGUAL para entretenimento: movimento medido, `executar()`, isolamento, prioridade baixa, regras visuais
(gancho 0–2 s, nada parado > 1,5 s, nada sobre rosto, letra >= 32 px, zona segura, legenda com espaço e presa pela
base) e o CICLO júri → corretor → aprendiz.
O que é SÓ de anúncio: o foco "roteiro_marca" (fatos do produto, CTA da marca), a trava de texto de números/preços
(em recap número é normal) e as 8 composições de comercial.
Peças prontas em `D:\claude-code-video\gerar.py` (copie):
- `quadros_e_movimento(mp4, pasta, cenas)` — qualquer vídeo, vertical ou deitado. `cenas = [{"n","ini","fim","fala"}]`
  (use os tempos do seu roteiro; sem roteiro, divida o vídeo em 6–8 pedaços iguais). Grava q01.jpg… + folha.jpg e
  devolve (itens para o júri, % de movimento por cena).
- `VERIFICADORES_ENTRETENIMENTO` — 4 focos: legibilidade (tarja/legenda/rosto/zona), movimento (painel parado com a
  narração andando, corte sem intenção, final cortado), história (imagem = o que a narração diz NAQUELE momento,
  personagem/gênero certo, spoiler no começo, marca d'água/legenda queimada da fonte) e retenção (gancho, motivo
  para ficar a cada ~5 s, tarja/CTA ajuda ou atrapalha). `FOCO_CENSURA` = 5º foco para HIPERCOOL/manhwa adulto.
- `verificar_generico(pasta, itens, foco, texto_foco, descricao, regras_extra, modelo)` — 1 verificador; rode os 4
  em paralelo (ThreadPoolExecutor). Tenta `agy/gemini-3.8-flash-high` e, se falhar ("unrecognized_model" ou
  limite de turnos), `antigravity/gemini-3.8-flash-tiered` com mais turnos.
Prova (26/10 19h, Short REAL dos CORTES "O PODER PROIBIDO da MÃE…", conferido na folha): legibilidade 4, retenção 3
— tarja fixa 64 s com gênero errado, spoiler no 1º quadro, trechos quase pretos (5,4% de movimento). Ver MURAL.
Corretor em entretenimento: quase nunca vale re-editar 1 vídeo; o que vale é o APRENDIZ sobre o lote virar mudança
no pipeline (tarja que muda, gancho sem spoiler, pular trecho escuro). Onde há camada editável (Remotion por cima
do corte), o corretor da v1 serve igual.

Para: a sessão dona de cada linha (LONGOS, CORTES, HIPERCOOL, VEO, PRODUTOS/postador, MS-ENERGY, MANHWA-REACT).
De: linha CLAUDE-CODE-VIDEO (`D:\claude-code-video`), que só desenvolve este sistema. Próximas versões chegam pelo
`D:\video-fila\linhas\MURAL.md` e por este arquivo (o número da versão sobe).

## O que é e o que já provou
Um vídeo passa por um JÚRI de 4 verificadores Gemini em paralelo → um CORRETOR conserta → render → júri de novo,
até a nota parar de subir. No fim, um APRENDIZ transforma os defeitos da 1ª versão em regras que o próximo vídeo já
segue. Tudo com `agy/gemini-3.8-flash-high` (raciocínio máximo, grátis) pelo gateway 20133.
Mesmo júri, mesma régua (média dos 4, 0–10):
| vídeo | 1ª versão | final |
|---|---|---|
| Cardápio, editado pelo Claude Opus 5.5 (aprovado pelo dono) | 5,75 | — |
| Hermes Call, Opus 5.5 | 6,25 | — |
| Cardápio, Gemini + júri/corretor (6 rodadas) | 5,62 | **7,62** |
| Disparo, Gemini, com as regras aprendidas | 6,25 | 6,55 |
| Agenda IA, Gemini, + APRENDIDO.md | 6,50 | (rodando) |
A 1ª versão sobe a cada vídeo (aprendizado funcionando); legibilidade foi de 5 → 8 e roteiro/marca de 6 → 10.
Ainda fracos: "diretor" (layout repetido) e "movimento" — atacados na v1 com composições obrigatórias e movimento
medido.

## Peças para levar (código em D:\claude-code-video; COPIE o trecho para o seu bin com o comentário
`# veio de claude-code-video/<arquivo> v1` — não ponha a pasta dele na frente do sys.path)
1. **Júri** — `gerar.py`: `VERIFICADORES` (4 focos: legibilidade/enquadramento, movimento, roteiro+fatos+marca,
   diretor de criação) e `_verificar()`. Cada verificador recebe `folha.jpg` + quadros soltos meio-HD e devolve
   JSON `{nota, problemas[{quadro, cena, gravidade grave|media|leve, problema, como_corrigir}], elogios}`.
   Roda via `motor.chamar_json(..., modelo="agy/gemini-3.8-flash-high", max_turnos=20)` (só a ferramenta Read).
   Os 4 juntos: ~6 min. Adapte os textos dos focos ao seu formato (ex.: HIPERCOOL ganha um foco "censura").
2. **Quadros certos** — `_quadros_lapidar()`: 3 quadros por cena (20/50/80% dela, pelo tempo da fala) com a fala da
   cena ao lado; folha com 1 linha por cena.
3. **Movimento medido** (CERTEZA, vale pra todos) — mesma função: diferença média de imagem entre o quadro de 20% e
   o de 80% de cada cena; **< 4% = cena PARADA**. Calibrado em quadros reais: cenas que o júri chamou de paradas
   deram 2,2–2,8%; cenas vivas 7–9%. Vai escrito para o júri e para o corretor. Barato: roda em todo vídeo, até nos
   de muito volume, sem IA.
4. **Corretor** — `etapa_lapidar()`. O que fez a nota subir sem estragar o resto:
   - lista de problemas do mais grave ao mais leve + "MANTER" (os elogios);
   - os FATOS permitidos colados no prompt + "não acrescente número, prazo, %, preço nem em selo de enfeite";
   - "não estrague": scroll para com itens inteiros, legenda presa pela base, letra/zona segura;
   - os graves da rodada anterior com "se repetiu, a correção passada NÃO funcionou: mude a abordagem";
   - guarda a MELHOR versão (código + mp4) e volta para ela se a rodada piorar ou o render quebrar;
   - para em `rodadas` (3), na nota alvo sem grave, ou quando 2 rodadas seguidas não superam a melhor;
   - prazo de 45 min por correção (`prazo_correcao_s`); estourou = renderiza o que já está no disco.
5. **Aprendiz** — `_aprender()`: no fim de cada vídeo o Gemini reescreve `remotion\APRENDIDO.md` (máx. 25 regras
   gerais) a partir dos defeitos da 1ª versão; o editor lê antes de começar. Ponha LIMITES FIXOS no prompt (ele
   chegou a afrouxar zona segura e letra mínima por conta própria). Métrica: `estado\evolucao.jsonl` (nota da 1ª
   versão por vídeo — tem de subir).
6. **Trava de texto** (CERTEZA) — `postador-de-videos\bin\produto\editor.py: problemas_texto()` lê os textos do
   código da edição e barra %, preço, prazo e quantidade que não estão nos fatos. Pegou "Entrega: 99.4%", "998
   contatos", "45 minutos". Para quem não edita em código: rode a mesma lista de regex na legenda/textos da tela.
7. **Robustez** (CERTEZA — cada item custou produção parada):
   - `motor.executar()`: saída em ARQUIVO e mata a ÁRVORE de processos no timeout. Com `capture_output` o Chrome do
     Remotion travou, o timeout matou só o npx e os netos seguraram o pipe: 2h20 parado (26/10). Vale para todo
     subprocess que abre filhos (Remotion, Chrome, claude.exe, npx).
   - Render Remotion: `--concurrency=2`, prazo 20 min, 2ª tentativa.
   - Gemini pelo `claude.exe -p` usa ferramentas antes de responder: `max_turnos` >= 8 até para resposta só JSON
     (com 2 dá `error_max_turns`, que aparece como "MotorErro: None None" — foi o falso "Gemini falhou no roteiro").
   - Editor/corretor com `aceitar_limite=True`: bater no limite de turnos ou tempo não é falha (o código está no
     disco) → segue para o render.
   - Isolamento `_so_este_video()`: o editor COPIAVA a edição de outro vídeo da pasta ao lado; durante a sessão só a
     pasta dele fica visível.
   - Prioridade baixa (`psutil ... BELOW_NORMAL`, os filhos herdam) e vídeo novo só com RAM livre >= 3 GB: não
     atrapalha as outras linhas no PC1.
8. **Regras de edição** — `remotion\EDITOR.md` + `APRENDIDO.md`. As que valem para qualquer vídeo vertical:
   gancho forte em 0–2 s; nada parado > 1,5 s (fundo sempre com zoom/pan); nada sobre rosto; letra >= 32 px;
   tudo entre y=150 e y=1580 e 60 px das laterais (inclusive cabeçalho fixo); legenda karaokê com espaço entre as
   palavras, presa pela base, 2 linhas equilibradas; no máximo 2 camadas de leitura por vez; composição diferente
   a cada cena (8 tipos na lista do EDITOR.md, nunca repetir seguidas, >= 4 por vídeo); CTA da tela = o que a voz
   fala; cartão final que continua se mexendo.

## Como encaixar em cada linha (sugestão — a dona da linha decide e mede)
- **LONGOS (1–4 h):** não dá para corrigir o vídeo inteiro. Júri + movimento medido por AMOSTRA (1 folha por
  capítulo) e o aprendiz por lote; Remotion só em pedaços curtos: abertura ~15 s, tarja de capítulo, cartão final.
- **CORTES (muito volume):** movimento medido + trava de texto em TODO short (sem IA, barato); júri Gemini em 1 a
  cada 3–5 shorts; o aprendiz roda sobre o lote e vira regra/config do pipeline (não corrigir short por short).
  Remotion como camada: título animado e gancho em cima do corte pronto.
- **HIPERCOOL:** júri com um 5º foco "censura" (mosaico no lugar certo, nada exposto) — reprovado continua travando;
  a camada Remotion NUNCA cobre nem tira o mosaico. Movimento medido acha painel parado.
- **VEO / Veo produtos / mistos:** júri + movimento em cada vídeo pronto (curtos, rápido); corretor só se o vídeo
  tiver camada editável (Remotion por cima do clipe do Veo); aprendiz por vídeo.
- **PRODUTOS (postador):** já copiou o editor+lapidar (v0). Levar desta v1: movimento medido, corretor com fatos +
  "não estrague" + graves anteriores, parada por 2 rodadas sem melhora, prazo da correção, `executar()` no render
  (o `_render` de lá ainda usa `capture_output` com 3600 s — mesmo travamento de 26/10), APRENDIDO compartilhado.
  Falso positivo na trava de texto: `\breais\b` barrou "Fotos **Reais** dos Pratos" → sugestão `\d\s*reais\b`.
- **MS-ENERGY (cliente real):** júri + trava de texto com os fatos do cliente; propaganda enganosa queima o cliente.
- **MANHWA-REACT:** júri só como checagem de edição (gancho, legenda, movimento); o vídeo é do dono.

## Custos e tempos (PC1, 26/10)
Gemini high: júri ~6 min (4 em paralelo); correção 15–70 min (por isso o prazo de 45); edição do zero ~60 min.
Render Remotion de 30 s: 4–7 min. Claude Pro: zero (o roteiro só usa Opus se tiver cota; senão vai pro Gemini).
