# Melhorias nos Shorts (Cortes) — 30/10/2026

Pedido da dona: "analise profundamente e faça todas as melhorias possíveis, principalmente nos vídeos curtos".
Análise feita por 5 frentes (só leitura) e gravada em `D:\tmp\analise_shorts_20261030\`:
`pendencias.md` (docs do Fable × código), `videos.md` (6 Shorts prontos inspecionados quadro a quadro),
`views.md` (321 Shorts com views medidas), `falhas.md` (130 falhas de produção casadas com os logs), `bugs.md`
(revisão do caminho do Short). Cada mudança abaixo tem o comentário `30/10` no código.

Backups: `bin\<arquivo>.bak_20261030_1340_shorts` (anime-pipeline, anime_segments, anime_auto, anime_script,
cortes_mascote, fx_subtitles, anime_fetch), `bin\anime_gancho.py.bak_20261030_shorts`,
`bin\cortes_melhorador.json.bak_20261030_shorts`, `config\seo_palavras.json.bak_20261030_shorts`.
Sem backup (desfazer pelos blocos `30/10`): `parceiro_marca.py`, `parceiro_diario.py`, `_whisper_sub.py`.

## O que mudou

### Vídeo quebrado que saía e era publicado
| # | Defeito (prova) | Correção |
|---|---|---|
| 1 | Short sem legenda, sem gancho e sem barra quando a queima da legenda falhava por RAM (5x nos logs; com delogo o vídeo ficava sem nenhum texto) | `anime-pipeline.py`: no vertical espera RAM (`fx_clips._wait_for_ram`) e tenta 1x; se falhar, o Short **não sai** |
| 2 | Frases sem áudio puladas em silêncio: 28/10 QjidaJbpEx4 saiu com 1 de 10 frases (4 s) e foi publicado; 76 frases puladas nos logs | `anime_segments.build_segments`: no vertical, faltou frase = devolve vazio e o Short não sai |
| 3 | Cobertura do parceiro falhava (MemoryError / WinError 1455) e o Short saía no NOSSO canal com a @ e a legenda deles (6x) | `anime_auto._reeditar_parceiro` devolve `None`; `fazer_short` espera RAM, tenta 1x e, se falhar, registra FALHA. O T2 (`CORTES_COBERTURA_USADA`) só é gravado depois de cobrir de verdade |
| 4 | Fim do Short com o mesmo plano repetido ("55 54", "70 70", "56 57 58") — o teto "cabe no original" vinha depois do "nunca volta" | `anime_segments._inicios`: passada de trás pra frente, cada corte termina antes do próximo; adianta a imagem no máximo 8 s (a fala pode vir antes da cena, nunca depois). Testado: `0 10 20 50 55 56` → `0 10 20 43.9 49.9 56` |
| 5 | Gancho dos 3 s escrito em cima da nossa legenda quando a legenda deles fica no alto (centro 0,12/0,21 em 29/10) | `anime_auto._reeditar_parceiro`: legenda nossa acima de 0,40 → `GANCHO_Y = centro + 0,09` |
| 6 | Delogo de 35–50% da tela = "vidro derretido" o vídeo todo (betinha, gta-rp) | `parceiro_marca.py`: `DELOGO_MAX_H = 0.12`; faixa maior não leva delogo nem borrão nem tarja (a nossa legenda entra em cima da deles) |
| 7 | Instrução da IA narrada no Short (sem-obra-54b88d: "envie a transcrição… no estilo do…") | `anime_script._RX_ERRO_IA` pega pedido de material/prompt; testado contra os 89 roteiros publicados: 0 falsos positivos |
| 8 | 1ª fala de enchimento ("E aí, galera", "Minha gente", "Ah, mon") | `anime_script._tirar_abertura_vazia`: tira a saudação (com pontuação depois) e, se não sobrar fato, a frase |
| 9 | Mascote do T7 nos cantos de baixo/direita = debaixo da UI do Shorts | `cortes_mascote._canto`: cantos entre 0,06 e 0,84 da altura e até 0,88 da largura |

### Duração (o dado mais forte de views)
Elegíveis de 18–27/10: < 30 s passam de 65% assistido em 8 de 12 e chegam a 1.500 views em 4 de 12; 60 s+ em 2 de
34 e 0 de 34. 26 Shorts saíram com 90–220 s.
- `anime_auto.fazer_short`: teto de frases do parceiro 18 → **10** (~55 s). O braço B do T8 (4–5 frases) não muda.
- `anime_script.rewrite_curto_com_tempo`: pede "NO MÁXIMO N" (era "aproximadamente"); veio com mais de N+1 → pede
  de novo 1x; ainda longo → fica com as N-1 primeiras + a última. (T8 B pedia 5 e recebia 6–10.)

### Falhas de produção
- Fonte reaproveitada era o pedaço parcial do yt-dlp (`source.f396.mp4`, sem áudio): `anime_auto._prepara_candidato`
  e `anime_fetch` só aceitam `source.mp4|mkv|webm` e apagam `source.f*`.
- Whisper rc=1 ao carregar o modelo (7x): `_whisper_sub.py` acha a pasta que tem o modelo (producao\models,
  bin\models, cwd) e carrega com `local_files_only`. Testado chamando de `C:\`.
- Erro do Whisper no log: fim do stderr (800 caracteres), não o começo (que era só aviso).

### Views / SEO
- Piso de views da fonte: `anime_auto.main` põe primeiro os candidatos com ≥ 100 mil views (abaixo: 11% chegam a
  500 views, contra 30%, p 0,002). Fonte sem nenhum acima do piso segue como antes. `PISO_VIEWS_FONTE=0` desliga.
- Horário: `parceiro_diario._ordem_horarios` manda 15–21 h de Brasília pro FIM da fila nos canais em pt (13% contra
  33% chegam a 500; pior em 9 de 9 canais). Só enchem se sobrar Short no dia. `HORARIO_FRACO_BR=""` desliga.
- Título: 29 dos últimos 150 abriam com "NINGUÉM ESPERAVA" (exemplo do prompt virou fórmula).
  `config\seo_palavras.json` (estilo provocação) e `anime_gancho.gerar_gancho` pedem o fato da história e proíbem
  essa abertura.
- Melhorador: os testes A/B (gancho_remotion, mascote, fx_choque, gancho_meio, legenda_impacto) saíram das alavancas
  do `cortes_melhorador.json` — D6/CORTES_01: teste só se decide por views dos elegíveis, nunca pela nota do júri.

## Achados que ficaram para a dona/Fable decidir (não mexi)
- **Cortar ~30% da produção sem retorno**: Dorama Noturno (0 elegíveis em 26), canais id/th/ru/hi (0 com 500+ em 47),
  fontes grananerd-k3r e king_chan01 (0 em 13 cada). Passar as vagas para Esporte, Filme, Curiosidades e
  CodigoInteligente. Números em `views.md`.
- **Placar dos testes** (`placar_cortes_testes.json`) não existe e o `notificar_telegram` conta todo vídeo (inclusive
  sem lote): sem ele nenhum teste T3–T9 pode ser decidido. T5 e T7 estão enviesados (braço A = falha de render).
- **Download pelo Kaggle** (`kaggle_baixar.py`, pronto, de outro agente) não está ligado: ligaria quando o IP está
  em pausa (hoje ~4 h paradas em "espaçando downloads"). Legenda do YouTube morta desde 22/10 (disjuntor com 80
  falhas) → todo Short passa no Whisper do PC1.
- Selo/logo em imagem do canal original ainda escapa da detecção (só texto é achado): VORIN, Maresia, KAIJINRE.
- `anime_health_monitor` diz "Tudo OK" porque não lê os `_parceiro_*.log` nem o `pipeline_metrics.jsonl`.
- B1/B2 (`bugs.md`): com cobertura "tarja", a nossa legenda cai em cima da tarja. Dormente enquanto for "delogo".

## Virais nos canais fracos (30/10, pedido da dona)
Pedido dela: "postar nesses canais que não dão visualizações os vídeos que viralizam nos outros; se um tipo de vídeo
ou um parceiro não dá visualizações, aí sim nós cortamos". Canal nenhum foi desligado.

**1. A gente produz mais do que consegue postar? Sim.**
- 23 a 29/10: **53,9 Shorts produzidos por dia x 40,7 enviados por dia** (ledger, projeto parceiro). Sobram uns 13 por dia.
- Hoje há **116 Shorts prontos esperando**, cerca de 2,8 dias de envio. Outros 24 foram reprovados e 14 bloqueados.
- O que trava é o **"limite diário de envios" do YouTube**: 1 canal bateu nele em 19/10, 7 em 28/10, 10 em 29/10 e
  14 em 30/10. Dicas financeiras e ForjaReact passaram 9 dias no limite, Curiosidades Noturnas e Fio da Meada 8,
  CartuchoReact 6. Em 7 dias esses 5 canais subiram 0, 0, 0, 3 e 8 Shorts e têm 10, 7, 6, 9 e 8 prontos parados,
  alguns há 5 a 8 dias. O `fila_alvo` já para a produção desses canais quando a fila enche, mas o estoque fica
  parado. Ele leva o @ do canal gravado, então não dá para mandar para outro canal.
- Os outros canais param na **cota de 4 por dia do postador** ("cota do dia 0": Dorama, Assist-IA, Esporte, Bicho,
  Game e Mistérios todo dia). As línguas estão com a semana cheia (1 por dia, 7 dias agendados).
- Como já se produz mais do que sobe, a versão do viral **ocupa o lugar** do Short comum (sai na frente da fila do
  canal fraco). Ela não acrescenta envio.
- Números: `D:\tmp\virais\q1.py`, `q1b.py` e `q1.out`.

**2. Viral num canal vai para o canal fraco (`bin\virais_fracos.py`, novo)**
- Viral: Short nosso com **1.500 views ou mais no placar de 48 h** (`medidas_48h`), publicado nos últimos 12 dias,
  cuja fonte de parceiro está no `parceiro.json`. Hoje são 13, todos de fatos, esportes, filme, dorama, anime e pesca.
- Canal fraco: pelo menos 5 Shorts medidos em 21 dias, **mediana abaixo de 100 views e no máximo 10% com 500+**.
  Hoje são Dorama Noturno, Manhwa Noturno, InventoReact, Assist-IA e as línguas id, th, hi, ru e it. Fica de fora o
  canal que está no limite do YouTube ou que tem Short pronto parado há mais de 4 dias.
- O Short não é subido de novo. O `anime_auto` **refaz o mesmo vídeo da fonte** (`--fonte <canal do parceiro>
  --id <vídeo>`, o mesmo caminho do PC1 para o PC2) com o @ do canal fraco, gerando roteiro, narração e título novos.
  A narração segue o tipo da fonte. Cada produção gera 1 versão em pt e as línguas fracas que couberem (no máximo 3
  canais por viral).
- Nicho: primeiro vai o canal fraco do mesmo nicho. Os de outro nicho entram como teste (`aceitar_outro_nicho`, a dona
  aceitou testar). As versões se dividem entre os canais fracos conforme quantas cada um recebeu em 7 dias.
- O `postar.json` novo leva `viral_de`. Com isso o `parceiro_diario.postar` deixa a versão subir mesmo com a fonte já
  postada em outro canal, e ela sai antes do Short comum. O Short comum com fonte repetida continua segurado.
- Mudanças em `parceiro_diario.py`: `_rodar_auto` (novo `video_id`, que vira `--id`), `producao` (chama
  `virais_fracos.rodada(c)` antes da produção normal; se der erro, a produção normal segue), `postar` (exceção do
  `viral_de` e ordem da fila) e `_escolher_fonte` (campo `peso`). **Não mexi em `_ordem_horarios`, `anime_auto`,
  `variantes` nem `cortes_ajustes`.**
- Config `parceiro.json` → `"virais_fracos"`. **Modo: `ligado`**, com 1 por rodada e no máximo 3 por dia. Antes de
  ligar, o ensaio mostrou 13 produções possíveis; 11 das 13 fontes estão na lista guardada do parceiro (thalisshortsbr
  ainda vai ser listada). No teste em memória do `postar --ensaio`, a versão viral passou e saiu primeiro, e a cópia
  sem `viral_de` ficou segurada. Para voltar, use `"modo": "ensaio"` (só registra) ou `"desligado"`.
- Acompanhar: `python bin\virais_fracos.py --ensaio` mostra os virais, os canais fracos, o plano e as **views em 48 h
  das versões já feitas**. Registro em `logs\virais_fracos.jsonl` e `workspace\anime\_virais_fracos.json`.
- Atenção: as línguas já têm 7 dias agendados, então a versão viral delas só sobe quando abrir vaga (até cerca de 7
  dias).

**3. Cortes (somente onde o dado mostrou; placar de 48 h, Shorts do parceiro, 21 dias; `virais_fracos.py --fontes`)**
Campo `peso` na fonte, com o motivo em `_peso_obs`. Para desfazer, apague o campo. Backup em
`parceiro.json.bak_20261030_virais`.
- `king_chan01`: peso 0,2. 13 Shorts, nenhum com 500+, máximo de 11 views, 39 no total.
- `grananerd-k3r`: peso 0,2. 15 Shorts, nenhum com 500+, máximo de 128. É a única fonte de finanças, então o peso só
  faz efeito quando entrar outra. Por enquanto a troca no Assist-IA vem das versões virais.
- `drameela`, `jresumos`, `d_UCJ4ZMy` (dorama), `a_UCbYDJC`, `nerdcf`, `a_UCHCxgk` (anime): peso 0,4. Cada uma tem
  4 ou 5 Shorts e nenhum com 500+. As de dorama ficam com no máximo 10 views. No rodízio passam na frente
  d_UCSJ6_g (que tem o viral de 1.827) e as fontes ainda sem medida.
- `cidademaresiarp` (jogos): peso 0,5. 17 Shorts, 1 com 500+ (6%), mediana 21.
- Não cortei por enquanto: o **tipo dorama** (7%, mas d_UCSJ6_g rende), **financas** (0% em 15 Shorts, só que o
  Dicas financeiras rende com dorama e esportes pelo funil de nicho) e o **kaijinre** (15% em 93 Shorts, e dentro do
  canal ele não é pior). Os canais Dorama Noturno e id/th/ru/hi não foram cortados: eles passam a receber as versões
  dos virais no lugar do conteúdo que não rende. O dado para cortar canal é rever em cerca de 7 dias, com as views
  dessas versões.
