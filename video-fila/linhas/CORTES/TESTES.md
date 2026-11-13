# CORTES — TESTES A/B (fator | versões | vídeos | views48h/mediana da conta | decisão)

## T2 — cobertura da legenda da fonte: tarja exata x delogo (aberto 27/10 06:20)
- Só em Short cuja fonte TEM legenda queimada. Versões: A = tarja branca do tamanho da legenda (caixa justa das
  letras, 1 linha) | B = delogo só na caixa das letras + a NOSSA legenda em cima (como os longos; dono: "quase invisível").
- Sorteio fixo por vídeo (md5 do caminho); registro: postar.json "cobertura" (tarja/delogo/nada).
- Medida: views 48 h / mediana do canal, só entre Shorts com legenda; mín. 6 por versão por canal-tipo.
- Amostra lado a lado: D:\hipercool-materiais\cortes_teste_produto\COMPARA_linha1_original_linha2_tarja_linha3_delogo.png

## T1 — produto nosso no meio do Short (aberto 27/10 00h)
- Fator: 3-4 s de demonstração de produto (Reel de produto_fila) + frase do narrador, num corte a 55-65% do Short.
- Versões: A = Short normal ("limpo") | B = "produto_meio" (1 a cada 3 por conta).
- Onde: SÓ cópias TikTok (postar_tiktok_auto.produto_meio; config tiktok.parceiro_produto). YouTube não.
- Registro: tiktok_auto_posted.json (formato, produto). Views: medir_tiktok (logs\tiktok_views) por conta.
- Medida: views 48 h / mediana da MESMA conta nos Shorts de parceiro A da mesma semana; mín. 6 B por conta-tipo.
- Decisão: B >= 0,9x A -> mantém e testa YouTube; B < 0,8x -> desliga (ligado=false) ou muda o ponto/duração.
- Vídeos: (preencher a cada ciclo)

## T3 — palavra de impacto: CENTRO x LATERAL (ligado 27/10 12:10)
- O quê: Shorts com ênfase/impacto (todos desde 08:40). Metade (md5("leg"+id) % 2) com o impacto como era (enorme no
  centro, Impact) e metade "lateral": inclinado ~9°, 1º à esquerda em Bangers, 2º à direita em LuckiestGuy, até 70%
  da largura. postar.json "legenda_estilo" = centro | lateral.
- Medir: views 48 h / mediana do canal e retenção, >= 6 por versão por canal. GOSTO (dona pediu "de lado").
- Desligar/fixar: cortes_ajustes.json legenda_impacto = centro | lateral | ab (alavanca do melhorador também).

## T4 — frase de expectativa no MEIO (ligado 28/10, frente 7)
- O quê: metade (md5("gm"+id) % 2 = B) com 1 frase curta de expectativa no meio do roteiro ("e o pior ainda estava
  por vir"), sempre cumprida no próprio vídeo; PROIBIDO parte 2 / continua / próximo vídeo. postar.json "gancho_meio" A|B.
- Medir: views 48 h e retenção por canal, >= 6 por versão. Risco: banimento antigo por promessa falsa -> júri olha.
- Desligar/fixar: cortes_ajustes.json gancho_meio = A | B | ab.

## T5 — gancho dos 3 s no REMOTION x ASS (LIGADO "ab" 28/10 — 1º render ok em 63 s, faltava --image-format=png)
- O quê: B = camada Remotion (_cortes_gancho: palavra por palavra com carimbo, a mais longa amarela, tremor) sobre
  o corte do ffmpeg; A = gancho ASS de sempre. postar.json gancho_remotion = B | A_falhou | vazio.
- Custo: Chrome ~1 GB só no render da camada (3,2 s); só com RAM >= 3 GB; PC2/PC3 sempre A (sem Remotion).
- Medir: views 48 h e retenção dos 3 primeiros segundos, >= 6 por versão por canal.
- Ligar: cortes_ajustes.json gancho_remotion = "ab" (ou "B"/"A").
- O que saiu vem do _testes_usados.json da pasta do vídeo (o render roda noutro processo; a variável de ambiente
  não chegava ao postar.json — consertado 28/10, valia para T5 e T6).

## T7 — waifu-mascote num canto nas pausas da narração (ligado "ab" 28/10, pedido da dona)
- O quê: B = bin\cortes_mascote.py, ANTES da legenda (a legenda fica por cima). Até 2 vezes, 2,4 s cada, nas maiores
  pausas entre palavras (>= 0,35 s, depois de 3,5 s, 10 s entre si). Foto de cosplay recortada (17 de
  hipercool-materiais\mascote_waifu_v2\cosplay_recorte; praia fora: fundo de cenário) ou gravação viva
  (workspace\assets\mascote_viva\reacao_*.webm, em loop). 30% da altura, no canto com MENOS detalhe naquele instante e
  fora da faixa da nossa legenda; canto cheio de detalhe = borra o retângulo atrás dela. Entra/sai deslizando.
- postar.json "mascote" = B | A_falhou | vazio (A).
- Medir: views 48 h e retenção; júri (história) não pode cair — se cair, ela está atrapalhando.
- Desligar/fixar: cortes_ajustes.json mascote = A | B | ab. PC2: recortes copiados em C:\hipercool-materiais\mascote_waifu_v2.

## T6 — choque / fogo / glitch nos impactos e nas trocas de cena (ligado "ab" 28/10, pedido da dona)
- O quê: B = quadros transparentes do Remotion (porte do divider.py do manhwa-react, src/videos/_cortes_fx)
  renderizados UMA vez em D:\hipercool-materiais\assets\cortes_fx (impacto_* e varredura_*, 720x1280, 15 quadros).
  O fx_subtitles sobrepõe: impacto = faixa de raio/fogo cortando a tela sob a palavra de impacto; varredura = a faixa
  atravessa a tela em até 2 trocas de cena (>= 3,5 s, 6 s longe de impacto). Estilo fixo por vídeo (raio azul, raio
  amarelo, fogo, glitch). Sem Remotion no render: roda no PC2 também (precisa da pasta cortes_fx no C:\hipercool-materiais).
- postar.json "fx_choque" = estilo usado | vazio (A).
- Medir: views 48 h e retenção, >= 6 por versão por canal; júri (movimento) também deve subir.
- Desligar/fixar: cortes_ajustes.json fx_choque = A | B | ab.

## T8 — Short CURTO (4-5 frases ≈ 20-27 s) x alvo de sempre (ligado "ab" 29/10 03:05, Fable 5.1 — ER_01)
- Por quê (dado, não gosto): os nossos Shorts param em 1.000-1.500 views (1º lote) e os únicos 5 que passaram de
  2.000 têm 13-24 s e 64-89% assistido; os do platô, 50-75 s e 44% assistido (`engenharia_reversa\continuaram_x_views.py`).
  "Continuaram assistindo" (deslizou) é igual nos dois grupos: o que decide o 2º lote é assistir INTEIRO (e repetir).
- O quê: metade (md5("ct"+id) % 2 = B) com `target_lines` = 5 (fonte ≥ 60 s) ou 4 (fonte 30-60 s); fonte < 30 s já
  era 3 e não entra. A = alvo de sempre (min(18, dur/5,5)). O roteiro com tempo continua escolhendo as frases pelo
  segundo do original; o corte segue. postar.json "curto" = A | B.
- Medir: views 48 h / mediana do canal + `pct_media` e `views_periodo` da tabela do Studio (ret_lista), ≥ 6 por versão
  por canal; placar automático `placar_cortes_testes.json` (notificar_telegram) já conta a chave.
- Decisão: B com mais ≥500 ou pct_media ≥ 65% → fixar `curto: "B"` e abrir T9 (loop: final que emenda no início).
  B pior em views E em pct_media em 2 semanas → `curto: "A"`.
- Desligar/fixar: cortes_ajustes.json `curto` = A | B | ab.

## T9 — fala RÁPIDA (+15 pontos %) x como sempre (ligado "ab" 29/10 07:20, Fable — pedido da dona)
- Dona: "quero os vídeos falando mais rápido, um louco como o parceiro kaijime, mas pode ficar ruim em alguns: gera variante,
  vai testando, sobrevive o que se sair melhor". B = `CORTES_FALA_DELTA=15` no `anime_tts._frase_v2` (Edge rate +15 e Kokoro vel
  ×1,15, dentro dos tetos; só no clone — Edge pura continua proibida); A = como sempre. postar.json "fala_rapida" = A | B.
- Medir: views 48 h / mediana do canal + pct_media/continuaram do lote (só elegíveis), ≥ 6 por braço por canal; placar
  `placar_cortes_testes.json` já conta a chave. A dona pode reprovar de ouvido: aí `fala_rapida: "A"`.
- Ajustes: `cortes_ajustes.json` `fala_rapida` = A | B | ab; `fala_delta` = pontos do B (15).
