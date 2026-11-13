# Recap LONGO (deitado) — melhorias trazidas dos Cortes e dos outros projetos

Pedido da dona (25/10/2026 ~07:00): "os vídeos de recap longos que estamos usando o Kaggle estão muito atrás dos
Cortes em efeitos, melhorias, narração — faça todas as melhorias possíveis; e acrescente tudo que fizer sentido dos
outros projetos nesses vídeos longos".

Sem Agent/Workflow (Opus = 429). Crons "continue" 08:03, 11:07, 12:09.

## Onde o longo é feito
- Colab/Kaggle/VPS: `colab\cliente.py alimentar` (PC1, fonte @Manhwa_Fresh) → fila no Drive → trabalhador
  (`colab\kaggle_trabalhador.py`, `colab\trabalhador.py`) roda `bin\anime-pipeline.py --formato deitado`. O
  trabalhador recopia `bin`, `config`, `secrets` do manhwa-drive a cada pedido (`colab\montar_pacote.py --codigo`).
- PC2/PC1: `bin\anime_auto.py fazer_deitado` (anime longo de busca).
- Shorts dos Cortes: `anime_auto.fazer_short` + `_reeditar_parceiro` (ANIME_FX_MOV=1, sem espelho no manhwa, voz
  clonada, CTA, gancho de retorno, roteiro com tempo, testes de formato).

## Diferenças achadas (longo x Cortes)
1. Câmera por trecho + tremida/flash no impacto (`fx_clips._movimento`, ANIME_FX_MOV) — só no Short.
2. Espelho (hflip) ligado no longo: na fonte de MANHWA (@Manhwa_Fresh) inverte o texto dos balões/painéis. Os Cortes
   desligam o espelho no manhwa desde 16/10.
3. Voz: longo = edge Thalita sem clone; Cortes = voz clonada (RVC) com curva v2.
4. Já iguais: curva de locutor + impactos, microcortes, música dinâmica, gancho na tela, master -14 LUFS.

## Defeitos achados e consertados (25/10 07:10–07:35)
- [x] 2 trabalhadores no MESMO pedido (Kaggle + VPS staging pegaram o 76SY no mesmo segundo: 2 renders iguais).
  Agora `_pegar` (kaggle_trabalhador.py e trabalhador.py da Colab): marca própria em_andamento_<quem>.json + o
  em_andamento.json de sempre, espera 15 s e quem marcou depois desiste. Marca velha de sessão que caiu é solta.
  Deploy: as 3 VPS reiniciadas 07:23 com o código novo; o Kaggle relança sozinho com o novo quando a sessão acabar
  (tarefa nova KaggleRecapManter, 30 min).
- [x] Longo do Kaggle (vMyOmvaaFIk) narrou 582 frases por 2 h com TODOS os cortes falhando (rc=254, original
  ilegível). Agora: o alimentador confere o original com ffprobe antes de mandar (quebrado = baixa de novo); o
  trabalhador recusa na hora original ausente/pequeno; o anime_segments para se não lê a duração; o fx_clips loga o
  motivo do ffmpeg (antes ia pro lixo).
- [x] Pasta órfã no Drive (2º trabalhador terminando depois do recolhimento) → o alimentador limpa.
- [x] Nas VPS (ffmpeg 7.1) TODO longo perdia as transições e a legenda exata: o xfade recusava a entrada ("inputs
  needs to be a constant frame rate; current rate of 1/0") e caía no concat simples ("offsets (0) != clips (903) —
  legenda cai na estimativa"). fx_clips._render_xfade_segment: fps= no fim de cada trecho e depois de cada corte seco.
  Testado no contêiner da VPS (ffmpeg 7.1) e no Windows (ffmpeg 8.1): 6 clipes, posições medidas, 19,0 s.
- [x] Whisper só transcrevia os 25 primeiros minutos (max_seconds=1500): o 76SY (original 2h18) virou 903 frases
  feitas só com o começo, espalhadas por 2h18 de imagem (narração do cap. 1 em cima do cap. 50). E o PC1 a 100% de CPU
  levou >10 min pra 6 min de áudio. Agora: sem legenda do YouTube, o alimentador manda só o original e o TRABALHADOR
  transcreve o vídeo inteiro (bin\anime_preparo_longo.py, chamado pelo anime-pipeline quando falta o roteiro;
  faster-whisper instalado na hora, áudio lido sem PyAV; 'base' até 40 min, 'tiny' acima). Testado no contêiner da
  VPS: 6 min de áudio em 235 s (base, 4 núcleos), 33 frases com tempo. O roteiro feito lá volta pra ficha do PC.
  PC2/PC1 (anime_auto, anime_worker_daemon): Whisper do vídeo inteiro.

## Melhorias de qualidade (25/10 08:00–09:35)
- [x] Roteiro LONGO com tempo (anime_script.rewrite_longo_com_tempo): cada frase marcada com o segundo do original
  que ela narra, em blocos fiéis (mesmo jeito do Short dos Cortes). Teste real: 70 frases, uma a cada ~5 s, sempre em
  ordem; amostra renderizada com "cortes pelos tempos do roteiro" e a imagem batendo com a fala.
- [x] config\longo.json + anime-pipeline._perfil_longo: todo longo com a câmera dos Cortes (ANIME_FX_MOV: zoom/pan por
  trecho + tremida/clarão no impacto) e manhwa sem espelho (tipo no pedido pelo canal, ou "manhwa/manhua/webtoon" no
  título). Custo medido na VPS: ~0,45 s de render por segundo de trecho (sem câmera era ~0,55 s): desprezível.
- [x] Amostra (VPS staging, 10 frases): perfil aplicado, gancho, legenda palavra a palavra, master -14 LUFS, xfade sem
  cair no concat. Quadros em D:\tmp\teste_longo\quadros\mosaico.jpg.
- [x] No ar: montar_pacote --codigo 09:28 (bin+config no Drive; cada trabalhador recopia no próximo pedido);
  VPS staging e bloqueio com o kaggle_trabalhador novo (09:33); prod segue renderizando o vMy (atualizar depois);
  alimentador religado 09:34 (roteiro ruim de 25 min do X90 guardado como .velho_25min pra ser refeito).
- [x] CTA no longo (config\longo.json "cta"): 1 pedido de inscrição depois da 4ª frase + 1 no fim, só em português,
  herdando o tempo da cena. Testado (inserção e tempos; roteiro curto não ganha).
- [x] Capítulos: o anime-pipeline grava capitulos.json (1 a cada ~7 min, 4 a 12, títulos pela IA em JSON) com as
  posições reais das frases no vídeo final; trabalhador devolve, alimentador põe na ficha, anime_publish põe
  "Capítulos:" na descrição (H:MM:SS acima de 1 h). Teste real: 0:00 O Desafio do Cristal Mágico | 7:30 O Despertar
  do Poder Oculto | 15:00 Acertando Contas com o Passado | 22:30 Poder Novo e Descrença Geral.
- [x] No ar 09:43 (pacote + staging/bloqueio + alimentador). 09:46: o vMy, que a prod renderizava desde 08:13 com o
  roteiro do Whisper de 25 min e o código antigo, foi refeito: roteiro ruim tirado do pedido, tipo manhwa posto no
  pedido.json, prod reiniciada com o código novo (o trabalhador transcreve o vídeo inteiro).

- [x] 10:28 — 1º longo real pelo caminho novo (vMy, VPS prod, 2 CPUs): Whisper tiny do vídeo INTEIRO (80 min, até
  4816 s; antes parava em 1496 s) em 2214 s; roteiro com tempo 796 frases (24 blocos, 0 sem marca). Render seguindo.
- [ ] CONFERIR quando o vMy terminar (~12:00): no pipeline.log da prod (/w/trabalho/20261025_075900_vMyOmvaaFIk ou
  manhwa-drive:colab_recap/fila/<pid>/pipeline.log): "[longo] fonte tipo manhwa; perfil", "[longo] CTA", "cortes pelos
  tempos do roteiro", "xfade lotes" SEM "lote N falhou"/"offsets (0)", "[longo] N capítulos", "PRONTO"; depois o
  alimentador recolhe → ficha D:\hipercool-materiais\animes recap\na_nuvem\vMyOmvaaFIk_* com roteiro.txt e
  capitulos.json; puxar 6 quadros do vídeo no Drive (videos-backup/anime/1_youtube_pendente/vMyOmvaaFIk_*/video.mp4)
  e olhar: texto dos balões sem espelho, câmera, legenda batendo com a fala.
- [ ] Mesmo conferir o X90-SNMMCdg (enviado 09:48 sem roteiro, sem legenda do YouTube).

## Legenda da fonte, borrão e tarja de capítulo (25/10 13:00–14:20, sessão claude-21)
Dona: "não tem legenda e não tinha por que ter borrado ... o borrão só quando há legenda, detecção boa como a dos
Cortes (tarja com título em cima, legenda em outro lugar); no longo a tarja muda numa taxa ideal, como apresentação de
capítulo; os já feitos ficam, os próximos não podem sair assim".
- [x] Causa: anime-pipeline, sem "tem legenda" da visão (3 quadros) ou com falha dela, borrava o rodapé do vídeo
  inteiro. Conferido nos quadros: 5 de 6 longos prontos borrados sem legenda (4 Manhwa_Fresh + Goku vs Saitama).
- [x] bin\anime_legenda_fonte.py: ~100 quadros do vídeo inteiro; linha de texto claro CENTRALIZADA (±3%) na mesma
  altura em >=12% dos quadros e que muda = legenda; 5-12% = IA de visão decide; sem resposta = não borra; texto parado
  (logo/título fixo) e tela cheia de texto descartados; legenda em 2 alturas = cobre as duas. Calibrado em 19 fontes
  reais (D:\tmp\legenda_teste\calibrar.py): 19/19. ~45 s num vídeo de 1h20. Cache <video>.legenda.json.
- [x] Borrão (fx_clips) agora na FONTE, antes do espelho/corte: antes caía ~4% acima da legenda deles.
- [x] bin\anime_tarja_capitulo.py: com legenda na fonte, placa branca (Impact preto) com selo "CAPÍTULO N" + título
  cobrindo a faixa; a cada capítulo pisca amarelo, selo estala, título sobe; nossa legenda logo acima. Vai no ASS da
  legenda (sem passada extra). Capítulos (descrição + tarja) a cada 5 min (config\longo.json "capitulos").
- [x] Defeito achado: fx_subtitles.burn_subtitles_ass reusava o nome "extra" no laço (23/10) e apagava o parâmetro:
  NENHUM longo desde 23/10 tinha gancho no início nem barra de progresso. Consertado.
- [x] Linux (Kaggle/VPS/Colab) sem Impact: legenda saía em DejaVu. subtitles=...:fontsdir=assets/fonts (testado no
  recap_worker da staging).
- [x] No ar 14:20 (montar_pacote --codigo). Os 4 longos que já estavam renderizando seguem com o código antigo.

## Pendente (próximas rodadas)
- Câmera (ANIME_FX_MOV) NÃO entra no deitado: fx_clips só chama _movimento no ramo vertical nativo (conferir antes de
  contar como feito).
- Voz clonada no longo: os Shorts usam RVC (Applio + vozes ~11,5 GB, fora do pacote da nuvem); os trabalhadores são
  CPU e RVC em CPU somaria 1–2 h por longo. Caminho: converter as falas do longo na GPU do Kaggle (gpu_fila /
  kaggle_conversor.py, que já faz isso pros Shorts) — exige separar a narração do render.
- Abertura com voz humana (hipercool intros_voz): NÃO se aplica — o @Manhwa_Fresh não está entre os 15 autorizados
  (config\intros_voz.json, conferido 25/10 11:10; regra da dona: só eles).
- 11:06: vMy 371/798 frases narradas (prod, 2 núcleos; fim ~13:00); X90 (bloqueio, 71 min transcritos inteiros, 921
  frases com tempo) e ssMb (staging, 97 min, 1123 frases) renderizando; cada VPS com um pedido diferente.
  Conferência agendada 13:23.
- Shorts derivados do longo (shorts_from_deitado.py) só existem no caminho do PC; no Kaggle não.
- Kaggle ainda roda o trabalhador antigo até a sessão acabar; KaggleRecapManter relança com o testado.
- Trabalhador "robustez" da claude-21 (colab\kaggle_trabalhador_ROBUSTEZ_nao_testado.py): NÃO está no ar; o ativo é o
  testado (kaggle_trabalhador_NO_AR.py + volta do roteiro pra ficha).

## Frentes
1. [ ] Perfil do longo por config (config\longo.json) lido pelo anime-pipeline (vale em Kaggle/Colab/VPS/PC).
2. [ ] Sem espelho quando a fonte é manhwa (tipo no pedido + palpite pelo título).
3. [ ] Câmera por trecho + impacto no longo (medir custo de render antes).
4. [ ] Narração: ver o que dá pra levar (clone na nuvem? ritmo, CTA, abertura).
5. [ ] Outros projetos: título/descrição/capítulos/capa/mid-roll no caminho Kaggle → postagem.
6. [ ] Render de amostra antes/depois + quadros conferidos.
7. [ ] Publicar o código pros trabalhadores (montar_pacote --codigo; PC2 sincronizar_bin).

## 30/10 tarde (sessão claude, pedido do dono: "melhorias nos longos")
- [x] Mascote: a fala da gravação agora casa com o ponto do vídeo (mascote_overlay.pausa_viva posicao=inicio/meio/fim
  + usados). Abertura não diz mais "se você chegou até aqui"; o fim não diz "até agora". Sem gravação que combine, o CTA
  sai com a voz clonada de antes. Não repete a mesma gravação se houver outra.
- [x] Pausa da mascote no fim do original: recua o corte pra cena não congelar (montar_pausa).
- [x] fila_dona.py recolher: não chama mais preparar() (que podia baixar o original de novo), copia capitulos.json e
  roteiro.txt da fila e MOVE o pronto dentro do manhwa-drive (antes baixava ~1 GB e subia de novo).
  capitulos.json refeito pelo pipeline.log no P-dj (ainda não postado) e no LAei (já no ar sem capítulos).
- [x] cliente.preparar: fonte com manhwa/manhua/webtoon na descrição/tags/canal = tipo manhwa no pedido (sem espelho).
- [x] postar_longos: "vid" com 11 caracteres (RRrhPp_qeCA virava RRrhPp); duração dos já postados preenchida pelo Drive.
- [x] postar_cortes com teto de 6 cortes por canal por DIA (est["cortes_dia"]), além dos 2 por rodada.
- GARGALO (decisão da dona, não mexido): 13:23 de 30/10, 10 de 14 canais no "limite diário do YouTube" renovado às
  13:05 — os Shorts pegam a vaga assim que ela solta, então rodar a RecapPostarLongos mais vezes não resolve. Longo só
  sai se tiver prioridade na politica do postador (reservar 1 envio/dia por canal pro longo).

## 25/10 tarde
- [x] Câmera no longo: o _movimento só entrava no vertical nativo (achado da claude-21) — agora também no deitado, ancorado no centro da faixa da legenda borrada. Testado (zoom e clarão medidos por diferença de quadros). No ar 14:5x.
- [x] Dona: render só no Kaggle; VPS não renderiza (containers param depois do vídeo atual). PC prepara, NÃO fala com o Kaggle: cliente.enviar manda o pedido pra hermes-prod:/opt/recap_central/entrada; vps_central.py (cron 5 min) repassa pra fila, relança o Kaggle, página de % e Telegram. KaggleRecapManter do PC desabilitada.
- Página: https://produtos.opus-sem-limites.com.br/<pagina em /opt/recap_central/config.json>/
