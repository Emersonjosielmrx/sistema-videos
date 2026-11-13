# CORTES — 03 — Voz (o que a dona mais reclama)

> **Projeto: linha CORTES** — Shorts de canais parceiros (recapd, `D:\recapd-ambientes\producao\bin`; estado em
> `D:\video-fila\linhas\CORTES`). Escrito pela sessão da linha CORTES em 28/10/2026.

## Fatos
- Motor: `D:\recapd-ambientes\producao\bin\anime_tts.py` — frase sai do Edge (base) e o RVC v2 troca o timbre
  pelo narrador clonado (`preparar_clone`, `_frase_v2`). Curva de locutor: `bin\narracao_curva.py`.
- Bases: Francisca (pronúncia), Kokoro (emoção), misto. Dona 28/10: Francisca sozinha é ruim; vozes escolhidas
  pelo PÚBLICO (memória `feedback_vozes_por_publico.md`). Edge puro proibido (sem clone o Short nem sai).
- Placares que já existem e esta sessão não analisou: `D:\postador-de-videos\_analise\placar_narradores.json`,
  `placar_voz_base.json`, `placar_testes_voz.json` (+ sorteio Thompson em `bin\anime_testes.py`).
- Amostra nova a ouvir: narrador_chris em
  `D:\hipercool-materiais\CORTES_ULTIMO_VIDEO\testes\voz_narrador_chris_28-10\` (base francisca e kokoro).
- Defeitos de hoje: (a) "coco" lido "cocô" -> `anime_tts._pronuncia` (lista manual); (b) REGRESSÃO 28/10: o pt saiu
  com base Edge em inglês (Emma) por baixo do clone porque `ANIME_TTS_VOICE` significava duas coisas — corrigido com
  `ANIME_OUTRA_LINGUA`; 1 Short segurado (larissa-manoela_cap1_20261028).

## Onde esta sessão chegou no limite
- Qualidade de voz é julgada de ouvido pela dona; não há medida automática de "soa natural/locutor". O júri olha
  quadros, não escuta.
- Pronúncia: correções são uma lista à mão. Não sei quantas palavras ambíguas (homógrafos, nomes estrangeiros,
  siglas) o Edge erra no corpus real.

## Perguntas para o Fable
1. Cruzar placar_narradores/voz_base com nicho e canal: qual narrador rende em qual público? Proponha o elenco.
2. Medida automática de qualidade da narração (prosódia, pausas, picos, ritmo por clímax) — dá para fazer barato?
3. Varredura de pronúncia: rodar os roteiros dos últimos 7 dias e listar palavras com risco de erro do Edge pt-BR.
4. A curva de locutor (`narracao_curva.py`) está boa? Compare com uma narração humana de referência.

## Fable — resultado
**29/10 (Fable).**
1. **Placar narrador × nicho (`placar_narradores.json`, 9 nichos):** não dá elenco ainda — quase todo narrador tem 1
   teste (1–3 por nome). O único com sinal: `walter_white_breaking_bad` 3/3 vitórias em dorama (e 1/2 em fatos).
   `alex_madagascar` 1,0 em 2 (filme), `capitao_nascimento` 1,0 em 1 (filme) — n 1–2. E o placar mede "views ×
   mediana do canal", que o ER_01 mostrou ser ruído quando mistura vídeos não elegíveis (60% deles). Proposta: (a)
   recalcular as vitórias só com vídeos que receberam lote (views_periodo ≥ 20) e por `pct_media`, não views —
   script pronto para adaptar: `engenharia_reversa\continuaram_x_views.py` (tem narrador na ficha); (b) elenco só
   com n ≥ 6 por narrador-nicho; até lá o Thompson do `anime_testes` continua explorando (está certo assim).
2. **Medida automática barata de narração (sem IA):** no wav final, `ebur128` dá a faixa de dinâmica (LRA: locutor
   humano 8–14 LU; Edge puro ~3–5); `silencedetect -30dB:0.25` dá as pausas (nº/min e duração média — locutor
   respira 10–16/min); velocidade = palavras do roteiro ÷ duração de fala (pt-BR locutor 2,6–3,2 pal/s); pico de
   fala no clímax = RMS por frase (ffmpeg `astats` por segmento do `roteiro_tempos.json`) e comparar a frase do
   clímax com a média (locutor sobe 3–6 dB). Tudo roda no `qa_video` (D10) em segundos; dá uma "assinatura" por
   narrador para comparar com 1 referência humana que a dona aprove. Não substitui o ouvido dela — serve para
   barrar o que saiu chapado (LRA < 4) antes de ela ouvir.
3. **Varredura de pronúncia (feita):** `python D:\video-fila\engenharia_reversa\pronuncia_risco.py 7` → 527 roteiros
   dos últimos 7 dias, `pronuncia_risco.json`. Risco real (ignorar "ele/para/esse", são só frequentes): homógrafos
   **logo (172), pelo (124), corpo (113), novo (96), sobre (72), jogo (63), olhos (59), medo (48), forma (46),
   pode (44), povo (38), rosto (34), cobra (33), começo (20), olho (20), gosto (19), ovo (12), soco (11)** — o Edge
   acerta a maioria pelo contexto, mas "gosto/jogo/olho/soco/ovo/corpo/povo" (ô × ó) são os que mais saem errados;
   siglas: **GTA (28), RP (22), FPS (12), GTRP (8), VIP, IP, NPC, RTX, CEO, SEGA, GG, MC** — o Edge soletra "RP"
   e "GG" mas lê "SEGA"/"FIFA" como palavra (certo), "GTRP" sai estranho; nomes estrangeiros mais usados: Aki (94),
   Power (67), Makima (57), Jack (41), Goku (40), Kishibe, Hanako, Amy, Kobeni, Kang — "Power" sai "póuer" (ok),
   "Aki" sai "áqui" (ouvir). A lista `anime_tts._PRONUNCIA` (linha 58) é onde entram; sugiro começar por GTRP→"G T
   R P", RP→"R P", GG→"gê gê", e os ô/ó que a dona reprovar no ouvido.
4. **Curva de locutor × humana:** não comparei (sem referência humana aprovada e sem ouvir). A medida do item 2 é o
   caminho para comparar com número.
