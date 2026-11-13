# Auditoria e correções do recap longo — 31/10/2026

Pedido da dona (CCJQvNP-23Y e longos recentes): narrador principal saía em ~1 min e trocava demais; Galvão com chiado
como narrador; Kratos grave demais; voz do personagem mudava; raio pouco usado; paisagem parada; zoom múltiplo;
Roda Regina e memes com música; figurinha de canto ruim; SFX tocando junto da voz; Maria + amiga no mesmo lugar,
tamanhos diferentes, parada e sem som da amiga.

Estado: **tudo aplicado, testado em arquivo real neste PC e subido pro Drive** (`colab/montar_pacote.py --codigo`,
31/10 ~15h30). Vale a partir do próximo pedido que o Kaggle pegar. **Ainda não verificado num longo inteiro
renderizado no Kaggle** — conferir o 1º longo novo (itens em "Como conferir").

Amostra pra ver: `D:\hipercool-materiais\recap_amostras\amostra_correcoes_31out.mp4` (30 s): pan antigo → pan
suave → zoom múltiplo → transição do raio → pausa Maria + amiga.

---

## 1. Narradores (revezamento)

Causa: `bin/anime_tts._inicios_blocos` fazia o 1º bloco = resumo + 12 frases e os seguintes crescendo em progressão
geométrica (o último narrador ficava com o maior bloco). No CCJQ: 5 vozes, Galvão no fim com o maior pedaço.

Correção:
- `bin/anime_tts.py`
  - `_inicios_blocos`: 1º bloco = max(35% do vídeo, parte igual, resumo + 12); o resto dividido igual.
  - `_separar_vozes`: tira vozes proibidas (`ANIME_NARRA_PROIBIDA`: Kratos x2, Patrick), separa as de
    **participação especial** (`ANIME_PARTICIPACAO`: Galvão, Chaves, Chapolin, Seu Madruga, Chiquinha, Pica-Pau,
    Gretchen), no máx. `REVEZ_MAX`=5 principais e 2 participações. Se só sobrar participação, narra 1 que não seja o Galvão.
  - `_janelas_especiais`: cada participação = 3 frases (`REVEZ_ESPECIAL_LINHAS`) no meio de um bloco, na 2ª metade do
    vídeo, longe das trocas.
  - `revezar`: reescreve cada trecho no jeito do dono dele e faz a cena de passagem em TODA troca (inclusive entrada e
    saída da participação).
- `colab/cliente.py` `_narradores_por_grupo`: corta em 5 vozes e acrescenta 1 participação especial em 1 de cada 3
  vídeos com mais de 1 narrador (sempre nos modos com_terciarios/mistura_grande).
- `colab/teste_narradores.json`: Kratos em `ruins`; Cid Moreira subiu pra `secundarios`; Cassidy (grave) saiu dos
  secundários; novo grupo `participacao_especial`; esses nomes saíram de `terciarios`.
- `config/longo.json` efeitos: `REVEZ_PRIMEIRO_FRAC`, `REVEZ_MAX`, `REVEZ_ESPECIAL_LINHAS`, `ANIME_PARTICIPACAO`,
  `ANIME_NARRA_PROIBIDA` (a lista de participação está em 2 lugares: longo.json e teste_narradores.json — manter iguais).

Teste (IA trocada por função vazia, só a divisão):
```
mesmas 5 vozes do CCJQ, 420 frases: solemsun 147 | cassidy 112 | chaves_chapolin 3 | cassidy 22 | cid 24 | galvao 3 | cid 109  (6 trocas)
momo,mike 300:      momo 150 | mike 150
8 vozes c/ Kratos:  momo 175 | vegeta 81 | walter 82 | mike 11 | chaves 3 | mike 67 | iki 81  (Kratos fora, 6 trocas)
```
8 sorteios do cliente: no máx. 5 principais + 1 participação.

Não feito: filtro de chiado no áudio do Galvão (ele agora só fala 3 frases; se ainda incomodar, pôr `afftdn` só nas
frases dele em `preparar_revezamento`).

## 2. Vozes dos personagens

Causa: a voz era fixada pelo nome cru que a IA devolvia ("Garota", "a garota", "Lia" = 3 personagens/vozes) e o
1º homem (protagonista) pegava `vozes_m[0]` = Kratos.

Correção:
- `config/longo.json` `personagens`: Kratos saiu de `vozes_m`; novo `vozes_monstro: [kratos_god_of_war_2018]`.
- `bin/anime-pipeline.py`:
  - prompt de `_falas_personagem` pede o MESMO nome sempre e `papel` (protagonista/aliado/vilao/monstro);
  - `_nome_personagem`: sem acento/artigo/maiúscula, só o 1º nome ("Kai Shin" = "Kai"), apelido genérico
    (garota, protagonista, ele...) = 1 personagem por gênero;
  - voz grave só para `papel=monstro` masculino; log `voz de cada personagem: {...}`.
- `colab/cliente.py` e `colab/corrigir_pedidos_fila.py`: `vozes_monstro` entra no download das vozes.

Teste: `Garota`/`a garota` → `_protagonista_f`; `Kai Shin`/`Kai` → `kai`; `A Guerreira` → `guerreira`.

**Ler/traduzir balões — NÃO implementado (a dona pediu medir antes).** Estimativa, não medida: 1 chamada de visão por
cena com balão (~3-7 s cada, como o zoom em objeto) ≈ 600 frases × 5 s ≈ 50 min a mais por longo se for em toda frase;
cada fala de balão narrada soma ~2-3 s de vídeo. Para medir de verdade: rodar o detector de objeto
(`fx_clips._objeto_no_trecho`) com pergunta de balão em 30 trechos de 1 longo e cronometrar. Aguardando a dona decidir.

## 3. Transição do raio + câmera

- `ANIME_FX_DIVISORIA_CADA` 6 → 3 (raio a cada 3 trechos).
- `bin/fx_clips._movimento`:
  - `ANIME_FX_SUAVE=1`: trecho sem rosto e sem impacto anda com aceleração/freio (cosseno) e flutua de leve
    (seno, limitado à folga do zoom).
  - `ANIME_FX_MULTIZOOM=1`: 3 zooms secos seguidos (cada degrau +0,22 em 3 quadros, segura 5; termina em 1,66×)
    mirando o rosto/objeto, 1 a cada `ANIME_FX_MULTIZOOM_CADA`=6 trechos com alvo. Log `[multizoom]`.
  - Observação: o rosto é achado pelo YOLO (onnxruntime) — existe no Kaggle, não neste PC; aqui o teste usou o rosto
    marcado à mão.
- Teste: quadros do zoom em 0,05/0,3/0,55/0,9 s mostram os 3 degraus; raio conferido em 16:9.

## 4. Memes

- `bin/fx_detect.py`: `MEMES_PROIBIDOS` (regex: regina, remix, funk, mc, hino, abertura, opening, tema, theme,
  official, música/music, song, cover, karaokê, ft./feat, clipe) + `meme_proibido()`; aplicado em `_valid_audio`
  (todo SFX/meme de áudio) e no banco por clima.
  Medido: bloqueia 14 de 904 sons — Roda Regina, Banana Song, abertura do PS2, Sonic, Sad Music 1/2, Música do
  Chaves funk, Que coisa mais fofa (Official), bora-bill-musica, Cartoon Music.
- `bin/memes_visuais.catalogo` e `anime-pipeline._memes_series`: mesmo filtro (catálogo visual segue com 235).
- Figurinha no canto: `ANIME_MEMES_FIGURINHA` 1 → 0. No lugar, a mascote reage até `mascote.reacoes_max`=6 vezes
  (era 3 fixo) — `anime-pipeline._memes_resumo`.

## 5. SFX x voz

Causa: `fx_clips.apply_effects_to_cmd` misturava SFX e voz ao mesmo tempo (amix).

Correção (`ANIME_SFX_GAP=1`, `ANIME_SFX_GAP_MAX=1.2`):
- `fx_clips.sfx_gap_s`: silêncio = duração do SFX (0,2 a 1,2 s).
- `anime_segments._voz_depois_do_sfx`: põe esse silêncio no começo do wav da frase (adelay) ANTES de montar o
  clipe; o trecho fica mais longo nesse tanto (tempo do vídeo e legenda continuam alinhados: os tempos de palavra
  do `.words.json` são deslocados junto).
- `apply_effects_to_cmd`: SFX cortado no mesmo tamanho + fade de 0,12 s no fim.
- Pausa da mascote não leva SFX (como antes).

Teste (soco, 0,15 s): áudio do clipe = SFX 0–0,14 s, silêncio, voz a partir de ~0,28 s.

Efeito colateral esperado: cada frase com SFX fica 0,2–1,2 s mais longa (~40% das frases têm SFX no longo →
estimativa +2 a 4% no tempo total).

## 6. Mascote Maria + amiga

Medido nas gravações (`workspace/assets/mascote_viva`): TODAS terminam com a personagem no centro (x≈0,5) — por
isso as duas ficavam uma em cima da outra; amigas ~7% menores (altura 0,84–0,91 × 0,92–0,97); o fim das gravações
da Maria tem um close no rosto; `amiga_indigena_comenta_02` é antiga em pé (718x960).

Correção (`bin/mascote_overlay.py`):
- `_anda_sempre`: fala maior que a gravação = vai-e-volta da janela 40–65% da gravação (ela parada falando), em vez
  do último quadro congelado (`tpad=clone`). Vale na pausa e no overlay do longo.
- `montar_pausa` com amiga: Maria entra pela esquerda e fica deslocada 22% pra esquerda; amiga entra pela direita
  (espelha conforme o `lado` do json dela) e fica 22% pra direita; amiga escalada até a altura da Maria
  (`_escala_amiga`, medida no alfa); a amiga **fala depois** da Maria (entra 0,8 s antes do fim da fala dela) e o
  trecho cresce até o fim da fala da amiga; som da amiga mixado.
- `amiga_viva(k, so_pedido=True)`: só amigas andando (paisagem) e, no CTA, só gravação de pedido (não "que raiva
  desse cara").
- `anime_segments`: duração do trecho da pausa = duração real do clipe montado (cresce com a fala da amiga).
- `anime-pipeline._mascote_longo`: a amiga por cima da narração SAIU — ali ela aparecia muda, no centro, e não há
  como ela falar sem tampar o narrador. Ela conversa só nas pausas (1 a cada 3 pausas).

Teste: pausa com Maria (7,9 s de fala) + amiga loira → clipe de 15,1 s; quadros em 1–14,5 s mostram as duas em lados
opostos, do mesmo tamanho, se mexendo; volume mostra as duas falas em sequência.

---

## 7. Rodada 2 (31/10 tarde, depois da dona ver a amostra)

- **1080p** (`fx_subtitles.burn_subtitles_ass`, `ANIME_SAIDA_1080=1`): o longo deitado sai 1920x1080, escalado
  (lanczos) na passada da legenda, antes do libass. Medido aqui: essa passada fica 2,65× mais lenta (14 s → 37 s
  em 60 s de vídeo). No 4wuf ela levou 28 min → estimativa +46 min (render 4h38 → ~5h25, +17%).
- **Disco** (`anime-pipeline.run_one`): SNhb31 morreu com "No space left on device" e o 4wuf chegou na legenda com
  1,4 GB livres; em 1080p o final fica ~2× maior. Os trechos e os memes inseridos agora são apagados logo depois do
  concat (log `disco depois do concat`).
- **Zoom múltiplo**: 5 variações em rodízio (3×0,22 aprovado; 2×0,35; 4×0,15; 3×0,12; 5×0,12).
- **Transições novas** (`bin/gera_divisoria.py`, mesmo formato do raio): fogo vermelho, água, papel rasgado, gelo
  (`_divisoria_{fire_ff2a1a,agua_2a9df4,papel_f4efe4,gelo_bfefff}.webm`) — 10 no rodízio. Fogo azul descartado (o
  gerador do manhwa-react ignora a cor do fogo).
- **Mascote reage mais**: `reacao_viva` só achava 2 das 9 reações deitadas (glob `<tipo>_andando_*`); no 4wuf reagiu
  1 vez em 18 memes. Agora pega todas (amigas inclusive) e repete quando acabam; `reacoes_max` 9.
- **Meme de imagem em tela cheia** (`memes_visuais.escolher_imagens/montar_imagem`, `memes_visuais.imagem_cada`=15):
  1,2 s, entra com soco de zoom, fundo borrado, whoosh; GIF anima. No lugar das 80 figurinhas de canto do 4wuf.
- **Amostras dos narradores**: `D:\hipercool-materiais\amostras_voz\narradores_para_separar\<grupo>\<voz>.mp3`
  (54 de 20 s, origem em `_origem.txt`; 19 vozes sem áudio no PC listadas no LEIA.txt).
- **Pedido novo com tudo isso**: `20261027_000050_SNhb31ZuuFA` (refeito do SNhb31, 1º da fila, narradores
  guugou + mangaticos).
- Vídeo P-djtsSY2Co (Curiosidades Noturnas) está privado porque foi AGENDADO pra 01/11 12:30 (logs\youtube_http.log),
  não é falha.

Por que o longo fica mais curto que o original (4wuf): original 6565 s, narração 5045 s (77%). O roteiro resume a
história; cada frase mostra o trecho do original que ela narra (tempos do roteiro) e o que o roteiro pula não
aparece. Quando a fala de uma frase é mais longa que a cena dela, a cena estica (é o "loop" visível).

## 8. REGRA: nenhum vídeo com menos de 1080p (dona 31/10)

Causa: o longo e os Shorts dos Cortes renderizam em 720p (fx_assets) e o `upscale_to_fullhd` só é chamado pelo
hiper-pipeline (Shorts do hipercool). Medido nos arquivos dos últimos 3 dias: Shorts do hipercool e produtos
(Remotion) 1080x1920; Shorts dos Cortes (`animes recap\shorts`, `final_anime_short.mp4`, `CORTES_ULTIMO_VIDEO`)
720x1280; cortes do longo (`shorts_from_deitado`) 720x1280; longos 1280x720.

Travas (sem chave pra desligar):
1. `fx_subtitles.burn_subtitles_ass`: deitado → 1920x1080, em pé → 1080x1920, na passada da legenda.
2. `anime-pipeline._garantir_1080`: confere o arquivo final com ffprobe e faz upscale do que escapou; falhou = erro.
3. `shorts_from_deitado.OUT_W/OUT_H` = 1080x1920.
4. Postador (`politica.garantir_1080`, chamado em `postar_youtube`, `youtube_web_poster.main` e `youtube_poster.main`):
   qualquer vídeo de qualquer projeto abaixo de 1080p vira `<nome>_1080p.mp4` antes do upload (reaproveitado nas novas
   tentativas); falhou = não sobe. Teste: Short 720x1280 → 1080x1920 em 44 s.
Os longos já prontos em 720p (fila de postagem) passam pela trava 4 no PC (estimativa ~1 h cada).

## Arquivos alterados
- `bin/anime_tts.py`, `bin/anime_segments.py`, `bin/fx_clips.py`, `bin/fx_detect.py`, `bin/memes_visuais.py`,
  `bin/anime-pipeline.py`, `bin/mascote_overlay.py`
- `config/longo.json`, `colab/teste_narradores.json`, `colab/cliente.py`, `colab/corrigir_pedidos_fila.py`

## Como conferir no próximo longo (log do Kaggle / vídeo)
1. `[revezamento] principais=[...] blocos=[...] especiais=[...]` — 1º bloco ≥35% das frases, ≤5 principais.
2. `[longo] voz de cada personagem: {...}` — nenhum `kratos` fora de personagem monstro.
3. `[divisoria]` ~1 a cada 3 trechos; `[multizoom]` presente.
4. Nenhum `Roda regina` / `Music` / `Song` nos nomes de SFX/meme do log.
5. Ouvir 3 frases com soco/explosão: som e voz separados.
6. Pausa com amiga: lados opostos, mesmo tamanho, as duas falando em sequência, sem congelar.

## Pendências
- Balões: decisão da dona com a medição (item 2).
- Filtro de chiado do Galvão (item 1), se ainda incomodar.
- Conferir o 1º longo inteiro renderizado com estas mudanças.
