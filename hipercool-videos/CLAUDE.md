# CLAUDE.md — hipercool-videos

> **OBRIGATÓRIO ANTES DE MELHORAR QUALQUER VÍDEO (dona, 01/11):** rode `python D:\video-fila\aprendizado.py aprovados`,
> leia `D:\video-fila\aprendizado\PARA_IMPLEMENTAR.md` (todos os aprovados + os candidatos do tipo que você vai mexer) e
> marque cada um aplicado/reprovado. Ninguém mais implanta isso — se você pular, fica parado. Passo a passo:
> `D:\video-fila\aprendizado\LEIA_ANTES_DE_MELHORAR.md`. Mexeu em LONGO? Mesma obrigação em
> `D:\video-fila\linhas\LONGOS\LONGOS_MELHORIAS.md` (A FAZER / JÁ FEITO / DESCARTADO — não refazer o que já está lá).

Recap em vídeo de capítulos de manhwa/manga (painéis reais) com narração TTS, efeitos ffmpeg
e legenda. Código em `bin/`, orquestrado por `bin/hiper-pipeline.py`.

**O que o dono pediu e ainda falta: `docs/PEDIDOS_DO_DONO_PENDENTES.md`** (lista com prioridade, estado e como fazer).

> **16/10/2026 — ADVERTÊNCIA do YouTube no canal pt (InovareManhwaVerse): "Nudez e conteúdo sexual", pelo compilado
> caps 1-11** (painéis sem censura e mosaico no lugar errado; ninguém tinha assistido o vídeo pronto). Envio
> bloqueado até ~23/10; a advertência vale até ~14/01/2027 e mais 2 apagam o canal. Os vídeos do The Inheritor do
> canal pt ficaram privados e o canal está em `suspensos` no `D:\postador-de-videos\config\canais_status.json`
> (tirar só por decisão do dono). A análise do vídeo pronto (`bin/revisao_video.py`, seção abaixo) roda em todo
> vídeo, mas **desde 18/10 só AVISA** e marca os painéis pra fosco no próximo render. Regra do dono: nenhum canal fica
> um dia sem postagem; nenhum impedimento segura a postagem (`config/fila.json` `_regra_postagem`).

**Leitura obrigatória: `docs/MELHORIAS_PARA_TODOS_OS_PROJETOS.md`.** Resume as regras de título/SEO (nunca o nome da
obra), capas (catálogo de poses, limite, teste A/B, capas dos Shorts), extras do Studio, estrutura, efeitos 2.5D e
censura. Vale também pros outros projetos: o manhwa-react, o historias-em-frames e o recapd-ambientes têm só um
ponteiro pra ele (`LEIA_MELHORIAS_HIPERCOOL.md`), então ninguém lê versão velha. **Melhorou ou corrigiu algo que serve a
outro projeto? Registre na hora em "Novidades", no topo desse arquivo** (data, o quê, onde está o código, pra quem
serve). Regra que mudou: corrija também a seção dela lá embaixo.

## Onde as coisas estão (o projeto é espalhado — leia antes de mexer)

| Pasta | Papel hoje |
|---|---|
| `D:\hipercool-videos` | **Projeto ativo.** `bin/` = código, `venv/` = Python (recriado em 2026-10-12), `config/`, `secrets/`. |
| `D:\hipercool-materiais` | Hub compartilhado: `panels/` (1064 caps), `videos/` (saída), `assets/` (sfx, trilhas, fontes, overlays), `narration_cache/`, `tts_cache/`, `bin/ffmpeg.exe`. `workspace/*` daqui são junctions pra lá. |
| `D:\recapd-ambientes\producao` | Outro projeto (recap de ANIME). Tem cópias antigas do pipeline e caches antigos de narração (`workspace/narration_cache/the-meek-cat-*`). Não editar. |
| `D:\postador-de-videos\bin` | Cópia antiga (monolítica, 03/07) do pipeline + postagem. Não editar. |
| `D:\historias-em-frames` | Projeto irmão (imagens IA). Não editar. |
| `D:\hipercool-motionframes`, `D:\hipercool-producao` | Órfãos (dependiam do venv apagado / do `hipercool-inferior-fix`, que não existe mais). |

O git deste projeto só rastreia `ambientes/3-exp/bin/gemini_llm.py`; o resto está fora do controle de versão.

## Rodar um capítulo

```bash
cd /d/hipercool-videos
export PATH="/d/hipercool-materiais/bin:$PATH" PYTHONUTF8=1 GEMINI_TTS_PROXY_ENABLED=1
venv/Scripts/python.exe bin/hiper-pipeline.py \
  --panels-dir /d/hipercool-materiais/panels/the-meek-cat-cap08 \
  --titulo "The Meek Cat — Capítulo 8" --max-panels 120 --skip-final 2 \
  --subtitles --karaoke --censura --skip-notify --output-suffix _NORMAL > logs/cap08_normal.log 2>&1
```

`--skip-final N` descarta os N últimos painéis. Os capítulos do scan Blackout (The Meek Cat) terminam com 2 páginas de
propaganda (Discord + site); sem isso a narração "dubla" o anúncio e o CTA final cai em cima dele.

Saída: `workspace/videos/hipercool_<slug>_<data>_NORMAL_ULTIMO.mp4` + `.meta.json` (com o relatório
de validação) + `.capa.jpg` (thumbnail). Teste rápido: `--max-panels 8 --skip-credits 0`.

Cache de narração: `workspace/narration_cache/<slug>_sk<N>_<n>panels.json` — reaproveitar evita gastar
visão/LLM. Voz: `workspace/tts_cache/` (não apagar). Re-render de capítulo já feito = zero IA: roteiro,
editorial, vozes, censura (`workspace/censura_cache/`) e tempo por palavra (`workspace/cache/groq/`) vêm do
cache. O que muda a chave e faz a IA rodar de novo: outra pasta de painéis, outro `--skip-*`/nº de painéis,
`--force-llm`, `--force-tts`, ou imagem de painel diferente (censura é por md5).
As vozes de antes de 2026-10-12 15:58 sumiram do tts_cache (causa desconhecida); refazer caps antigos regera voz.

**Backup dos caches**: `bin/backup_caches.py` (tarefa `BackupCachesHipercool`, diária 06:10) só COPIA vozes,
roteiros, censura e groq pra `manhwa-drive:caches-backup/hipercool/` — nunca apaga nada. Restaurar o que
sumir do PC: `python bin/backup_caches.py --restaurar`.

**Máquina**: i5-8365U, 16 GB, só GPU **Intel UHD 620 integrada** (não há NVIDIA: NVENC/CUDA não funcionam).
O que usa a GPU: Quick Sync (`h264_qsv`, ~3x mais rápido que x264), hoje só nas camadas do parallax.

## Personagem recortado + parallax 2.5D (`bin/fx_parallax.py`, ligado por padrão)

Nos clips normais (não nos de impacto/tensão), ~60% dos painéis com personagem destacável (10–72% da área,
proporção até 3:1, sem dois quadros empilhados) e nunca em dois clips seguidos: o modelo local isnet-anime
(`D:\hipercool-materiais\models\isnet-anime.onnx`, CPU, ~2-3 s/painel, máscara em `workspace/cache/mascaras/`)
recorta o personagem; o painel (sem o personagem, inpaint) e o personagem (sombra + contorno de luz) se mexem
em velocidades diferentes. Depois passa pelo mesmo comando do `build_clip` (cor, vinheta, overlay, transição,
SFX). Falhou -> clip normal. Desligar: `HIPER_PARALLAX=0`; frequência: `HIPER_PARALLAX_CHANCE`.

## Vozes do português: elenco fixo + motor (`bin/elenco.py`, 15/10)

- **Motor**: `config/fila.json` → `"tts_motor"` (`HIPER_TTS_MOTOR` passa por cima).
  - `"edge"` desde 15/10: teste do dono a partir do cap 9 do The Inheritor; ~5 s por fala, sem cota.
  - `"gemini"`: como era, ~70 min de voz por capítulo por causa do limite de cota.
- **Elenco por obra**: `config/elenco/<obra>.json`.
  - Narrador, protagonista e par principal têm voz FIXA na obra, e a base deles é exclusiva (ninguém usa nem
    variação dela).
  - Cada personagem novo ganha uma voz livre e fica com ela.
  - Figurante genérico ("Rapaz", "Jovem"...) usa só variações.
  - `normalizar()`: apelido vira nome oficial. Genérico com 4+ falas num capítulo sem o nome do protagonista/par
    vira ele/ela (cap 2: 27 falas de "Rapaz" = Joo Inhyuk).
  - Antes o registro de vozes era um só pra todas as obras e trocava a voz quando a IA mudava o nome.
- **Edge PROIBIDAS** (dono): `pt-BR-AntonioNeural`, `pt-BR-FranciscaNeural`, `it-IT-IsabellaNeural`.
  - Aprovadas: as **Multilingual** (Thalita, Ava, Emma, Seraphina, Vivienne; Andrew, Brian, William, Florian,
    Remy, Giuseppe, Hyunsu) × 10 variações de velocidade/tom (`VARIACOES`).
- **Amostras e testes**:
  - amostras: `Área de trabalho\Hipercool\AMOSTRAS DE VOZ`;
  - motores locais testados (Supertonic-3 ~1,3x tempo real, Kokoro 0,3x): `D:\tools\tts-teste` +
    `D:\tools\testar_vozes.py`.
  - Local = só reserva e no PC2; ainda não ligado.
- **Microcortes (dona, 22/10)**: as pausas entre as falas saem (`narracao_curva.microcortes`, comum: pausa > 0,07 s
  vira 0,07 s, a fala NÃO acelera) — vale pra qualquer vídeo, depois do teste. Aqui está LIGADO desde 22/10 (dona
  aprovou o teste do cap 14 com o cache: 214 s -> 194 s): `elenco._microcortes` no fim de toda fala (pt, Gemini,
  `idiomas.py`, 16:9). `HIPER_MICROCORTES=0` desliga. Não reintroduzir respiro fixo entre as falas.
- **Janelas**: tarefa agendada roda em pythonw e todo filho de console abria janela na tela.
  `bin/sem_janela.py` (importado no `fila.py` e no `backup_caches.py`) põe CREATE_NO_WINDOW em todo subprocess.
  Ponto de entrada novo que roda escondido tem que importar ele.

TTS: proxy **obrigatório** (decisão do dono, 15/10): `GEMINI_TTS_PROXY_ENABLED=1` em tudo (fila, .bat, PC2) —
não voltar pra 0. A voz nunca chama o Gemini direto; sem proxy disponível a fala falha e é tentada depois.
Lista em `secrets/proxies.txt` (Webshare, `p.webshare.io:80`; # = comentário). Proxy que falha (conexão, túnel
ou página que não é JSON da API) sai da rotação e é testado de novo em 1 h / 1 dia — a Webshare renova a banda
1x por mês e a conta volta sozinha (estado em `secrets/proxies_estado.json`). Erro JSON da API = chave (429 etc.).
Atenção: proxy não aumenta a cota do Gemini (é por chave); cada fala gasta ~1 MB de banda da conta Webshare.
(12/10: a lista tinha linhas com comentário no fim e o endereço 31.59.20.176:6754 morto — por isso "caía".)

## Acabamento (`bin/fx_acabamento.py`, porte do D:\manhwa-react — ligado por padrão)

Depois do concat, num único fluxo:
- **Editorial por LLM** (1x por capítulo, salvo no cache de narração): gancho, 5–8 palavras de impacto + emoji, pergunta do CTA.
  Usa o proxy do `D:\manhwa-react\secrets_proxy.json`; o Gemini fica como reserva.
- **Tempo real por palavra**: Groq whisper (`D:\postador-de-videos\secrets\groq_keys.json`) alinhado ao texto; sem Groq, divisão proporcional.
  Todo pedido ao Groq passa por `bin/groq_api.py`: rodízio das chaves e SEMPRE pelo proxy Webshare (dono, 15/10;
  sem proxy não vai direto). Chave que der 401 vira `"status": "invalida"` no arquivo. `python bin/groq_api.py --testar`.
- **Legenda ASS** palavra a palavra com pop, gancho, selo obra/capítulo, palavra de impacto gigante, barra de progresso, marca d'água e CTA sobre o último painel.
  Esses elementos substituem o intro/outro de tela parada.
- **Som**: SFX de impacto e gatilhos por palavra (`config/gatilhos_narracao.json`), com anti-poluição.
  A trilha é nivelada (-28 LUFS), respeita a blocklist de copyright e tem ducking pela voz.
  O master final sai em -14 LUFS, com pico de -1 dBTP.
- **Passe final único**: upscale lanczos + `cas` + punch-in/tremor nos impactos + emoji + ASS.
  Emoji e figurinha parada entram como clipe `.mov` curto (`_clipe_parado`, cache em `workspace/cache/clipes_parados/`),
  NUNCA como `-loop 1 -i imagem`: com várias imagens em loop no mesmo gráfico o ffmpeg 8.1 trava sem usar CPU, sempre
  no mesmo quadro (15/10: cap 8 parou 3x aos 19 s; cap 6 ficou 2 h preso). Reproduzido e conferido no vídeo inteiro.
- **Validação** (duração, resolução, LUFS, trechos pretos, áudio x vídeo) e **capa** 1280x720.

Desligar: `--no-acabamento` ou `HIPER_ACABAMENTO=0`.
Ajustes por env:
- `HIPER_TEMPO_PALAVRA=prop` (sem Groq)
- `HIPER_EDITORIAL_LLM=0`
- `HIPER_LUFS`, `HIPER_MUSICA_LUFS`
- `HIPER_PRESET`, `HIPER_CRF`, `HIPER_THREADS`, `HIPER_CLIP_CRF`
- `HIPERCOOL_COR`

## Censura (`--censura`, `bin/censura_visual.py`) — a versão que vai pro YouTube

A censura é feita **na imagem do painel, só nas partes explícitas**. Nunca borre o vídeo pronto por janela de
tempo (`fx_subtitles.censurar_video` é legado): isso borra a tela inteira, legenda e @ inclusive. Esse foi o
erro de 2026-10-12.

1. **Quais painéis**: Sightengine `nudity-2.0` (score `activity*2 + display*1.5 + erotica*1.2`, limiares
   0.45/1.15 da V8; cache por md5 em `workspace/censura_cache/`). Reserva: NudeNet e, por último, o texto
   (`fx_detect.is_nsfw_panel`). 3ª camada da V8: mancha branca + vizinho +18 vira censura "branco".
   Chaves: lidas de `secrets/sightengine.json` e das cópias do postador/recapd (só leitura). O status de
   esgotada fica em `workspace/censura_cache/_chaves_esgotadas.json` e zera no dia seguinte.
2. **Onde**: o Gemini devolve as caixas das partes explícitas (cache `<md5>.regioes2.json`). Primeiro os Gemini
   do proxy do Claude Code (`claude_client.GEMINI_PROXY`, mais rápidos e precisos), depois as chaves diretas.
   A caixa ganha folga de 22% + 3% da largura. O NudeNet não serve pra localizar: em manhwa ele não acha quase nada.
3. **Como**:
   - **Mosaico é SEMPRE a primeira escolha** (decisão do dono, 16/10). Fosco só quando não tiver jeito:
     cobertura > 80% (`CENSURA_MAX_FRAC_LOCAL`), cobertura < 3% com score alto, conferência visual diz que o mosaico não escondeu, ou
     Gemini falhou em localizar. Nunca trocar mosaico por fosco "por segurança" — mosaico bem feito já basta.
   - Com caixas: mosaico com borda suave **só nelas** (nível `local`). Balão com texto fica fora da máscara.
     Caixa pequena (menos de 2% do painel) ganha folga mínima de 6% da largura, senão o mosaico não cobre nada.
   - Caixas cobrindo mais de 80% do painel, ou Gemini falhou: `fosco`, o exodia fosco da V8 (fundo borrado,
     balões e branco da página nítidos).
   - **Mosaico cobrindo menos de 3% (`CENSURA_MIN_FRAC_LOCAL`) com score >= `LIMIAR_NSFW` também vai pro
     `fosco`** (16/10): o modelo às vezes marca só um mamilo num painel de nudez inteira e o mosaico de 1%
     não esconde nada (cap 10 panel_028, score 2.01, 0,9% do painel: os dois seios nítidos no vídeo postável).
   - O Gemini dá primeiro um veredito (`explicito`). Se ele diz "não explícito", o painel fica intacto,
     exceto quando o score é forte E a narração também indica +18; aí vai pro fosco. O Sightengine erra
     muito em manhwa (conferido em 16/10: cap 10 panel_062, score 1.64, é um casal VESTIDO no sofá; panel_065,
     display 0.49, é uma MÃO apontando). A narração sozinha também não veta:
     o panel_030 é explícito e ela não marca.
   - **Se o Gemini diz `explicito` e nenhuma caixa sai legível, o painel vai pro `fosco`, nunca intacto**
     (16/10): `localizar_regioes` devolve `None` nesse caso — `[]` quer dizer "não é explícito". O parser
     não lia o formato `"box_2d": [[y,x,y,x]]` e por isso o cap 10 panel_027 (score 2.08, nudez frontal) e o
     cap 9 panel_102 saíram INTACTOS nos vídeos de 15/10 e no compilado caps 1-11 que foi postado.
   - Painel que entra na lista +18 e sai intacto com score >= `LIMIAR_NSFW` é logado com `[!]` e vai pro
     `.meta.json` em `censura.conferir` — é o que precisa de olho na folha de quadros antes de postar.
   - **Silhueta branca (19/10, dono achou nos caps 8, 9 e 14)**: a própria obra "censura" o pênis pintando de
     BRANCO/luz — liso, sem traço, mas com o contorno do órgão. Sightengine/NudeNet não veem pele e o fosco/mosaico
     por cima de mancha branca grande MANTÉM a silhueta. Por isso, em todo painel com risco (score >= dúvida,
     forçado ou "branco"), `censurar_imagem` pergunta antes `localizar_silhuetas` (Gemini, `PROMPT_SILHUETA`, cache
     `<md5>.silhueta1.json`; proxy -> chaves diretas, 3 tentativas), APAGA o branco dentro da caixa
     (`apagar_silhuetas`: inpaint com as cores de volta, balões preservados) e só então segue o caminho normal
     (local/fosco/forçado/branco) sobre a imagem sem a silhueta; a área dela sai sempre com mosaico. Testado nos 5
     painéis com a forma (cap08 047/074, cap09 030/059, cap14 003) e em 3 de faixa de luz (nada marcado). O parser
     aceita `"regioes":[[y,x,y,x]]` sem `box_2d` (o cap08 074 veio assim e passava como "nada").
4. O pipeline refaz só esses clips com a mesma função e parâmetros (mesma duração). No `fx_acabamento.finalizar`,
   a censurada recebe o **mesmo** áudio masterizado, ASS, emojis e punch-ins do principal, com tudo nítido por
   cima. Saída: `..._NORMAL_CENSURADO_ULTIMO.mp4` + `.meta.json` com `censura` (painéis, nível e janelas) +
   capa feita só com painéis limpos.
5. **Reforço depois da advertência (16/10)**, todos com a mesma pergunta da análise do vídeo pronto
   (`revisao_video.exposto`): (a) `reforcar_scores`: painel abaixo de `LIMIAR_DUVIDA` em que a visão vê parte
   exposta entra na censura (cap 10 panel_005, score 0,44, e cap 3 panel_048, 0,16, saíam com nudez); (b) a imagem
   JÁ com mosaico é perguntada de novo e, se ainda aparece, vira fosco (cap 3 panel_054 original: caixas longe dos
   mamilos); (c) localização diz "não explícito" mas a pergunta direta vê parte exposta: fosco; (d) painel na
   lista de forçados (`forcar_fosco`, alimentada pela análise do vídeo pronto) sempre sai em fosco. O parser lê
   também várias caixas no mesmo `box_2d` (`[[...],[...]]`).
6. Depois do render: **análise do vídeo pronto** (seção abaixo). A "folha de quadros" sozinha não basta: ninguém
   olhava e foi assim que o compilado caps 1-11 subiu com nudez.
7. **Versão NORMAL só precisa ser produzida uma vez** (decisão do dono, 16/10). Quando um capítulo já tem o vídeo
   `*_NORMAL_ULTIMO.mp4`, re-renders fazem APENAS a versão censurada — vozes novas, censura melhorada, marca d'água
   diferente etc. não refazem a normal. Implementado via flag `so_cens_pt` em `hiper-pipeline.py`: detecta o normal
   existente no diretório e passa `so_censurado=True` ao acabamento. As línguas já faziam só a censurada.
   (16/10: escrito depois que o lote do cap 1 começou; ainda não rodou em nenhum render — conferir no log a linha
   "pt: o capítulo já tem a versão normal".)

Requer `opencv` e `nudenet` no venv (instalados em 2026-10-13). Ajustes: `CENSURA_LIMIAR_DUVIDA`,
`CENSURA_LIMIAR_NSFW`, `CENSURA_MAX_FRAC_LOCAL`, `CENSURA_MIN_FRAC_LOCAL`.

> **Vídeos feitos antes de 16/10 têm nudez sem censura** (a análise do vídeo pronto reprovou 47 quadros só no
> cap 10 de 15/10). Não poste nenhum deles: a fila analisa e renderiza de novo com o código novo.

## Análise do vídeo pronto (`bin/revisao_video.py`, 16/10) — trava da postagem

Faz o papel de quem assiste antes de postar.
- **O que faz**: 2 quadros/s do arquivo FINAL (sem os repetidos), em resolução cheia (1280 px); cada quadro vai ao
  Gemini do proxy (3 opiniões, basta 1 "sim") perguntando se tem mamilo, genitália ou nádegas à mostra sem mosaico
  ou com mosaico fraco. Veredito em `<video>.revisao.json`, os
  quadros reprovados em `<video>.revisao/` e lado a lado em `<video>.revisao.jpg`. Vale só pra aquele arquivo
  (tamanho + data) e pra `VERSAO` do critério.
- **Só painel com risco vai ao Gemini** (16/10 tarde; cap 1: 142 de 727 quadros, 5 min em vez de 18,6). Limpo =
  score do Sightengine < 0,10 (cache), fora da censura e dos forçados, e a mesma pergunta na imagem original diz
  "nada exposto". Abertura, memes e ±0,6 s em volta de painel com risco são sempre olhados. O mapa clip->painel do
  meta é posto no tempo REAL pelos cortes de cena do próprio vídeo (`_alinhar`): o `acabamento.fronteiras` chega a
  ficar 3,5 s adiantado no fim (ver PEDIDOS, "mapa atrasado") e antes disso a análise apontava o painel errado — no
  cap 1 de 16/10 forçou fosco no 007 (vestida), 102 (casaco) e 103 (pé) e deixou de fora o 104, que aparecia. Mapa
  casado em menos de 60% dos cortes ou sem pasta de painéis: olha todos os quadros, como antes.
- **Onde trava**: `postar_hipercool.postar()` não sobe sem veredito "ok" — completo (o próprio arquivo), Shorts (o
  completo de onde foram cortados) e compilado 16:9 (cada `capNN.mp4`; compilação mais velha que um capítulo refeito
  também não sobe). Sem veredito, analisa na hora. Sem resposta do Gemini = "incompleto" = não posta.
- **Fila** (`fila.revisar_pronto`, depois de cada render): reprovado na 1ª vez → fosco forçado nos painéis do trecho
  (`censura_visual.forcar_fosco`; lista em `workspace/censura_cache/_forcar_fosco.json`, vale pra pt, línguas e
  16:9; o `pc2.py` manda pro PC2 junto com os painéis) e renderiza de novo; na 2ª vez, situação `revisar` + aviso no
  Telegram com os segundos. Vídeo antigo (meta sem `clip_paineis`) só renderiza de novo com o código novo, sem forçar.
  `revisar_pendente` (Gemini sem resposta) tenta de novo a cada ciclo; o ciclo também analisa 1 capítulo "pronto"
  antigo por rodada. As línguas só renderizam com o pt "pronto", então herdam os painéis forçados.
- **Engano da análise**: o dono olha `<video>.revisao.jpg` e libera com
  `python bin/revisao_video.py --liberar <video>`.
- **Prompt**: vocabulário de moderação e resposta só `{"exposto": true|false}`. Palavra anatômica mais direta, campo
  de texto livre ("o_que") ou vários quadros numerados na mesma imagem fazem o filtro do Google RECUSAR o pedido
  (testado). Peito de homem, gente vestida e meme de desenho sem nudez estão excluídos (eram falso positivo).
- **Medido em 16/10**: pegou todos os vazamentos conhecidos (cap 10 aos 32-35 s e 158-166 s, caps 1-3 aos 900-911 s,
  cap 3 hindi aos 33-35 s) e outros que a censura por painel nunca pegaria. Cena de sexo com mosaico só na boca/fluido
  costuma ser marcada — é o lado seguro. Ponto fraco: nádegas às vezes só na 3ª opinião; painel < 1 s na tela.
- **Nome repetido no postador**: `D:\postador-de-videos\bin` tem cópias velhas de `claude_client`, `censura_visual`
  e mais 20 módulos, e o `postar_hipercool` põe essa pasta na FRENTE do `sys.path`. Em processo que importou o
  `postar_hipercool`, use `revisao_video.modulo("censura_visual")` em vez de `import censura_visual`.

## Produção automática (`bin/fila.py`) e botões da área de trabalho

Pasta `Área de trabalho\Hipercool`, com o passo a passo em `0 - O QUE CADA BOTAO FAZ.txt`. Os `.bat` ficam na raiz
do projeto (`HIPERCOOL_*.bat`):
- `fila.py ligar|desligar`: cria ou desliga a tarefa `HipercoolFila`, que roda `fila.py ciclo` a cada 20 min.
  A flag `config/FILA_DESLIGADA.json` também desliga.
- **Ciclo**:
  1. Posta em português: 1 vídeo completo novo por dia; o resto da cota (3/dia) vai pros Shorts.
  2. Se houver menos de `adiantado` (2) capítulos esperando postagem, renderiza o próximo de `config/fila.json`
     (hoje The Inheritor 1–41).
  3. Propaganda/créditos nas pontas: o Claude (Sonnet do Kiro) classifica os 2 primeiros e os 3 últimos painéis.
  4. Checagem automática no lugar da revisão: validação ok e menos de 50% do tempo censurado. Acima disso o
     capítulo vira "compilado" e não é postado avulso. A folha de quadros é gerada.
- `fila.py postar`: só português, funciona com a fila desligada. `fila.py idiomas`: outras línguas (ver abaixo).
- `fila.py status`. Estado: `workspace/fila_estado.json`. Avisos no Telegram (`_tg_safe`).
- **Pausa inteligente** (`bin/limitador.py`): na 3ª falha seguida de um serviço (tts, render, youtube), pausa.
  A pausa começa em 5 min, dobra até 2 h e cai pela metade quando volta a dar certo (`workspace/limitador.json`).
  O TTS espera e tenta de novo, em vez de virar clip mudo.

## Outras línguas (`--idioma hi|id|it|ru|th|vi`, `bin/idiomas.py`)

Canais inovare hindi/ind/ita/ru/thai/viet, que são do hipercool desde 13/10 (projeto "hipercool" no postador).
Postam **só pelo navegador** e só depois do capítulo em português.
- O que reaproveita: painéis, censura, recortes, efeitos.
- O que troca:
  - roteiro: tradução em 1 chamada (Claude), cache `narration_cache/<chave>_<lang>.json`;
  - voz: edge-tts por idioma/gênero, tom por personagem. Precisa do **edge-tts ≥ 7.3.1**: a 7.2.8 dava 403;
  - Groq no idioma, e textos fixos (selo, CTA, Shorts, descrição) traduzidos;
  - fontes Nirmala UI (hindi), Leelawadee UI (tailandês) e Montserrat no vietnamita (acentos empilhados).
- Saída `_<LANG>_ULTIMO.mp4`. O `postar_hipercool.py --idioma xx --canal <id>` confere se o canal é o da língua.
- ind e thai sobem pela conta inovaremanhwaverse@gmail.com (o dono logou em 13/10). viet foi liberado no mesmo dia.
  Canal sem login: `ativo: false` no `config/fila.json` (a fila pula). french/eng pausados e esp suspenso: fora.
- **Elenco normalizado** (15/10): `hiper-pipeline.py` chama `elenco.normalizar()` também nas locucoes traduzidas
  (linha ~400), pra genéricos virarem protagonista/par nos idiomas. Testado no cap 2 hindi: "Rapaz" → "Joo Inhyuk".

## Métricas automáticas (bin/metricas.py, 15/10)

Lê analytics do YouTube Studio pelo navegador e decide o que rende melhor (aberturas com voz humana e estilos de título).

- **O que mede**: impressões, CTR, views, duração média e **retenção aos 30 s** de vídeos LONGOS (completo 9:16 e 
  compilado 16:9) postados há 2–21 dias. 6 vídeos por rodada, 1 rodada por dia (chamado no fim da `fila.postagem`).
  Resultado em `workspace/metricas.json`.
- **Decisão**: com 7+ dias e 3+ vídeos medidos de um tipo:
  - **Abertura voz humana**: retenção 30 s acima da mediana dos compilados = vitória (`intros_voz.registrar_resultado`).
  - **Estilo de título**: CTR acima da mediana dos completos do canal (100+ impressões) = vitória 
    (`seo.registrar_resultado`).
- **Leitura do Studio**: `youtube_studio_extras.py --metricas <video_id>` raspa os valores das páginas de analytics.
  Rótulos esperados: "Visualizações", "Impressões", "Taxa de cliques", "Duração média", "retenção em 30 segundos".
  **NÃO TESTADO em página real do Studio** (parsing unit-testado, mas os rótulos podem ter mudado).
- **Teste A/B de capa**: bloqueado (canal pt em verificação até 14/11/2026). Quando liberar: 
  `youtube_studio_extras.teste_ab` + `capa_ia.registrar_vencedora`.
- CLI: `python bin/metricas.py` (roda se última rodada > 20 h), `--agora` (força), `--so-decidir` (não abre navegador).

## Divisão entre os dois PCs (desde 14/10)

O gargalo são as línguas (7 canais, até 3 vídeos/dia cada), não o pt (1 completo/dia). Por isso:
- **PC1 (este)**: pt sempre primeiro (gera roteiro e o cache 2.5D) e, no tempo livre, línguas na ordem do
  `config/fila.json` (hi, id, it...).
- **Desktop** (desktop-su00b7v, `ssh desktop` = 100.73.7.19, usuário Emerson): desde 24/10/2026 o Windows de lá está
  SEM SENHA; acesso só por chave (`ssh -o BatchMode=yes desktop`), nunca usar/pedir senha. Se a chave for recusada,
  avisar o dono. Só tarefa leve (i5, sem GPU); ocupado com OBS ou chamada (`D:\video-fila\maquinas.py`).
- **PC2** (Revision-PC, ssh `pc2` = 100.125.7.77, usuário Emerson-IA, 2 núcleos, Intel HD 620 com Quick Sync):
  **só línguas, sem parar**, na ordem inversa (en, vi, th...), pra não pegar a mesma do PC1. Reaproveita o cache
  2.5D do pt, então não refaz o movimento.
- Quem coordena é o PC1: tarefa `HipercoolPC2` (`fila.py pc2`, a cada 20 min, independente do render daqui),
  com o código em `bin/pc2.py`. Cada rodada: (1) traz o vídeo pronto + a tradução do roteiro (o SEO lê) e apaga a
  cópia de lá; (2) manda o que falta (cache 2.5D novo, roteiro, painéis) e dispara a próxima língua por
  `bin/pc2_rodar.ps1`. Estado: `idiomas.<lang>.pc2` no `fila_estado.json`; 2 falhas -> desiste daquela língua
  (`pc2_falhas`). Liga/desliga: `fila.py ligar-pc2 | desligar-pc2` (flag `config/PC2_DESLIGADO.json`).
- No PC2 o código fica em `C:\hipercool-videos` e os materiais em `C:\hipercool-materiais`, com as mesmas junctions
  do workspace. O `pc2_rodar.ps1` faz `subst D: C:\` só na sessão do render, então os caminhos fixos `D:\...` do
  código funcionam lá sem mudança. Processo criado por WMI: filho direto do ssh morre quando a conexão fecha.
- Mudou código? **Desde 16/10 o PC2 se atualiza sozinho**: toda rodada da tarefa `HipercoolPC2` compara o
  `bin/` daqui com o de lá (tamanho e data) e copia o que mudou ANTES de disparar o render da língua
  (`pc2.sincronizar_bin`). Se a cópia falhar, a rodada para e o render não começa. Ficam de fora os arquivos
  que começam com `_`, os `.bak` e os que só rodam no PC1 (fila, pc2, refazer_caps, lancamento_pt); `config/`,
  `secrets/` e `workspace/` nunca são copiados. `scp` manual só se quiser adiantar. Pacotes do venv de lá = os daqui.

## Mais efeitos e acabamento (13/10, só código, sem IA paga)

- **Recorte do personagem e closes** (`fx_parallax`, escolha no laço de clips do `hiper-pipeline`), modos:
  - `close`: punch-in no ROSTO, em painel de reação (`fx_detect.is_reacao_panel`) e de vez em quando;
    rosto pelo YOLOv8 de rosto de anime (`models/anime_face_yolov8s.onnx`, CPU, cache
    `<md5>.rostos.json`; acha rosto em ~50% dos painéis, o lbpcascade achava 10%). NUNCA em painel +18 ou
    sugestivo (score >= 0,25): o detector já confundiu lingerie com rosto;
  - `objeto`: close numa coisa pequena achada pelo recorte (1–10% do painel, sem rosto) quando a cena fala
    de objeto (celular, carta...);
  - `andar`: personagem de corpo solto (não cortado embaixo) atravessa a cena com passo; busto vira `foco`;
  - `parallax` (personagem cresce 17% e desliza contra o painel, fundo com desfoque de profundidade e
    balões nítidos); `foco` (câmera vai até o personagem); `impacto`; `tensao`.
  - No cap 1 isso dá ~50% dos clips com efeito (o vertical antigo tinha 16%). Log: `efeitos 2.5D/close`.
- **Trilha** (`fx_music`): ver seção abaixo.
- **Capa sensual** (`fx_acabamento._capa_sensual`, estilo @oporaodacidadela): mulher em busto grande (painel
  com decote/roupa curta pelo cache do Sightengine, SEM nada +18 e lingerie <= 0,6; rosto inteiro visível;
  recorte de pessoa, não o quadro) + protagonista reagindo + fala dela com seta + reação dele grande em
  amarelo. Sem painel que sirva -> capa antiga. `HIPER_CAPA_SENSUAL=0` desliga.
- **Concat**: `fx_clips._igualar_audio` refaz o áudio de clip com formato diferente (a abertura saía 44.1k
  estéreo no meio das falas 24k mono e o hindi de 13/10 saiu com o áudio quebrado).
- **Abertura**: ~3 s de montagem dos rostos da 2ª metade do capítulo, sem nada sugestivo (score < 0,25) nem
  propaganda (`HIPER_TEASER=0` desliga).
- **Capa**: painel com UM rosto de anime (`models/lbpcascade_animeface.xml`; precisa do OpenCV 4.x, a 5.0
  removeu a cascata). Personagem recortado grande com brilho, ou o painel enquadrado no rosto.
- **Cor e vinheta pelo clima** da cena (`EffectsManager.clima`). **Memes de comédia** (`sfx_memes`, máx. 1 a
  cada 8 clips).
- **Passe final em Quick Sync** (GPU Intel; cai no x264 se falhar; `HIPER_QSV=0` desliga).
- **Propaganda no MEIO do capítulo** (`fx_detect.is_propaganda`, pela descrição da visão): o painel é pulado.
- **Trecho preto** num painel escuro da própria arte não reprova a validação (`descontar_pretos_da_arte`).
- **Claude/Gemini via proxy** (`bin/claude_client.py`, `secrets/claude_proxy.json` = proxy do Claude Code):
  - Sonnet do Kiro no `haiku_helpers` e como reserva da narração;
  - Gemini do proxy como reserva do `gemini_llm` e como principal na localização da censura.

## Trilha (`bin/fx_music.py`) e trilhas novas (`bin/baixar_trilhas.py`)

- `assets/trilhas/prioritarias/` = as que o dono separou ("em alta": Passo Bem Solto, Montagem Bailão,
  Cornfield Chase/"ciência"...). Tocam ~85% das vezes que existe uma do clima, FORA da blocklist de copyright
  (escolha do dono; risco = reivindicação de Content ID, não strike). Clima e início fixo em
  `prioritarias/climas.json` (`"inicio": s` = a faixa sempre começa nesse segundo; a Bailão começa no
  "clima perfeito, noite enluarada"). Arquivo novo sem entrada vale pra neutro/calmo.
- Nenhuma faixa passa de 100 s seguidos (`HIPER_TRILHA_MAX_S`); crossfade entre faixas; volume nivelado; sem
  toque de celular/efeito/meme nem faixa < 1 min; evita as dos últimos vídeos (`workspace/cache/trilhas_recentes.json`).
  Antes de 13/10 um só clima "neutro" tocava o vídeo inteiro (caiu no toque "Nokia ringtone arabic").
- Baixar pra avaliação: `python bin/baixar_trilhas.py --lista config/trilhas_buscar.txt` (ou buscas soltas) ->
  `hipercool-materiais/_curadoria/_a_aprovar/trilhas/<data>/`. Proxy de `secrets/proxies.txt` só se o YouTube
  bloquear. Aprovada = mover pra `prioritarias/`.

## Estado em 14/10 (o que roda sozinho e o que falta)

- **Fila automática** (`HipercoolFila`, a cada 20 min): posta pt -> renderiza o próximo pt (até 2 adiantados)
  -> no tempo livre (`fila.tempo_livre`): 1 língua por ciclo (render+post), a parte 16:9 de 1 capítulo (pt e
  línguas) e as compilações 16:9 (1ª com 2 caps, depois a cada 3).
- **Canal pt = InovareManhwaVerse** (`canal_pt`), mas `postar_pt=false`: o Studio do canal está preso no aviso
  de ADVERTÊNCIA de direitos autorais (1 advertência, 08/10). O dono fecha o aviso/faz o curso; o e9 confirma
  no `--checar` e troca `postar_pt` pra true. A migração já foi feita (`fila.py migrar-canal`): a série recomeça
  do cap 1 lá. O estado de postagem é por canal (`workspace/postagens/<video>__<canal>.json`).
  Com o pt segurado, as línguas seguem sem esperar o pt.
- **Línguas**: hi, id, it, ru, th, vi ativas (o dono logou ind/thai em 14/10). fr/en: o código fala francês e
  inglês, mas os canais estão pausados no postador (`ativo: false`).
- **SEO** (`bin/seo.py`): agente de título/descrição/tags (Sonnet do proxy -> Gemini), 1 chamada por capítulo/
  idioma/tipo, em cache (`workspace/cache/seo/`, chaves `v2|...`).
  - Desde 15/10: NUNCA o nome da obra (`_sem_obra` apaga). Palavras buscadas do gênero vêm de
    `config/seo_palavras.json` + `obras[].generos`.
  - O completo sai com 3 títulos (busca/provocacao/curiosidade) em rodízio; o estilo fica gravado na postagem.
  - Detalhes em `docs/seo_titulos.md`.
- **Capas** (`bin/capa_ia.py`): ver `docs/MELHORIAS_PARA_TODOS_OS_PROJETOS.md` §2 e a memória do dono.
  - Shorts com capa 9:16 (`capas_short`).
  - Obra de fantasia/ação ganha 1 variante de batalha (`POSES_GENERO`).
- **Extras do Studio** (`D:\postador-de-videos\bin\youtube_studio_extras.py`): tela final, comentário fixado,
  teste A/B, vídeo relacionado dos Shorts e limpeza de rascunhos.
  - Plano por vídeo no estado da postagem (`extras`), executado por `postar_hipercool.rodar_extras` a cada
    rodada da fila (máx. 3 vídeos).
  - Pendente (canal em verificação, vídeo agendado) repete a cada 3 h.
- **Vídeo longo**: plano da biblioteca de efeitos em `docs/longo_efeitos.md`.

## Vídeo longo 16:9 (`bin/hiper-longo.py`)

Reaproveita narração, vozes, censura, recortes e rostos do cache do vertical (zero IA nova). Cada fala vira um
momento: `tira` (painel no meio e vizinhos apagados dos lados), `close` (painel + rosto grande ao lado) ou
`recorte` (painel + personagem recortado saindo dele). Legenda desenhada no quadro, Quick Sync, trilha do fx_music.
- `python bin/hiper-longo.py --obra the-inheritor --caps 1-10 --compilar`
- Saída `workspace/videos/longo/<obra>/capNN.mp4` (cache por capítulo) e `<obra>_capsAA-BB.mp4` + `.json` com
  a lista de capítulos com minuto pra descrição. O vídeo "cresce": cada compilação vai do cap 1 ao último pronto.
- Seleção de painéis compartilhada com o vertical em `bin/hp_paineis.py` (precisa ser idêntica, senão a narração
  em cache desalinha).
- A fila (`fila.longo`) renderiza os capNN.mp4 no tempo livre (estado `longo` no `fila_estado.json`; `"longo": false`
  no `config/fila.json` desliga). Desde 23/10 a compilação sai de `fila.compilados_do_dia` (1..N do capítulo do dia) e
  a postagem é automática, na ordem da dona (seção "Postagem"). Só o compilado mais novo fica no disco (o postado e os
  avulsos `capsNN-NN` ficam).
- Cap 1 (6,4 min) levou 11 min de render na UHD 620.

### Abertura com voz humana no compilado (`bin/intros_voz.py`, 15/10)
O feed do YouTube toca o começo do vídeo longo no hover e o público usa isso pra ver se a voz é de IA. Em pt, o
`compilar()` põe na frente do capítulo 1 uma abertura com VOZ HUMANA (saudação + "deixa o like/se inscreve" +
"bora pra história") sobre a capa do compilado, com legenda palavra a palavra, selo INSCREVA-SE/LIKE e a nossa trilha.
- Vozes SÓ dos canais que autorizaram o dono (15/10/2026): `config/intros_voz.json` → `autorizados`. Nunca o nome
  do canal/criador, obra, personagem, trama nem palavrão na fala; uma abertura = um criador.
- Tela: capa nítida só no 1º meio segundo (a prévia do feed continua a miniatura), depois capa desfocada com MEMES
  ANIMADOS sem som (catálogo do fx_memes, tags por momento da fala: saudação/like/bora; nada negativo) + legenda +
  selo LIKE/INSCREVA-SE. Fala com `"lugar": "meio"` (só pedido de like) entra numa troca de capítulo perto de 1/3
  do vídeo (`hiper-longo._cap_do_meio`, nunca antes de 4 min), de outro criador; `meta["intro_meio"]`.
- Só vale fala com legenda conferida (`texto_ouvido` no registro: o `montar --texto` grava). O Whisper erra gíria.
- A música do canal sai (separação de voz `UVR-MDX-NET-Voc_FT`, venv `D:\tools\separador`): Content ID.
- Rodízio: cada compilado POSTADO leva uma diferente (`registrar_uso` no `postar_longo`); depois de 2 usos de cada,
  Thompson por `registrar_resultado` (retenção dos 30 s — leitor do Studio ainda falta). Estado em
  `workspace/intros_voz_stats.json`; desligar uma = `"ativa": false` em `config/intros_voz.json`.
- O `.json` do compilado guarda `intro_voz`; a lista de capítulos já desconta a abertura (cap 1 fica em 00:00).
- Emenda sem re-encode: a abertura sai no mesmo encoder do capítulo 1 e é conferida (formato + decodificação da
  emenda); se falhar, o compilado sai sem abertura (log `[!] ... sem abertura`).
- Ferramenta: `colher` (começo/fim de 4 vídeos por canal, Groq) → `texto`/`palavras` → `cortar` + `checar` →
  `montar` (voz separada, corte no silêncio, nível) → `previa ID` (vídeo pra ouvir) → `lista`.

## Postagem (`bin/postar_hipercool.py`)

### ORDEM DE POSTAGEM POR DIA — REGRA DA DONA (23/10/2026)
Palavras dela: "pode postar os vídeos hipercool normal, sendo como eu falei, e deve estar documentado: um vídeo do
capítulo feito em retrato, um do capítulo feito em paisagem, um compilado do cap 1 até o atual do dia que foi postado
(ex.: se postou o cap 5 retrato e paisagem, aí posta compilado do 1-5 em paisagem também), só [depois] shorts cortados
dos capítulos e os de resumo. Como sai muitos, mais [ou menos] ordem de prioridade é essa, todo dia."

Por dia e por canal (pt e cada língua ativa, dia de lá):
1. completo do capítulo N em RETRATO 9:16 (`postar_pt` / `postar_idiomas`, 1 por dia);
2. o MESMO capítulo em PAISAGEM 16:9 (`<obra>_capsNN-NN.mp4`, "avulso");
3. COMPILADO 16:9 do cap 1 até N (`<obra>_caps01-NN.mp4`) — todo dia que sai capítulo novo (antes: 1º com 2 caps e
   depois a cada 3, `longo_primeiro`/`longo_a_cada`, que não valem mais);
4. Shorts cortados dos capítulos; 5. Short de resumo (`short_resumo.py`, `"tipo": "resumo"`), por último em cada
   capítulo (só pt: a descrição dele é fixa em português).

Como está no código (`bin/fila.py`): N = último capítulo cujo completo já subiu no canal (`_caps_postados`);
`_longos_do_dia` diz o que falta de 2 e 3 (estado `_longo_cap_postado` e `_longo_postado` por `obra|canal`);
`_postar_longo_da_vez` sobe o próximo, chamado dentro de `postar_pt`/`postar_idiomas` DEPOIS do completo e ANTES dos
Shorts, com o mesmo `_pode_postar` (pico, intervalo, teto do dia). O arquivo ainda não existe = os Shorts seguem (não
trava). Quem produz: `compilados_do_dia` no `tempo_livre` só COLA (`hiper-longo --compilar` com os capNN.mp4 prontos:
concat `-c copy` + abertura de voz/CTA de ~10 s, minutos, fora da fila_render); falta capNN.mp4, ou o do capítulo do dia
é mais velho que o vertical atual (`_seg_velho`), quem renderiza é o `longo()` pela fila_render (pesado, ~11 min/cap).
`postar_hipercool --longo OBRA --longo-caps A-B` posta aquele arquivo (não o mais novo). O avulso e o compilado
convivem no disco (o `compilar` não apaga um pelo outro).
Exceções que continuam valendo: nudez achada segura aquele vídeo (a análise olha cada capNN.mp4; desde 23/10 o
veredito do vertical só vale pro capNN.mp4 feito DEPOIS dele); nenhum canal fica um dia sem postar; cotas/pico/
intervalo do postador. Língua com capítulo pulado por nudez nunca fecha o 1..N (o compilado fica esperando e os
Shorts seguem). O compilado começa em 1-2 (N = 1: só o avulso).
- **23/10 (2ª leva, dona)**: trava `longo_pt_desde` TIRADA ("é só postar o cap 1 nele, já foi refeito, está
  diferente"). O compilado só cola capNN.mp4 feitos DEPOIS do vertical atual (`_seg_velho(..., estrito=True)`): os
  16:9 pt de 15-16/10 (marca do canal antigo, vozes velhas) são refeitos pelo `longo()`, um por ciclo, o do capítulo
  do dia primeiro. **Teto do dia = o real do canal** (`politica.teto_canal`, no `_pode_postar`), não o `max_dia` do
  fila.json. Conferido em 23/10: Manhwa Noturno = 3 (cadastro `max_dia` 3, rampa 0; NÃO está acima de 3); línguas = 4
  (política 4, rampa 0). Subir o do Manhwa Noturno é na rampa/cadastro do postador (dona decide).
- **Drive**: o hipercool já está no `D:\manhwa-react\scripts\backup_drive.py` (via `catalogo.py`): o postado sai 2 h
  depois, com conferência tamanho+md5, e fica no PC enquanto o capítulo/língua ainda tem Short a postar
  (`_hipercool_em_uso`). Os capNN.mp4 16:9 nunca são postados sozinhos, então nunca saem (o compilado precisa deles).
- **No PC só o do dia (29/10, dona)**: `fila._janela_do_canal` = por canal, os que já subiram e cortam Shorts + os N
  próximos completos na ordem da postagem (nudez não ocupa vaga; N = `janela_local`, 1 com o D: < 10 GB). O resto sai
  pelo `backup_drive.hipercool_estoque` (sem exigir 16:9 feito nem línguas prontas: hiper-longo e línguas usam caches/
  painéis, não o mp4) e volta pelo aviso `_NO_DRIVE.txt` quando entra na janela; rc 3 do Drive com mp4 no PC = envio
  não completou, o aviso sai. Postado: vertical/Shorts 2 h, longo/ 3 dias. `_nudez` lê o veredito também de vídeo no
  Drive. 29/10: a dona liberou a nudez de todas as línguas (mesmo critério do pt de 19/10).

Posta a versão **censurada** (completo + Shorts) via sistema de postagem do manhwa-react (Chrome logado). O
completo sobe com a capa (`.capa.jpg`) e na playlist "<Obra> — Recap" (suporte do postador desde 13/10).

```
# 1) revisão: gera <censurado>.folha.jpg e mostra o plano (não posta)
python bin/postar_hipercool.py --video workspace/videos/VIDEO_NORMAL_ULTIMO.mp4
# 2) depois de conferir a folha:
python bin/postar_hipercool.py --video workspace/videos/VIDEO_NORMAL_ULTIMO.mp4 --aprovado
#    --no-shorts / --no-completo / --ensaio
```

- Aborta se não houver a censurada do pipeline novo (meta com `censura`) ou se a validação dela falhou.
  Nunca posta o vídeo normal.
- Retoma: o que já subiu (`workspace/postagens/<censurado>.json` + ledger do postador) não sobe de novo.
  No limite diário do canal (3/dia) ele para; rode o mesmo comando no dia seguinte.
- Shorts: `split-shorts.py` corta nas **fronteiras de painel** gravadas no meta (`acabamento.fronteiras`),
  com 30–58s por parte, nunca no meio de uma fala. Short com mais de 50% do tempo censurado é pulado.
- **pt em 2 canais (29/10, dona)**: Shorts no Manhwa Noturno (`canal_pt`); completo + 16:9 avulso + compilado no
  InovareManhwaVerse (`canal_pt_longos`, `fila._canal_longos_pt`). Sem a chave, tudo volta pro `canal_pt`.
- **Shorts do cap 1 no Manhwa Noturno (16/10)**: `bin/shorts_a_cada_2h.py`, tarefa `HipercoolShorts2h` (20 min), com a
  agenda do dono (2 em 16/10, 3 em 17/10 às ~10h/15h/20h). Usa os 5 cortes de `workspace/shorts/the-inheritor-cap1`
  (vindos de "SHORTS NOVOS (ver como ficaram)"); desliga sozinha no fim. Não recorte essa pasta antes disso.
- **Sempre AGENDADO, nunca público na hora — é a PROTEÇÃO do canal (dono, 19/10).** Mesmo "postar agora" sai agendado
  pra 10+ min (o postador força: `politica.horario_obrigatorio`, mínimo agora+11). Por quê: com o vídeo agendado o
  YouTube faz a checagem de direitos autorais ANTES de ele ir ao ar; se achar problema, o aviso vem antes e o vídeo
  não é publicado — e vídeo que não foi ao ar não dá advertência ao canal. Público direto pula essa proteção. Nunca
  "corrigir" isso pra público, nem tratar o agendamento como atraso.
- Canal padrão: `inovaremanhwabr` (`--canal` pra trocar). Projeto `hipercool` (`PROJETO` do postar_hipercool, desde 18/10;
  onde ele pode postar vem do cadastro `D:\postador-de-videos\config\canais.json`).
- Backup e reuso: 3 dias depois de publicar, o vídeo postado (caminho registrado pelo `marcar_aprovacao` + nome no ledger) vai para o Google Drive `manhwa-drive:videos-backup/hipercool/` e sai do PC (`D:\manhwa-react\scripts\backup_drive.py`, tarefa diária BackupDriveVideos). Onde cada vídeo está e onde já foi postado: `D:\postador-de-videos\bin\catalogo.py` (os shorts já postados no YouTube são reaproveitados no TikTok pela conta inovaremanhwaverseita, baixando do Drive). Não reaproveite como entrada um vídeo já postado.

## Métricas automáticas (`bin/metricas.py`, 15/10)

Coleta e decisão de performance dos vídeos via YouTube Studio analytics (`youtube_studio_extras.metricas`).
- **Quando roda**: `fila.py postagem` chama `metricas.rodar()` uma vez a cada 20h.
- **O que coleta**: vídeos longos (completo/longo) com 48h–21 dias, máx 6 por rodada, re-lê a cada 72h.
  Pega views, impressões, CTR, duração média e retenção aos 30s.
- **Decisões** (quando tem ≥3 amostras e ≥7 dias):
  - **Compilados**: ret30 acima da mediana → `intros_voz.registrar_resultado(venceu=True)` (Thompson sampling).
  - **Completos**: CTR acima da mediana do canal (≥100 impressões) → `seo.registrar_resultado` (teste A/B de título).
- Estado em `workspace/metricas.json`. CLI: `python bin/metricas.py --agora` ou `--so-decidir`.
- **ATENÇÃO**: parsing dos rótulos da página de analytics NÃO foi testado em página real (15/10 noite).
  Se `metricas.py` falhar, verificar se YouTube Studio mudou os textos das abas/linhas.

## Aberturas com voz humana (`bin/intros_voz.py`, 15/10)

Compilados 16:9 e vídeos longos pt começam com ~8s de NARRADOR REAL (não edge-tts) + trilha + memes animados.
- **Canais autorizados** (15/10): @oporaodacidadela, @mangaticos, @MattzManhwa, @SR.GUUGOU, @MomoManhwa, 
  @mikemanhwa, @DrezinNimes, @omelhormanhwa, @KkVirjao, @Doinsuka, @iJaxManhwa, @Solem_8037, @Jubertim, 
  @IkiManhwa, @solem_sun. Montadas em `config/intros_voz.json`, campo `intros[].texto_ouvido` (conferido).
- **Como funciona**: `hiper-longo.compilar()` chama `intros_voz.para_compilado()` (pt only), que:
  - Escolhe intro por Thompson sampling (lugar="abertura" ou "meio", evita canal repetido).
  - Monta segmento com capa sharp 0.3s + capa blur com memes GIF/vídeo SEM som + legenda + selos + música.
  - Meio: frase DEPOIS do cap k (decidido por `_cap_do_meio`), no momento do like.
- **Memes**: MEME_TAGS (saudacao/like/bora), filtros MEME_FORA e MEME_DESC_FORA, joinha prioridade no like.
- **Métricas**: ret30 acima da mediana → `registrar_resultado(venceu=True)` (bin/metricas.py).
- **NUNCA**: palavrão, nome do canal/criador, obra/personagem, Shorts verticais.
- CLI: `python bin/intros_voz.py lista` / `previa <id>`.

## Regras

- Um render pesado por vez na máquina (o manhwa-react também renderiza; o pagefile é pequeno).
- Nunca dizer "pronto" sem conferir o `acabamento.validacao` do `.meta.json` (ou ffprobe: áudio >5s menor que o vídeo = quebrado).
- Não regerar áudio à toa (`--force-tts` só com motivo). Commit/push só com confirmação.
- Narração de capítulo NOVO: chaves diretas do Gemini (os modelos mortos foram tirados da lista em 13/10). Se
  falharem, entram os Gemini do proxy e depois o Claude (`narration._claude_proxy` → `claude_client`).
- `--hyperframes-karaoke` precisa do Chromium do Playwright, que não está instalado.

## Decisões do dono (16/10/2026)

- **A censura "Exodia" que o dono lembrava JÁ É o `fosco` de hoje** (negativo + pixelão + cinza +
  ruído + véu branco + borrão + balões nítidos por cima, em `censura_visual.censurar_fosco`).
  Testado em 16/10: tirar o borrão NÃO funciona, porque o passo que recoloca os balões nítidos
  (`lumakey`) também recoloca pele clara, e a cena volta a aparecer. Detalhe, prova e as três
  alternativas em **`docs/censura_exodia.md`**.


- **POSTAR POR API ESTÁ PROIBIDO. Todo upload vai pelo NAVEGADOR.** Canal novo só posta depois de
  entrar em `D:/postador-de-videos/config/youtube_navegador.json` com `"usar": true`. A regra agora
  é cumprida pelo código: `politica.postar_youtube` RECUSA o upload quando o canal não está marcado
  (`config/politica.json` → `proibido_postar_por_api: true`). Como isto apareceu: em 16/10, 8 dos 23
  uploads do dia subiram pela API (`script=youtube_poster.py` no ledger), todos do ManhwaReact-ia, e
  ninguém tinha notado. **Pra conferir:** o ledger do postador guarda o `script` de cada upload; se
  aparecer `youtube_poster.py`, é erro — ponha o canal no navegador.


- **Trilhas ficam como estão.** O risco de Content ID das prioritárias (Hans Zimmer, Re:Zero, HxH, Tensura,
  MC Jhey) é assumido: o dono já viu canais do nicho usando as mesmas. Não propor troca de novo.
- **Cena +18 e cartaz "QUER SEM CENSURA?": PERGUNTAR, não decidir.** Quando houver pelo menos 10 vídeos com
  métricas lidas (retenção e CTR), levar os números ao dono e perguntar se o público assiste ou pula esses
  trechos. A pergunta é o entregável — não mudar sozinho ao chegar nos 10.
- **O 16:9 por capítulo pode virar o vídeo principal**, mas o dono vê ANTES: quando ficar pronto, abrir a
  pasta dele e avisar, sem postar. (Superado em 23/10: a dona mandou postar o 16:9 de cada capítulo logo depois do
  retrato — seção "Postagem", ordem por dia.)
- **Shorts: duração dinâmica.** Nada de 55 s fixos. Cada parte começa num ponto que faz sentido e termina num
  gancho que dê vontade de ver a próxima; pode cortar trecho que não ajuda. Além disso, fazer **Short de
  RESUMO** como subproduto (como o dono já faz nos reacts) e comparar as visualizações com as do Short de
  trecho — a ideia é promover a história original.
  **Feito em 16/10 (tarde):** `bin/short_resumo.py`. A dúvida de como separar um do outro se resolveu olhando
  o canal que o dono passou (@kaijinre): lá o Short **sem "Parte N" no título** é a porta de entrada e rende
  outra ordem de grandeza — 513 mil visualizações contra 2,4 mil da "Parte 2" da MESMA obra; outros três sem
  parte fizeram 433 mil, 231 mil e 37 mil. Então o resumo sai com título `<emoji> <gancho em CAPS>...
  #manhwa #manga #anime`, sem parte, e com `"tipo": "resumo"` no meta, que é por onde as métricas vão separar
  os dois. O conteúdo vem dos momentos que o editorial já marcou no `.meta.json`, cada um virando um BLOCO de
  painéis seguidos (o painel do impacto dura 3 a 8 s e sozinho não conta nada: o bloco cresce pra trás pra
  pegar a fala que arma o momento — no cap 1, 28,7 s viraram 68,6 s). Não gera narração nova nem chama modelo,
  e pula painel censurado. O postador **gera e não posta**: a postagem espera o dono ver.
- **Marca d'água por canal**: o `@` de cada língua está em `config/fila.json` → `idiomas.<lang>.handle`
  (conferidos em `D:/postador-de-videos/config/rede_canais.json`). O pt é `@manhwanoturno` (hp_common).
- **Não vai contestar** o bloqueio dos recursos avançados no Studio do canal antigo: a série seguiu pro canal
  novo. Comentário fixado, vídeo relacionado e teste A/B seguem indisponíveis lá, e isso não é mais pendência.

## Controle de versão (16/10)

O projeto passou a ser versionado de verdade: antes o git rastreava **um** arquivo só e não dava pra saber
quem mudou o quê nem voltar atrás — com duas sessões editando os mesmos arquivos no mesmo dia, isso custou
caro. Agora há `.gitignore` (deixa de fora `secrets/`, `workspace/`, `venv/`, `models/`, `assets/`, `logs/`,
mídia e `.bak`), `.gitattributes` (fim de linha: `.sh` com LF, senão quebra no PC2) e um commit local com o
estado de 16/10. **Nada foi enviado ao GitHub** — push só com confirmação do dono.
As flags `config/FILA_DESLIGADA.json` e `config/POSTAGEM_DESLIGADA.json` ficam FORA do git de propósito: é a
existência do arquivo que desliga a produção, e um `git checkout` apagaria o arquivo religando tudo sozinho.
Antes de mexer no código, `git status` mostra o que a outra sessão já alterou.

## Cópia velha dos módulos no postador (corrigido em 16/10)

`D:/postador-de-videos/bin` tem **22 arquivos com o mesmo nome** dos de `bin/` daqui (censura_visual,
gemini_llm, effects_engine, split-shorts, tts_cache...). O `postar_hipercool.py` punha o caminho do postador
no INÍCIO do `sys.path`: qualquer import feito antes das funções carregava a cópia velha, que ficava em
`sys.modules` o resto do processo — foi assim que a censura antiga rodou escondida. Agora o postador vai no
FIM do path e o `bin/` daqui no começo (`postar_hipercool.py` ~linha 35); os módulos que só existem lá
(`politica`, `youtube_studio_extras`, `youtube_web_poster`, `catalogo`) continuam sendo achados.
**Ao criar arquivo novo em `bin/`, confira se o nome já existe no postador.**
