# Revisão técnica das 10 melhorias — modelo superior (14/10/2026)

## 4ª rodada (15/10 ~0h30) — revisão da 3ª rodada pelo modelo bom (VALE ESTA)

Conferido com dado real (logs da postagem, prints do Studio, roteiros/vozes em cache dos caps 1–3), não só lendo código.

| # da 3ª | Veredito | O que estava errado de fato | Correção |
|---|---|---|---|
| 1 Prioridade | Ordem ok, **regra por dia não existia** | O comentário dizia "1 compilado + 1 completo por canal/dia", mas `postar_longos` não olhava data, e nas línguas `postar_idiomas` subia o completo e depois **todos os Shorts do capítulo** antes do próximo completo (Shorts na frente do completo por 2–3 dias) | `fila.py`: `_longo_postado_em` (1 compilação por canal por dia, dia de lá); `postar_idiomas`: completo do próximo capítulo primeiro (1/dia, marca `completo_em`; "ja" = subiu antes da regra, não conta como o de hoje), o resto vai pros Shorts. Simulado em 3 rodadas |
| 2 Prompt | Ok, com 1 risco | Piadas literais ("F pro cara", "o maluco deitou"...) pedidas 2–4/capítulo: a 2ª revisão já mediu que o modelo copia frase do prompt → mesma piada em todo capítulo. Exemplo ✅ com narrador "M" no meio dos "F" | Linha do humor: "exemplos mostram o ESTILO; no máx 1 literal por capítulo". Exemplo corrigido. **Prova real: roteiro novo do cap 1 (refeito)** |
| 3 FOLGA 0,45 | Ok | — | Medido: compilado +7–9% (cap 2: 3,8→4,1 s/painel; cap 3: 3,6→3,9 s) |
| 4 Respiração | **Bug** | Ampliava e **cortava** ~2% de cada lado do painel (some a borda branca, pode cortar balão na beirada); INTER_AREA ao ampliar serrilha | O quadro inteiro cresce (1004→1044 px, cabe em 1080), INTER_LINEAR |
| 5 Pan do fundo | **Bug** | Na transição o fundo do momento anterior voltava pro início do pan: pulo de ~30 px a cada troca | Anterior fica no fim do pan (`_fundo_pan(k-1, 1.0)`) |
| 6 Sem voz 2,2 s | Ok, mas quase sem efeito | Medido: só 0/3/4 momentos mudos nos caps 1/2/3 (e são "...", "!?", "Hã?") | Mantido. **Novo**: painel fica no mínimo o tempo de ler os balões (texto entre aspas na descrição, 15 letras/s + 1 s); legenda agora segue a duração da VOZ (antes seguia a do momento e sairia dessincronizada) |

Diagnóstico do "pula falas, passa rápido": quase toda fala de balão **já é dublada**; o compilado conta a mesma
história do vertical (1 locução por painel). Mais tempo de tela só deixa ~8% mais lento. Contar **mais** história
exige roteiro estendido pro 16:9 (LLM + TTS novos por capítulo) — decisão de custo/cota pendente com o dono.

Postagem: o limite é **real e da conta** (Studio: "limite diário de envios alcançado — verificação única ou
esperar 24 h"), vale pro navegador também. O poster às vezes não lê o aviso a tempo e devolve `erro` (timeout no
clique) em vez de `limite` → pausas do limitador maiores (postador é da sessão claude-e9: avisar, não editar).

**Prova real do prompt (roteiro novo do cap 1, 15/10 02:57)** vs antigo: narrador 34→77 das 106 locuções (média
11→14 palavras), quase tudo em discurso indireto ("pergunta se", "diz que", "nosso garoto"); personagens 72→29
(só fala marcante); nomes mantidos (Joo Inhyuk, Noh Yeseul); **nenhuma** piada do prompt copiada literal.
Fracos: abertura genérica (descreve o céu antes de apresentar o protagonista) e a última locução é do personagem
("Herança?!"), não o gancho do narrador que o prompt pede; "porém" (nº 1 dos dados) não apareceu nenhuma vez.

Cap 6 (render 22:40→02:35): cota do Gemini esgotada (429 em voz e LLM) e o **passe final travou 2 h** (timeout de
7200 s; caps 4/5 levaram 13/20 min) → caiu no "fluxo antigo", que não gera a censurada → `sem_censurado`, não posta.
Causa não achada (pasta da sessão já apagada; memes entram sem loop). Suspeita: disputa do Quick Sync com outro
processo noturno (o cap 1, às 4h, fez o mesmo passe em 503 s). Recolocado na fila (`render: falhou`) pra refazer com
cache depois do cap 1; se travar de novo, investigar com o processo vivo (`workspace/tmp/session_*/_video_graph.txt`).
Efeito visto pelo dono: legenda do cap 6 com a frase inteira e o fim cortado — é o gerador do "fluxo antigo"
(`fx_subtitles.render_subtitles_progressive`: frase inteira por PNG, estático depois de 300). Correção
(`fx_acabamento.py`): Quick Sync com limite de 1 h e, se travar (`TimeoutExpired`, antes não era pego), o MESMO
passe no x264 — não cai mais no fluxo antigo por travamento.

Voz pelo proxy (15/10 ~4h, pedido do dono: obrigatório): ver CLAUDE.md "TTS". `gemini_tts.py`: nunca vai direto;
proxy que falha sai da rotação (1 h / 1 dia, `secrets/proxies_estado.json`) e volta sozinho quando a Webshare
renova; página de erro que não é JSON da API não marca mais a CHAVE como erro no banco (antes marcava). Lista:
80 ativas (57 OK + 23 que falharam hoje, marcadas pra testar amanhã); 31.59.20.176:6754 morto, comentado.
Fila/.bat/PC2 com `GEMINI_TTS_PROXY_ENABLED=1`; PC2 recebeu o mesmo código e lista (backups `.bak-20261015` lá).

Cap 1 no InovareManhwaVerse: a fila ia subir o cap 1 ANTIGO (o mesmo do inovaremanhwabr). Agora: `refazer` no
estado → fila renderiza de novo com `--force-llm` (roteiro novo); a postagem não pula pro cap 2 enquanto isso.
`personagens_anteriores` passou a ler todos os capítulos (inclusive o roteiro antigo do próprio) pra não trocar
nome/voz. Roteiro antigo guardado em `narration_cache/...106panels.json.antigo-20261013`.

### As 10 melhorias de 14/10 conferidas no cap 1 refeito (15/10 04:07, primeiro render com tudo)

| # | Veredito | Prova |
|---|---|---|
| 1 Dicionário | OK | Roteiro novo: 1 troca (natural), nenhuma palavra proibida sobrou na voz do narrador |
| 2 Propaganda | OK | Pulou o painel 19 (anúncio do scan) + 1 do fim. Obs.: o banner "BLACKOUTCOMICS.COM" carimbado DENTRO de painel de história continua aparecendo (2 de 4 quadros conferidos) — decisão do dono se cobre |
| 3 Tremor | não reconferido | 2ª revisão marcou ok |
| 4 Prompt | OK | ver "Prova real do prompt" acima |
| 5 Sons → narrador | OK | "falas só de som -> narrador: 8/8" |
| 6 SEO | sem prova ainda | nada postado no canal novo; título do compilado saiu bom |
| 7 Legenda | OK | 4 quadros: 1–3 palavras por vez, palavra ativa amarela, cabe na tela |
| 8 30 fps | OK | ffprobe 30/1, 16488 quadros / 549,7 s |
| 9 2.5D | OK | 77 cenas 2.5D (67 recorte + 10 close), 0 falhas (antes 100%) |
| 10 Memes | OK + 1 correção | gatilhos certos; "Por que isso..." (pergunta) disparava choque como "Que isso!" → `fx_memes.py` ignora "que …" depois de "por" |

Outros: o cap 1 vertical ficou com 9,2 min (antes 6) — o narrador conta mais. 1 chave Gemini do banco responde
"API key not valid" (o rodízio contorna).

### Pedidos do dono (15/10 ~5h) — valem a partir do cap 7 (produção ficou pausada ~20 min pra entrarem)

| Pedido | O que foi feito | Prova |
|---|---|---|
| Tremor "de vez em quando" | Sumia porque o 2.5D (que voltou a funcionar) substitui o clip que tremia e o modo tensão ficou "sem vibração". `fx_acabamento.passe_final`: os 7–8 punch-ins de impacto viram TRANCO (26 px que somem em 0,45 s) | trecho de 5 s: 22–36 px entre quadros no impacto, 0 depois de 0,4 s |
| Tirar "BLACKOUTCOMICS.COM" | `bin/marca_scan.py` + `config/marca_scan/`: acha o carimbo pelo CONTORNO (nota 0,85–0,95 real x ≤0,50 fundo) na coluna dele, apaga com a máscara exata (44–54 recortes empilhados) + inpaint. `fila.renderizar` limpa a pasta antes do render (originais em `_originais/`) | cap 1: 14 painéis, cap 7: 18, cap 8: 14; antes/depois conferido (fica uma faixa lisa onde era o texto) |
| Memes no centro, às vezes com som | Figurinha ESTAMPADA no centro (480 px, acima da legenda, sem som). Meme que INTERROMPE: clip tela cheia com o som do meme inserido depois da fala com choque/deboche/vergonha/raiva (1,2–3,5 s, máx 1/min, fora do começo/fim) — entra antes da lista censurada, então as duas versões têm. Bug achado: meme de IMAGEM (102 de 239) aparecia só 1 quadro (faltava `-loop 1`) | cap 1 simulado: 1 interrupção ("Meu Deus do céu"); clip 720x1280/30fps com som; figurinhas no centro conferidas em quadro |
| Pedir "SEM CENSURA" nos comentários | Versão censurada (pt): chamada no topo no começo de cada trecho censurado (máx 1/45 s). Descrição (pt, vídeo com censura e compilado): 2º parágrafo `CHAMADA_SEM_CENSURA`. SEM link/site (política do YouTube). Comentário fixado: depende do postador (sessão claude-e9 não está ativa) | quadro conferido |

### Pedidos do dono (15/10 ~5h30–6h20)

| Pedido | O que foi feito | Prova |
|---|---|---|
| Abertura/final do roteiro (itens 2 e 3) | `narration._abertura_e_fim`: se a 1ª locução não for o narrador apresentando o protagonista, ou a última não for o narrador com gancho, 1 chamada LLM reescreve só elas (lista de personagens com gênero + título da obra; fala original entra entre aspas) | caps 1/3 (cópia): "Joo Inhyuk é um estudante preso numa aula bizarra..." / "Será que...?"; cap 7 real já saiu com a abertura reescrita |
| Línguas sem esperar o pt (item 4) | `fila.idiomas` e PC2: só exigem o capítulo pronto em pt | — |
| Capa sem nudez + estilo Porão (item 5) | `bin/capa_ia.py`: capa REDESENHADA pelo gateway OmniRoute (antigravity/gemini-3.1-flash-image — as chaves Gemini grátis dão 429 em imagem), personagens em `config/capas.json`, 3 cenas do próprio capítulo (LLM) com ELA EM CIMA DELE vestida, texto curto (2–4 palavras) e balão com a fala dela (sem palavra sexual). Toda imagem e todo painel passam por `fx_acabamento._capa_segura` (visão Gemini: exposto/mosaico/casal — o Sightengine deu erotica 0,19 pro mamilo do cap 5). Capa de painel (reserva) só com painéis aprovados; sem painel seguro = sem capa | caps 2–5 e compilado 1–5 regenerados (3 por vídeo, `.capa.jpg` + `_v2`/`_v3`; antigas em `.capa_antiga.jpg`); folha em `workspace/tmp/_capas/com_balao.jpg` |
| Capa com ato sexual implícito (referências do dono) | Recusado: o YouTube proíbe retratar ato sexual em miniatura, mesmo sem genital | — |
| Figurinha desvia de balão (item 8) | `fx_acabamento._posicao_figurinha`: pega o quadro do instante, detecta balão (`censura_visual._mascara_baloes`) e põe a figurinha no centro se livre (≤2% de balão), senão alto/laterais — nunca na faixa da legenda | cap 1 a 30,7 s: desviou do "JOO INHYUK..." pra esquerda; quadros sem balão: centro |
| Compilado com mais narração (item 7) | `hiper-longo._extras`: 1 chamada LLM por capítulo escolhe painéis e escreve 1 frase EXTRA do narrador (só o que está no roteiro/cenas, sem inventar, sem descrever câmera), que entra logo depois da fala do painel (mesmo wav, legenda junto). pt: até 12/cap (voz Gemini liberada só pra ela); línguas: até 30 (edge, grátis). Cache `<roteiro>_longo_extra[_xx].json`. `HIPER_LONGO_EXTRAS=0` desliga | cap 2: 12 frases fiéis ("Ela joga as roupas no chão e afirma que agora pertence a ele por herança"); 1ª versão inventava ("dívida de sangue") — prompt corrigido. Caps 1–5 do deitado só ganham se refizer (`--refazer`, ~60 vozes Gemini) |
| Referência Porão (item 1, parte) | yt-dlp da lista pública (311 vídeos): o que estoura (5–11x) são compilados LONGOS (54 min–3h40), título de premissa, capa casal/harém | `workspace/tmp/_ref_porao/` |

## 3ª rodada (15/10 ~0h) — melhorias na linguagem e no compilado 16:9

Feito por modelo inferior (Opus bloqueado de subagentes). Revisada na 4ª rodada acima.

| # | Mudança | Arquivo | O que mudou | Risco/revisar |
|---|---------|---------|-------------|---------------|
| 1 | Prioridade postagem | `fila.py` postagem() | Compilado 16:9 sai ANTES de completo e shorts. Ordem: `postar_longos → postar_pt → postar_idiomas` (era pt→idiomas→longos) | Lógica simples; verificar que `postar_longos` não consome cota que impediria o completo |
| 2 | Prompt narração | `narration.py` gerar_recap() | Prompt enriquecido com dados do MomoManhwa: moldes de discurso indireto (fala que, pergunta se, diz que pelo visto), bordões (dá uma olhada, toma um susto, porém de repente), humor/opinião (pelo amor de deus / eu no lugar dele / F pro cara), tom informal (tá/pro/pra/num), mais apelidos (bandidão, o trouxa, o psicopata), proibição de descrever aparência, mais 2 exemplos | Prompt ~40% maior — verificar se o modelo segue; gerar recap de teste e comparar |
| 3 | Compilado mais lento | `hiper-longo.py` FOLGA | 0.25→0.45s de respiro entre falas (compilado é pra contar história, não shorts dinâmico) | ~10% mais longo; verificar que narração não fica com silêncio demais |
| 4 | Breathing no cartão | `hiper-longo.py` render | Zoom suave 1.0→1.04 no cartão principal (layout tira/duo/close) durante cada momento. Substitui o deslize horizontal estático (18px) | Custo: 1 resize extra por quadro (INTER_AREA, ~ms); verificar que não corta texto nas bordas |
| 5 | Pan vertical no fundo | `hiper-longo.py` render | Fundo borrado renderizado com +30px de altura; pan de 0→30px ao longo do momento | Mínimo; verificar borda inferior |
| 6 | Painéis sem voz mais lentos | `hiper-longo.py` _momentos | Duração de painel sem narração: 1.0→2.2s (dá tempo de ler legendas e absorver a cena). Shorts já são separados e não são afetados | Compilado ~20-30% mais longo; verificar se não fica arrastado |

---

## 2ª revisão (14/10 ~20h) — conferida nos logs, vídeos e dados reais (VALE ESTA; a 1ª abaixo tem erros)

Critério: não "roda?", e sim "faz o certo na produção?". Medido no log do cap 4 em render, nos roteiros dos caps
1–4, renderizando quadros de verdade (libass/ffmpeg) e nas transcrições do MomoManhwa
(`D:\hipercool-materiais\referencias_narradores\ANALISE_LINGUAGEM.md`).

| # | Item | O que estava errado de fato | Correção (código) |
|---|------|-----------------------------|-------------------|
| 9 | Profundidade 2.5D | **Falhava em 100% dos painéis** (cap 4: `cv2.remap` assert — mapa float64 no NumPy 2) e caía no clip normal. Esticava painel baixo até 1280 px; deformava texto de balão; limiar p95-p5>0,25 não barra nada (mapa já é 0..1) | `fx_parallax.py`: mapas float32; só painel ≥ altura da tela; balões parados (profundidade zerada com borda suave); fora painel >35% balão. Testado: 90 quadros 30 fps, sem deformar balão |
| 8 | 30 fps | A 1ª revisão errou (clipes são 30 fps; `fps` não faz blending). Causa real dos 26,7 q/s: `build_clip` com `-loop 1` sem `-r` sai a **25 fps** em painel largo e no fallback; concat `-c copy` misturava 25/30 e o `fps=30` final duplicava quadro (tranco) | `fx_clips.py`: `-r FPS` antes do `-loop` nas 4 chamadas. O `fps=30` final virou só rede de segurança |
| 7 | Legenda 110 px | `WrapStyle: 2` (sem quebra) + até 3 palavras: **64% dos blocos estimados largos e vários saem cortados nas duas bordas** (render libass conferido) | `fx_acabamento._blocos`: máx. 18 letras por bloco. Os 4 blocos mais largos dos caps 1–4 conferidos em quadro: cabem |
| 2 | Propaganda | Minhas palavras-chave da 1ª correção davam falso positivo: "logo " ("logo em seguida"), "fundo preto", "créditos" (moeda de jogo), "blackout" (marca d'água). **O cap 4 em render perdeu o painel 12 ("SE MASTURBANDO?!")** | `fx_detect.py`: termos só de anúncio + painel com fala ("X diz:") nunca é propaganda. Nos 414 painéis dos caps 1–4: marca só as 4 propagandas reais |
| 4 | Prompt narração | Narrador repetia as frases-exemplo do próprio prompt ("o pior ainda tá por vir", "vocês não estão prontos"), fazia o exemplo FRACO, não explicava a trama; personagens "falavam" gemidos ("Hnngh", "Hang", "?") e a regra "NUNCA narre 'Fulano disse'" contrariava o padrão nº 1 dos grandes canais | `narration.py`: prompt reescrito com o que os dados mostram (presente, fato concreto, discurso indireto, conectivos/reações reais, proibição de frase pronta, abertura que situa) + `_sons_para_narrador` (fala só de som vira narração; o modelo não obedecia sempre). Teste A/B nos 40 primeiros painéis do cap 4: narra a história; 7/7 sons trocados |
| 10 | Memes | Busca por pedaço de palavra: "mano"⊂"humanos", "dor"⊂"narrador", "sério"⊂"mistério"; termos de 2 palavras nunca casavam; "EITA/QUE/RIP" em maiúsculas nunca casavam; 1ª emoção ocupava todas as vagas | `fx_memes.py`: palavra/frase inteira, varredura única no tempo, sem repetir meme, emoção -> grupo de tags que existe no catálogo, vocabulário real do narrador |
| 1/5 | Dicionário | Com a escolha aleatória, alternativas erradas apareciam: "a morte"->"a fim", "uma arma"->"uma instrumento", "a bala"->"a projétil", "heroína" (a protagonista!)->"substância pesada", "Droga!"->"Substância!" | `dicionario_seguro.json`: só alternativas com o mesmo gênero/número; tirados "heroína" e "droga" (ambíguos). `engajamento_narrador` não é lido por nenhum código |
| 3 | Tremor | ok | — |
| 6 | SEO | ok (as tags já tinham o 2º filtro de 480 com aspas/vírgulas em `postar_hipercool._caber_tags`) | — |

Decisão do dono (não mexi): o MomoManhwa fala "sangue/matou/morreu/arma" livremente na narração e só evita no
título — o dicionário hoje troca também na voz do narrador.

---

## 1. Dicionário seguro (`config/dicionario_seguro.json`)

**Funciona**: sim, carrega e aplica substituições.

**Problemas**:
- **Redundância com o prompt**: o prompt de narração (linhas 380-383 de narration.py) já lista
  as mesmas substituições em texto livre ("morte/matar→eliminar"). Se o LLM obedece o prompt,
  o dicionário pós-processamento é redundante. Se não obedece, a regex corrige. Ter os dois
  não é errado, mas mantém listas duplicadas para manter em sincronia.
- **"sangue"→"fluido vital"**: soa robótico. Narradores reais falam "vermelho escorrendo",
  "ele ficou todo sujo" — não "fluido vital". Precisa dos textos dos narradores reais como
  referência para calibrar.
- **"arma"→"ferramenta"**: arriscado em manhwas de fantasia. "Ele empunhou a ferramenta" não
  faz sentido pra espada. Falta contexto — talvez "instrumento de guerra" ou simplesmente
  "espada/lâmina" (que não são palavras proibidas).
- **Idiomas (hi,id,it,ru,th,vi)**: cobertura mínima (4-6 palavras cada). Funcional mas incompleto.
  Não bloqueia nada, melhor que nada.
- **`engajamento_narrador`**: listão de frases fixas mas NADA no código as injeta no prompt.
  São mortas — o prompt lista exemplos avulsos mas não consulta esse JSON. Pode ser útil no
  futuro mas hoje não faz nada.

**Veredicto**: funcional com ressalvas. Os eufemismos precisam ser calibrados com linguagem
real de narradores (quando as transcrições ficarem prontas). As frases de engajamento são
código morto.

---

## 2. Detecção de propaganda (`bin/fx_detect.py` linhas 230-248)

**Funciona**: parcialmente. Keywords + regex estão corretas *em tese*.

**Problema grave já confirmado**: o panel 009 do cap 2 (propaganda Blackout Comics com URL
e "acesso antecipado") **não foi detectado**. A descrição do LLM diz "Tela final exibe
créditos da obra sobre fundo branco com logotipos" — sem as keywords.

**Causa raiz**: `is_propaganda()` depende da descrição textual gerada pelo vision LLM, não
do conteúdo visual/OCR do painel. O LLM resume em português sem preservar as URLs/nomes.

**O que precisa mudar**:
1. Adicionar keywords "créditos", "logotipo", "logo", "tela final", "fundo branco com" à lista
2. Ou (melhor): rodar OCR leve no painel ANTES de gerar a descrição — se detectar ".com",
   "discord", "patreon", "scan", marcar como propaganda sem depender do LLM
3. Panel 010 (gradiente vazio): adicionar filtro por variância/entropia da imagem para pular
   painéis sem conteúdo real

**Veredicto**: o mecanismo funciona mas a fonte de dados (descrição LLM) é frágil. Precisa
de OCR ou detecção visual para ser confiável.

---

## 3. Tremor → movimento real (`bin/fx_parallax.py` linhas 582-591)

**Funciona**: sim. Código matematicamente correto.

**Análise**:
- **Tensão**: balanço ±4px a 0.5Hz horizontal + ±2.5px a 0.35Hz vertical. Frequências
  não-harmônicas (0.5 vs 0.35) evitam loop visível. Bom.
- **Impacto**: tranco de 8px que decai em t/0.12 (3 frames a 25fps, ~4 a 30fps). Rápido
  o suficiente para não parecer tremor contínuo. Com balão, limita a 5px e 0.3s — proteção
  de legibilidade.
- **Zoom de tensão**: z_fg=0.22 vs 0.17 normal. Diferença sutil mas perceptível (personagem
  "pesa" mais). OK.

**Problema menor**: a amplitude do tremor de tensão é FIXA (não varia ao longo do clip).
Num clip de 5s, o balanço é idêntico do início ao fim. Narradores reais fazem a tensão
CRESCER — o tremor deveria intensificar ao longo do tempo. Mas isso é refinamento, não bug.

**Veredicto**: melhoria sólida sobre o anterior. Funcional e visualmente correto.

---

## 4. Prompt de narração viral (`bin/narration.py` linhas 369-413)

**Este é o item MAIS crítico de toda a revisão.**

**Funciona**: sim, gera narração.

**Problemas sérios**:

### 4.1 O prompt INSTRUI a engajar mas NÃO a contextualizar
O prompt diz "reaja às cenas", "use humor", "coloque ganchos" — mas NÃO diz:
- "Explique o que está acontecendo para quem nunca leu o manhwa"
- "Dê contexto sobre os personagens e suas motivações"
- "Não apenas reaja — NARRE a história"

**Resultado** (comprovado nos caps 2-3): o narrador faz reações genéricas
("A tensão é tanta que daria para cortar com uma faca!") sem explicar O QUE está
acontecendo. Quem assiste sem ler o manhwa não entende a trama.

### 4.2 O prompt é um bloco monolítico de texto
São ~45 linhas de instrução num system prompt. Melhor seria:
- Separar ESTILO (como falar) de ESTRUTURA (como organizar a narração)
- Ter exemplos reais de narradores (quando as transcrições estiverem prontas)
- Usar few-shot com trechos de MomoManhwa/oporaodacidadela/etc.

### 4.3 A lista de palavras proibidas no prompt é redundante
Linhas 380-383 listam substituições que o dicionário seguro já faz no pós-processamento.
O LLM às vezes obedece (duplo trabalho) e às vezes não (o dicionário corrige). Ter no
prompt não é errado, mas ocupa tokens com informação que o pós-processamento garante.

### 4.4 "PELO MENOS 40% das locuções DEVEM ser de PERSONAGENS"
Regra rígida sem base nas transcrições reais. Os melhores narradores (MomoManhwa) variam
MUITO: cenas de ação têm 90% narrador, cenas de diálogo têm 80% personagens. Um número
fixo força o modelo a inventar falas ou a suprimir narração contextual.

### 4.5 Sem distinção de tipo de cena
O prompt trata todos os painéis igualmente. Mas painéis de ação, diálogo, flashback,
transição e revelação precisam de tratamentos diferentes:
- Ação: narrador reage, comentário rápido
- Diálogo: personagens falam, narrador contextualiza brevemente
- Flashback: narrador SINALIZA ("voltando no tempo...")
- Revelação: narrador constrói suspense ANTES e reage DEPOIS
- Transição: narrador resume o que mudou

**O que precisa mudar**: reescrever o prompt com base nas transcrições reais dos narradores.
Isso depende do download em andamento. Quando estiver pronto, analisar como MomoManhwa
etc. estruturam a narração e adaptar.

**Veredicto**: funcional mas **subótimo**. O resultado mais importante (narração que conta
a história E engaja) não está sendo atingido — o narrador engaja mas NÃO conta a história.

---

## 5. Sanitização do narrador (`bin/narration.py` linhas 114-130)

**Funciona**: sim, após a correção das smart quotes.

**Análise**:
- Filtra apenas narrador (persona in "narrador", "narradora", "narrator") — correto
- Regex `\b` word boundary, case-insensitive — correto
- Pega a primeira alternativa da lista (`alts[0]`) — sempre o mesmo eufemismo para cada
  palavra. Poderia variar aleatoriamente para não repetir "eliminar" 10x no mesmo vídeo.

**Problema menor**: não varia as substituições. Se "matar" aparece 5x, todas viram
"eliminar". Idealmente usaria `random.choice(alts)` para diversificar.

**Veredicto**: funcional, melhorias possíveis mas não urgentes.

---

## 6. SEO com dicionário seguro (`bin/seo.py`)

**Funciona**: sim (testado, import OK).

**Sem problemas encontrados**. Aplica o mesmo dicionário no título/descrição/tags.
O risco é remover palavras que o YouTube usa para indexação (ex: "ação" em "arma de ação"
vira "ferramenta de ação") mas o regex usa `\b` então só pega palavras inteiras.

**Veredicto**: OK.

---

## 7. Legendas maiores (`bin/fx_acabamento.py` linha 783)

**Fonte Cap: 78 → 110 (+41%), Outline: 6→7, Shadow: 2→3.**

**Problema potencial**: com 110 de FontSize + Margem L/R de 40, uma palavra longa em
idiomas como tailandês ou hindi pode cortar na borda. O ASS faz *word wrap* automático
mas o tamanho 110 em 1080x1920 deixa ~4-5 palavras por linha. Não é problema em PT mas
pode ser em idiomas com palavras longas.

**Comparação**: MomoManhwa usa fontes ~100-120px, então 110 está no range. OK.

**Veredicto**: OK para PT. Monitorar para outros idiomas.

---

## 8. Saída 30fps fixo (`bin/fx_acabamento.py` linha 880)

**`fps=30` como primeiro filtro no grafo.**

**Problema**: `fps=30` faz frame blending (padrão ffmpeg), não drop/duplicate. Se o vídeo
de entrada é 26.7fps variável, o `fps=30` interpola — pode criar frames "fantasma" borrados.
Para shorts/recap isso é aceitável, mas o ideal seria `fps=30:round=near` para duplicar
frames em vez de interpolar, ou gerar os clips já em 30fps upstream.

**Mas**: como os clips 2.5D já são gerados a FPS=25 (`fx_parallax.FPS`), o `fps=30`
está upsampleando de 25→30. Cada 5º frame é duplicado. Visualmente imperceptível em
painéis estáticos com Ken Burns lento.

**Veredicto**: funcional. Pode melhorar com `round=near` mas não é urgente.

---

## 9. Profundidade parallax (`bin/fx_parallax.py`)

**Funciona**: testado, modelo existe, inferência funciona.

**Análise do render** (`_render_profundidade`, linhas 440-474):
- Usa `cv2.remap` com deslocamento baseado no mapa de profundidade — objetos mais perto
  se movem mais. Matematicamente correto.
- Deslocamento máximo: 18px * depth_normalized. Para um painel de 1080px, isso é ~1.7%.
  Sutil mas perceptível.
- Zoom por profundidade: 1.0 + 0.04 * depth * ease. Máximo 4% de zoom no foreground.
- Balanço senoidal (0.4Hz e 0.3Hz) adiciona vida orgânica.

**Problema**: o threshold `profundidade_vale` (p95-p5 > 0.25) é arbitrário. Painéis com
textura uniforme mas alto/baixo (ex: close de rosto que é plano mas tem profundidade)
podem passar. Em prática, funciona porque rostos não são "cenário vazio".

**Performance**: 0.5-0.6s por painel na CPU (Depth Anything V2 Small). Com 100 painéis
= ~60s extra de processamento. Aceitável.

**Veredicto**: bom. Funcional e a qualidade visual deve ser perceptível em painéis de
cenário com profundidade real (prédios, ruas, paisagens).

---

## 10. Memes visuais (`bin/fx_memes.py` + `fx_acabamento.py`)

**Funciona**: testado, 239 memes carregados.

**Problemas**:

### 10.1 Gatilhos por palavra são frágeis
O `escolher_memes` procura palavras como "choque", "confusão", etc. nas `palavras_tempo`
(palavras da legenda com timestamp). MAS: essas palavras são raras na narração — o narrador
diz "EITA!" não "choque". O sistema vai gerar poucos memes porque os gatilhos não casam
com o vocabulário real da narração.

**Correção**: expandir gatilhos com as palavras que o narrador realmente usa (baseado
nas transcrições quando prontas) ou usar detecção de emoção por LLM.

### 10.2 Figurinha no canto pode sobrepor balões
A figurinha fica em x=OW-mw-40=760, y=180 (canto superior direito). Mas painéis verticais
de manhwa frequentemente têm balões nessa região. Não há verificação de colisão com
o texto do ASS.

### 10.3 Memes tela cheia cobrem TUDO
O overlay tela_cheia cobre todo o vídeo (inclusive legenda). Se a narração continua por
baixo (áudio), o espectador ouve mas não vê o que está sendo narrado. Deveria ser
mais curto (0.5-1.0s) ou ter transparência.

### 10.4 Config em fila.json adicionada (OK)
`"memes": {"ligado": true, "figurinha_s": 25, "tela_cheia_s": 60}` — correto.

**Veredicto**: funcional mas os gatilhos vão gerar poucos memes na prática porque o
vocabulário não casa com o da narração. Precisa calibrar depois de ver o cap 4.

---

## Resumo executivo

| # | Melhoria | Funciona? | Qualidade | Prioridade de ajuste |
|---|----------|-----------|-----------|---------------------|
| 1 | Dicionário seguro | ✅ | Eufemismos robóticos | Média |
| 2 | Detecção propaganda | ⚠️ | Falha confirmada | **Alta** |
| 3 | Tremor → movimento | ✅ | Bom | Baixa |
| 4 | Prompt narração | ✅ | **Subótimo** — engaja sem contar | **Alta** |
| 5 | Sanitização narrador | ✅ | OK, falta diversificar | Baixa |
| 6 | SEO seguro | ✅ | OK | — |
| 7 | Legendas maiores | ✅ | OK | Baixa |
| 8 | 30fps | ✅ | OK | Baixa |
| 9 | Profundidade parallax | ✅ | Bom | — |
| 10 | Memes visuais | ✅ | Gatilhos fracos | Média |

**Os 2 itens que MAIS impactam a qualidade do vídeo final**:
1. **Prompt de narração** — o narrador precisa CONTAR a história, não só reagir
2. **Detecção de propaganda** — painéis de crédito/scan estão entrando no vídeo

Ambos dependem das transcrições dos narradores reais (download em andamento em
`D:\hipercool-materiais\referencias_narradores\`) para serem melhorados com dados reais.
