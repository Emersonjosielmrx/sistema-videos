# Pendências do recap longo e Shorts — atualizado 31/10 noite (sessão claude-33)

## Para o agente do Telegram
Cada longo novo traz a versão no `pronto.json` (fila manhwa-drive:colab_recap/fila/<pid>/pronto.json), campo
`versao` = {"versao": "AAAA-MM-DD HH:MM", "mudancas": [{"desde", "item"}...]}. Gerado por colab/montar_pacote.py
(`_carimbar_versao`, lê config/mudancas_longo.json) e copiado pelo kaggle_trabalhador.py (VPS hermes-prod,
hermes-staging, hermes-bloqueio atualizadas 31/10). No aviso de "longo pronto"/"longo postado", mandar a versão e a
lista de mudanças que ele tem. Longos de antes disso não têm o campo (ver tabela abaixo).

## Estado dos longos (atualizado 01/11 01:30)
- PRONTO 31/10 ~23:40: 20261027_000050_SNhb31ZuuFA — 1º com as mudanças de 31/10 15:30 + 1080p + disco
  (log: 351 raios, 113 zoom múltiplo, 0 figurinha, 32 memes de imagem, 9 reações da mascote). versao=None no
  pronto.json (trabalhador antigo já carregado). NÃO tem upscale spline.
- Renderizando: 20261027_000800_VgQUQTmYLeQ (revolutionemerson, desde 01/11 00:21 BRT) — refeito com o código
  novo: deve ser o 1º com `versao` no pronto.json.
- Morto: 20261027_082355_cLF1aexIye0 — caiu 30/10 ~01:30 BRT em fx_clips.concat_with_xfade (Traceback no
  pipeline.log); em_andamento.json + em_andamento_emerson2032.json ficaram e seguram o pedido. Liberar = apagar
  esses 2 marcadores (esperando a dona confirmar).
- Com erro.json (não renderizam):
  - GFrKL-1J_xQ (000300): disco cheio no Kaggle 30/10 23:47 (mix da trilha, 5 h de render perdidas). O conserto do
    disco é de 31/10 → pode voltar pra fila (apagar erro.json; esperando a dona).
  - UYU3JWS5zu4 (111210): "original (source.mp4) não chegou" — o vídeo-fonte não foi enviado; reenviar pelo cliente.
- Achado: a trilha do GFrKL usou músicas de jogo/anime com dono (Naruto, JJBA/DIO, Pokémon, Megaman, Deltarune). O
  filtro de memes proibidos (fx_detect.meme_proibido) NÃO vale para a pasta de trilhas — decidir se filtra também.
- Prontos esperando postagem (todos SEM as mudanças de 31/10, todos em 720p — sobem pra 1080p na trava do postador):
  G1_iPga6nLg, yKfgs7SXOb0, bXe7-vR7o5M, ssMbrCz0fhE, X90-SNMMCdg, XNKCOSdfMrU, 6d2aEsFp6Qk, nV2aNVwUL-A, 4wufdzeZKgs
  (último pronto: 4wuf, 31/10 13:44 BRT).
- Último no YouTube público: 2jtdp4vB1WQ (CenaReact, 30/10). P-djtsSY2Co (Curiosidades Noturnas) agendado 01/11 12:30.
- Eco nos longos: a correção é de 29/10 23:31; os prontos começaram 30/10 06:21 BRT ou depois, mas o ssMb (06:21)
  saiu sem uma mudança de 30/10 (sprint do resumo) = o Kaggle pode ter usado código atrasado. NÃO dá pra provar pelo
  log se tem eco. Falta: ouvir/medir ou refazer.

## Incidente 31/10 23:11
Outra sessão (mudança "muitos avisos"/advertencias) regravou politica.py, youtube_web_poster.py e youtube_poster.py
a partir de cópia antiga e apagou a trava de 1080p — com isso os posters de TikTok/Instagram/Facebook/Kwai quebrariam
(importam politica.garantir_1080). Reaplicado às ~23:20 mantendo a mudança dela; avisadas claude-d0, claude-08 e
fluxo n8n. Conferir de novo: `grep -c garantir_1080 D:\postador-de-videos\bin\politica.py` tem que dar >= 2.

## Feito 01/11 madrugada (pacote no Drive ~02:40)
- Imagem presa na tela: anime_segments._desprender (cada corte anda >= 60% da fala anterior). Testado com os cortes
  reais dos 10 longos: ssMb 26 frases presas → 0, VgQU 16 → 0; atraso máx. 61 s atrás do roteiro. Render real: falta.
- Memes de série: arsenal_memes.py corta até o fim da frase (pontuação do Whisper), teto 10 s; modo `refazer`
  (mesmo vídeo-fonte, sem busca). Greg conferido por transcrição: "Cara, ela tá tão na sua!" (2,1 s). Os outros 23
  refeitos 01/11 02:33-03:44 e conferidos por transcrição. Fora do catálogo: moana_sou_moana (virou trecho cantado,
  música com dono) e julius_nao_comprar (pegou o Chris narrando) — arquivos *.ruim_01nov. pague_o_aluguel cortado
  na 1ª fala (1,9 s; o de 9,5 s ficou em *.longo_01nov). isso_isso_isso: frase não achada, ficou o arquivo antigo.
  Catálogo 22 memes, backup memes_series.json.bak_01nov. No Drive (montar_pacote ~03:50).
- Capitão Nascimento e Ei Nerd fora (ANIME_NARRA_PROIBIDA, teste_narradores, vozes_m, "fora" em narradores_nichos);
  modelos em manhwa-drive:vozes_arquivadas (rclone check ok) e apagados do PC.

- Dona deu ok 01/11 ~04:00: cLF1 liberado (marcadores apagados); GFrKL de volta na fila (erro.json → erro_30out_disco.json;
  pego na hora por aulacomia).
- Trilhas: anime-pipeline chamava add_dynamic_music(no_copyright=False) — a marca copyright_risk do moods.json era
  ignorada (GFrKL tocou Naruto, JJBA/DIO, Pokémon, Megaman, Deltarune). Agora True. moods.json: marca era
  inconsistente (marcada num clima e não em outro) — 112 faixas de franquia/artista marcadas e marca igual em todos os
  climas (backup moods.json.bak_01nov). Sobram livres: tenso 7, triste 3, romântico 3, engraçado 16, neutro 100,
  calmo 10 → baixar mais faixas sem direitos (Kevin MacLeod, NCS, biblioteca do YouTube) pra tenso/triste/romântico.

## PEDIDOS DA DONA 01/11 — LISTA VIVA (ela esquece o que pediu quando a prévia chega: TODA prévia leva "o_que_testar")
Prévia nova: colab\cliente.enviar(..., extra={"previa": True, "o_que_testar": [...]}) → ao chegar, cliente._o_que_testar
grava <video>_O_QUE_TESTAR.txt do lado e manda no Telegram com o MINUTO de cada novidade (marcas_visuais.json do
fx_subtitles, que volta em cortes_longo/ e no pronto.json["marcas"]). Modelo: D:\tmp_logs\cartoes_teste\enviar_previa3.py
FEITO (na PREVIA3 20261027_000003_PREVIA3nov, 01/11 ~13:40):
- cartões animados estilo comercial Instagram (bin\anime_cartoes.py; ANIME_CARTOES=0 desliga, GAP_S=9): personagem,
  lugar, sistema, chat, alerta, antes/agora, like — sempre em movimento. Teste local D:\tmp_logs\cartoes_teste (g3.jpg).
- decoração da legenda criativa desenhada (emoji saía quadradinho na nuvem: a pasta fonts não tem emoji)
- legenda criativa v3 (resumo inteiro 45 s, ênfase, esmaecer), intro real + mesmo narrador, transições líquido/whip,
  SFX m1oy, memes ≤ 6 s, Woody fora, concordância de gênero, 1080p60, mascote com roupa variada
FEITO 01/11 tarde: legenda MIX (bin\legenda_mix.py, porte do ms-energy montagem_ms; ANIME_LEGENDA_MIX=0 desliga;
  modo vai em marcas "legenda_mix_modo"); cartões VITÓRIA/GPS; visualizador: longos (tipo completo) só no DESKTOP
  (D:\visualizador + tarefa VisualizadorLongos, video-fila\desktop\visualizador_win.py), x200ma só curtos; dorama 1ª
  pessoa de mulher -> narradora (anime_script.narradora_feminina + anime_voz_clonada.genero_da_voz, troca em anime_auto);
  comentário pessoal/ironia do narrador 1 por trecho no longo (anime_script._COMENTARIO_NARRADOR, prompt v13).
FALTA na legenda MIX: desviar do rosto (anime: detector de rosto de anime, YuNet não pega desenho), não pôr legenda
  em cima de meme em tela cheia. FALTA no comentário do narrador: tom de voz próprio (clima) + balão visual "comentário".
FALTA (em ordem):
1. Mascote aparecer NA TELA quando a narração pede like (meio do vídeo) — hoje só a voz.
2. Mais aberturas reais (Momo etc.: intros_voz.py; só momo_1/2/3 + porao_3 sem CTA hoje).
3. Memes do 5l-8a1HLfkM (download falhou "format not available") → pasta pra dona escolher; memes do Laestro.
4. Aprendizado (claude-15, D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md): seta amarela [64e54485], flare divino em
   triunfo [b450f844], transição memória dupla exposição [edd839f7], mapa GPS em investigação [1e25c542] — flare e GPS
   cabem como cartões do anime_cartoes.
5. LONGOS_MELHORIAS.md (claude-15): L-05 abrir no choque, L-06 25-35 cortes no 1º min depois 12-15/min, L-07 pequena
   vitória < 8 min, L-09 narrador "parça", L-10 card "nome da obra no comentário fixado" ~5 min, L-11 tags, L-12 "- Completo".
6. Cartões animados nos Shorts de parceiro/cortes (hoje: longos e Shorts que saem dos longos via burn_subtitles_ass).
7. Teste A/B de capa: seletor do youtube_studio_extras teste_ab quebrado (options-button).
8. Kaijinre: variante de fala rápida; idiomas a ~25%; NVENC; trechos longos de SFX (sfx_06/07/09/14/16/17) como trilha.
9. Fila dos 14 vídeos da dona (01/11 ~11:45): YouTube pedindo "não sou robô" nas legendas — conferir quais entraram.

## 02/11 madrugada (chat dos longos) — FEITO / FALTA (retomar daqui)
FEITO e conferido no quadro:
- V-02/06/07/10/11/12 em bin\fx_visual.py (VISUAL_MELHORIAS.md JÁ FEITO). Bug do `negate:enable` (ffmpeg 8) que fazia
  a legenda MIX cair no PNG antigo nos Shorts: corrigido + 2ª tentativa sem efeitos. V-07/V-11 roxo/verde: blend só na
  luminância + format=yuv420p (rgbashift deixa o quadro em RGB planar).
- L-05/06/07/09/10/12 implantados (LONGOS_MELHORIAS.md, "IMPLANTADO 01/11 noite"): conferir no 1º longo real.
- Aprendizado 64e54485 (seta), b450f844, edd839f7 (memória), 1e25c542 marcados aplicados.
- 2 comentários do narrador por trecho (prompt v15).
- Mascote: reacao_viva nunca repete a FALA no vídeo; reação curta NO CANTO sem parar o vídeo
  (mascote_overlay.reacao_no_canto: trecho do meio da gravação + caixa do corpo, 58% da altura; quadro canto_58.jpg);
  conversa Maria x amiga (dupla_viva + anime-pipeline._memes_resumo); mascote_producao.py: 12 falas curtas novas +
  6 DUPLAS (amiga responde) — gravações chegam aos poucos pelo Veo.
- Cortes dos longos EM PÉ com legenda própria (MIX/cartões/efeitos): melhores_cortes.gerar(word_times=...) a partir do
  vídeo SEM legenda (anime-pipeline, antes de apagar); shorts_from_deitado.make_vertical_short(cheio=True). Teste:
  t2min\corte\corte_grade.jpg (1080x1920 60 fps). ANIME_CORTES_VERTICAL=0 volta ao antigo.
- Mascote muda do CURTIR no Kaggle: montar_pacote sobe mascote_waifu_v2\cosplay_recorte; fx_subtitles acha em RAIZ_WIN.
- Trava do Chrome (yt_web.lock): dono vivo > 2 h que não é upload = travado -> mata e solta (youtube_web_poster).
- Kaggle hermes-prod 1 -> 4 GPUs (gpus_por_saida; estava 1 desde 29/10 23:26 com 8 contas ok paradas). Pool igual nas
  4 centrais (md5 eea4b72a...). revolutionemerson3 (404 na API) e emersonjosiel02 (sem conta) = dona refaz.
- PREVIA5 (4 min, His Game Comes To Life) na fila do Kaggle: 20261027_000001_PREVIA5nov.
EM TESTE: Shorts de parceiro renderizados em LOTE no Kaggle — bin\lote_shorts_kaggle.py (PC manda pra
  manhwa-drive:colab_recap/fila_shorts) + colab\kaggle_trabalhador.py lote_shorts/fazer_short (linha paralela, igual aos
  comentários do claude-08). Liga: config\shorts_kaggle.json "ligado": true (parceiro_diario põe SHORTS_NO_KAGGLE=1).
  Só ligar depois de 1 Short real voltar do Kaggle (as sessões atuais rodam o código antigo; só sessão nova pega).
FALTA: conferir PREVIA5; ligar o lote depois do teste; cortes dos longos no lote (hoje saem dentro do longo no Kaggle,
  já não gastam o PC); L-11 tags; desviar a legenda MIX de rosto de anime.

## 02/11 ~09h10 — RENDER MAIS RÁPIDO NO KAGGLE (dona: "aplique logo o nosso maior problema: produção")
Pesquisa H6 (hipercool-materiais\pesquisa_github_02nov2026.md): no Kaggle a T4 só trabalhava no Applio; ~800 clipes 1
por vez e todo encode em libx264 nos 4 vCPUs (3-5 h por longo). Implantado (pacote no Drive ~09h10; vale pra sessão
NOVA do Kaggle):
- colab\sitecustomize.py (vira colab_traduz no Kaggle): com ENCODER_GPU=1, todo ffmpeg "-c:v libx264 -preset X -crf N"
  vira h264_nvenc -rc vbr -cq N+1 -b:v 0 -tune hq; passada da legenda (subtitles= no filtro) = -preset p6 + AQ +
  lookahead + B-frames; o resto = p2. Erro no NVENC = roda de novo com libx264 (nunca perde vídeo).
- colab\kaggle_trabalhador.preparar: testa NVENC de verdade (1 s 1080p60); passou = ENCODER_GPU=1 e
  ANIME_CLIPES_PARALELO=3.
- bin\anime_segments: ANIME_CLIPES_PARALELO=N -> clipes num ThreadPool (narração continua em ordem; resultado na
  mesma posição; falhou = sai da lista como antes). Testado no PC num Short real com 3: 6 clipes em 5 s (antes 13 s),
  mesmo vídeo (16,5 s, 1080x1920, quadro conferido).
- bin\fx_clips: detector de rosto (onnxruntime) e Depth-Anything (2.5D) na GPU quando houver; carga com lock
  (_CARGA) por causa do paralelo.
FALTA (próximos da H6, medir o 1º longo com isto antes): passada final em 4 fatias (-copyts), música/master só no
áudio, lanczos+cas no upscale, 1440p. CONFERIR no 1º longo: log "NVENC ok", tempo total, qualidade do quadro.

## Falta fazer
1. Mascote FALANDO nos Shorts (hoje imagem calada no canto). Plano: reação com voz (mascote_overlay.reacao_viva)
   recortada pro 9:16.
2. Longos prontos possivelmente com eco: decidir (ouvir trecho de clima terror/triste de cada, ou refazer).
3. Liberar o pedido travado cLF1 (e conferir o VgQU).
4. Balões: medir a triagem barata (estimativa +1-3%) se a dona quiser.
5. Memes de vídeo novos: dona dizer a fonte.
6. Testar com vídeo real: borrão só com legenda confirmada (parceiro_marca), travas 1080p de TikTok/Instagram/
   Facebook/Kwai (só compilado).
7. Outra máquina produz Shorts de parceiro em 30-31/10? Se tiver cópia própria do bin, atualizar.
8. NVENC (GPU do Kaggle) pra acelerar as passadas em 1080p — não testado.
9. Sentinela: ficou 1h10 sem rodar (18:01-19:11) com a CPU cheia pelas minhas medições de 1080p — não rodar
   medição pesada no PC1 sem limitar CPU.

## Feito hoje (detalhes em AUDITORIA_E_CORRECOES_31OUT.md, seções 1-8)
1080p em tudo (pipeline + postador + TikTok/Instagram/Facebook/Kwai), upscale spline+nitidez (VMAF 99,6), narradores,
vozes de personagem, raio/movimento/zoom múltiplo/transições novas, memes, SFX x voz, Maria+amiga, mascote reagindo,
meme de imagem em tela cheia, disco, eco desligado + 53 Shorts antigos segurados, borrão só com legenda confirmada,
Porão/Mike prioridade em anime, trilha audível nos Shorts, versão no pronto.json.
