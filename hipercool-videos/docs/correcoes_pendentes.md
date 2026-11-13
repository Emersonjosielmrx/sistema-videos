# Correções e melhorias — hipercool (estado em 14/10/2026, ~13h45)

Pedido do dono (14/10), nesta ordem: 1) vídeos dos outros idiomas rodando; 2) consertar a postagem;
3) correções que ele pediu; 4) melhorias sugeridas; 5) renderizar o cap 3 pra ver como ficou.

## O que está rodando agora (13h45)

- **Produção e postagem são processos separados** (pedido do dono: a produção nunca espera postagem):
  tarefa `HipercoolFila` (`fila.py ciclo`, só renderiza) e tarefa `HipercoolPostagem` (`fila.py postagem`,
  só posta), cada uma com liga/desliga (`HIPERCOOL_FILA_LIGAR/DESLIGAR.bat`,
  `HIPERCOOL_POSTAGEM_LIGAR/DESLIGAR.bat`). Log das rodadas agendadas: `logs/fila_ciclo.log`,
  `logs/fila_postagem.log`.
- **Cap 3 pt renderizando** (começou 13h22), depois cap 4, 5 e 6 em pt (`adiantado` 6). Depois do cap 6 as
  outras línguas entram no tempo livre (`idiomas_auto`), já com o cache 2.5D: cap 2 hindi monta o cache e
  as seguintes reaproveitam (primeiro teste do cache num render inteiro — conferir a linha "cache 2.5D").
- **pt segurado**: `postar_pt=false`. Os capítulos pt ficam guardados.
- **Francês e inglês bloqueados no postador** (`rede_canais.json` status `pausado`): fr = advertência de
  direitos autorais (strike 27/09, o Studio trava o upload nessa tela); en = YouTube bloqueou envios por
  avisos das diretrizes. Dono precisa resolver no Studio e voltar o status pra ativo; até lá a postagem
  pula esses dois (os vídeos continuam sendo feitos e ficam guardados).
- Rascunhos que sobraram das tentativas falhas no InovareManhwaVerse (ex.: https://youtu.be/1EavaQDrLbU)
  e no Hindi (Short parte 3): apagar no Studio (pedir confirmação ao dono antes).

## FEITO em 14/10 ~13h45 (Opus)

| O quê | Onde |
|---|---|
| **Produção × postagem separadas.** `ciclo` só renderiza (pt; no tempo livre 1 língua + 16:9). `postagem` posta pt, línguas e 16:9; pula a rodada se já houver um `postar_hipercool` vivo (um upload por vez). O estado (`fila_estado.json`) é gravado por mescla: cada processo aplica só o que ele mudou desde que leu e troca o arquivo inteiro de uma vez (testado: um não apaga o `postado` do outro). | `fila.py` `ciclo`, `postagem`, `gravar_estado/_mesclar` |
| **Postagem por país.** Cada canal de língua sobe 1 vídeo por rodada (completo primeiro, depois os Shorts, com `postar_hipercool --max-novos 1`), só no pico do país (`idiomas.XX.fuso` + `pico`, hora de lá com horário de verão via `tzdata`), com `intervalo_h` (2) desde o último upload do canal e até `max_dia` (3) por dia de lá. Canal sem nada há mais de `parado_h` (24 h) sobe o próximo na hora. Conta pelo ledger do postador (inclui outros projetos no mesmo canal). Canal bloqueado no postador é pulado sem tentar e sem contar falha geral. | `fila.py` `_pode_postar`, `postar_idiomas`; `config/fila.json` `postagem_idiomas`; `postar_hipercool --max-novos` |
| **Cache do movimento 2.5D.** O vídeo do movimento (numpy, a parte cara) fica em `workspace/cache/clips_2p5d` por imagem+modo+painel (máx. 15 GB, apaga os menos usados). Outro render do mesmo painel reaproveita esticando/encolhendo (0,75–1,4×) pra duração da fala nova e refaz só o passe barato. Nas línguas, o pipeline usa o modo que já está no cache em vez de sortear. Medido: 6,7 s → 2,3 s por clip 2.5D. Liga/desliga: `cache_clipes` no `fila.json`. | `fx_parallax.build_clip_parallax`, `_do_cache`, `modos_guardados`; `hiper-pipeline` (modo nas línguas) |
| **Visual diferente por língua.** Cor e vinheta já eram sorteadas a cada render; agora ~30% dos painéis sem balão saem espelhados em cada língua (escolha fixa por língua+painel, diferente entre línguas). Duração dos clips muda com a voz de cada língua. | `fx_parallax._espelhar`, `efx.variante` |
| Política do postador: o intervalo de 2 h da política agenda a publicação no Studio, e o agendamento só funciona com o Studio em pt/en — por isso fica 0 lá e o espaçamento é feito pela fila. ATENÇÃO: `politica.json` é global (vale pra todos os projetos do postador). | `postador-de-videos/config/politica.json` |

## FEITO em 14/10 (testado)

| # | O quê | Onde | Como voltar |
|---|---|---|---|
| Postagem | Tags passavam de 500 caracteres pela regra do YouTube (tag com espaço conta com aspas): caixa vermelha e upload travado no passo Detalhes. Corta pela regra certa (≤480). Testado: indonésio passou do Detalhes. | `postar_hipercool._caber_tags` (chamado em `postar()`) | — |
| Tremor | Painel com balão: impacto vira tranco curto (0,3 s no recorte / 0,7 s e 6 px no clip comum), tensão sem tremor. Antes tremia 45–60% do clip. **O tremor do clip comum nunca tinha funcionado**: as vírgulas de `max(0,1-t/...)` quebravam o filtro do ffmpeg e caía calado no clip sem tremor; agora a expressão vai entre aspas (medido: ±4 px até ~0,5 s, parado depois de 0,7 s). | `fx_parallax._render_camadas(com_balao)`, `fx_clips.build_clip_with_shake(shake_dur)`, `hiper-pipeline` (`com_balao`) | — |
| Close | Com balão, mostra o painel inteiro pelo tempo de ler (~15 letras/s, mín. 1,2 s, máx. 60% do clip) e só depois dá o zoom no rosto. Close de rosto menos frequente (reação 80→60%, espaço 2→3 clips; aleatório 45→30%, espaço 3→4). | `fx_parallax.espera_leitura`, `_render_close(t_pulo)`, `build_clip_parallax(texto)` | — |
| Objetos/poder | Close em objeto (espada, adaga, cristal...) e novo close em **poder** (mancha colorida e muito clara: energia, magia, fogo) com prioridade antes dos sorteios. Palavras de poder por palavra inteira ("poder" casava com "poderia"). Detector de brilho ignora pele, céu e cabelo (0 falsos em 205 painéis; acha esfera de teste). | `fx_detect.PODER_RE/is_poder_panel`, `fx_parallax.brilho_principal`, modo `poder` | — |
| Respiração | Recorte com escala oscilando ~1% (ciclo ~3 s): personagem não fica "colado". | `fx_parallax._render_camadas` | apagar 2 linhas "respiração" |
| Falas cortadas | (1) visão recebia o painel a **400 px/q55** (letra ilegível) → 1024 px/q80; (2) limite de **15 palavras** incluía o balão → balão transcrito COMPLETO, sem suavizar; (3) balão com "desculpe"/"não posso" virava **"Cena do manhwa"** (achava que era recusa) → só conta recusa fora das aspas; (4) palavras +18 eram trocadas **dentro da fala** ("Vou pro banheiro" → "Vou pro personagem") → só fora das aspas (último nível de retry ainda limpa tudo); (5) regra na narração: fala do balão quase literal, sem cortar nem suavizar. | `narration._sanitize_desc`, `_jpeg_bytes`, prompts, `CENSURA_LEVELS` | — |
| Voz trocada | (1) removido o "forçar 30% de personagens" que dava fala do narrador a **nomes sorteados de outra obra** (The Meek Cat) com gênero aleatório; (2) removido o fallback que inventava história com Joon/Noona; (3) **ficha de personagens**: a narração do cap N recebe nomes/gêneros dos caps anteriores (a voz é escolhida pelo NOME em `gemini_tts.voice_for_persona`: no cap 2 o protagonista virou "Rapaz" e mudou de voz); (4) revisão de quem fala: regra fixa por marca de 1ª pessoa ("obrigada", "estou cansado"...). | `narration.personagens_anteriores`, `falantes.py`, `hiper-pipeline` | `HIPER_REVISAR_FALANTES=0`; `falantes.restaurar()` desfaz (campos `persona_orig`) |
| Pastas | Vídeo novo nasce em `workspace/videos/<obra>/capNN/<idioma>/normal|censurado/`. Raiz organizada em 14/10 ~09h50: os atuais (inclusive os postados pt/hi/id) movidos pras subpastas; as 3 aprovações em `postador-de-videos/config/aprovacoes.json` reapontadas pro caminho novo (o catálogo e o backup do Drive ligam postagem→arquivo por esse caminho; conferido: as 4 postagens pt/hi/id/it ligadas). A fila acha pelo nome o vídeo cujo caminho gravado mudou. | `hp_paineis.pasta_video`, `hiper-pipeline`, `fila.video_do_estado`, `postar_hipercool.achar_censurado`, `refazer_capa` | — |
| Limpeza automática | Depois de um render bom, apaga da pasta do capítulo/idioma os renders anteriores do mesmo sufixo (superados, rebaixados, incompletos sem meta) com `.meta/.capa/.folha` — cada pasta (normal/censurado) só se a versão nova DELA saiu completa (com `.meta.json`). **Fica** o que tem aprovação no postador (postado ou indo postar) e o de outro sufixo (testes). Se o render falha, nada é apagado nem renomeado (antes o `_ULTIMO` anterior era rebaixado ANTES do render e, se ele caía, a fila perdia o vídeo). Ao começar um render, apaga `workspace/tmp/session_*` com mais de 12 h (render que morreu no meio; havia ~800 MB de jun/jul). Só nas pastas organizadas, nunca na raiz (é junction). | `hiper-pipeline._limpar_versoes_anteriores`, `_limpar_sessoes_velhas` | — |
| Só censurada nos idiomas | Em outra língua o normal é apagado no fim e a fila recebe a censurada. | fim do `run_pipeline` | — |
| Legenda nos idiomas | Em outra língua a fala do personagem também ganha legenda (o balão continua em português). | `fx_acabamento.finalizar` | — |

Testes feitos: detectores nos caps 1–2 (balão 50/96, rosto 28/96), render de close com espera (quadros
conferidos), render parallax/impacto/tensão com balão, sanitização com frases de controle, ficha
(`personagens_anteriores('the-inheritor', 3)` = Joo Inhyuk M, Noh Yeseul F, Professora F), compilação.
**Não testado ainda em vídeo inteiro**: sai no cap 3 (e nos idiomas renderizados depois das 08h20).

## FEITO em 14/10 ~13h (modelo inferior, pedir revisão às 14:50)

| # | O quê | Onde | Valores antigos → novos | Revisar |
|---|---|---|---|---|
| Animação: mais close | Close reação: espaçamento 3→2 clips, chance 60→70%. Close aleatório: espaçamento 4→3, chance 30→40%. Foco fallback: 65→75%. Objetivo: mais efeitos, menos painéis estáticos. | `hiper-pipeline.py` linhas 475, 489, 492 | `>=3 0.6` → `>=2 0.70`; `>=4 0.3` → `>=3 0.40`; `0.65` → `0.75` | Se ficar close demais ou repetitivo no cap 3, baixar de volta. |
| Poder: +6 termos | PODER_RE ampliado: barreira, maldição, selo, invocação, vórtice, escuridão. Testado sem falsos (poderia/poderoso/chamar → False). | `fx_detect.py:150` | — | Ver se pega coisas que não são poder visual no cap 3. |
| Objeto: +15 itens | OBJETO_KEYWORDS ampliado: poção, frasco, sangue, ferida, cicatriz, tatuagem, símbolo, emblema, mapa, lança, arco, flecha, bastão, cajado, cetro, luva, máscara, capacete. | `fx_detect.py:147` | — | "sangue" e "ferida" podem casar demais em manhwa de ação — se virar close em todo painel de luta, tirar. |
| Auditoria 8 áreas | Verificado que as 8 correções do dono (tremor, zoom delay, objeto, animação, voz, fala cortada, modelos, cap 3) estão ativas no código. | — | — | — |

## Análise de performance — onde o tempo vai (14/10 ~13h)

### Tempos medidos (logs reais)

| Etapa | PT cap 2 (94p) | TH cap 1 (106p) | Notas |
|---|---|---|---|
| Visão (Gemini) | ~5 min | 0 (cache) | Só na 1ª vez, outros idiomas usam cache |
| Narração (LLM) | ~0.5 min | 0 (cache) | Idem |
| Tradução | — | ~1 min | Só outros idiomas |
| Censura (SightEngine) | ~2.5 min | 0 (cache) | Cache funciona |
| **Clips + TTS** | **~31 min (57%)** | **~13 min (57%)** | **MAIOR GARGALO — ver abaixo** |
| Acabamento | ~2 min | ~3 min | Editorial, Groq, trilha, mix |
| **Passe final** | **~9 min (2×)** | **~5 min (1×)** | 720→1080 upscale+ASS+overlays |
| Capa + validação | ~1 min | ~1 min | — |
| **TOTAL** | **~54 min** | **~23 min** | — |

Projeção: 8 idiomas × 23 min = **~3 horas** por capítulo em idiomas (+ ~54 min do pt = ~4 h total).

### O que já está otimizado
- ✓ Clips em 720p, upscale 1080p no passe final (fx_acabamento.py:65)
- ✓ Quick Sync (GPU Intel) no passe final (~3× mais rápido que x264)
- ✓ Só censurado nos idiomas (pula passe final normal: -5 min/idioma)
- ✓ Narração/visão/censura em cache (0 min nos idiomas)

### MAIOR OPORTUNIDADE: reuso de clips entre idiomas

**Números medidos** (TH cap 1, 106 painéis):
- 2.5D (parallax/close/shake — numpy frame a frame): 47 clips, **~10s/clip**, total **8 min**
- Normal (build_clip — ffmpeg zoompan): 51 clips, **~5s/clip**, total **4.5 min**
- Total clips: **12.5 min** dos 13 min da etapa (o resto é TTS entrelaçado)

**Problema**: cada idioma recria os 98 clips do zero. A parte visual é parecida ao pt mas não idêntica
(porque a duração muda com o áudio do TTS em outra língua → zoompan avança diferente, efeitos ficam
em tempos ligeiramente diferentes). Isso já VARIA o vídeo naturalmente — o YouTube não identifica como
cópia porque:
1. A duração de cada clip é diferente (edge-tts em hindi fala mais rápido que em pt)
2. O vídeo total fica com tempo diferente
3. O áudio é completamente diferente

**Mas não é eficiente**: refazer 47 clips 2.5D (numpy ~10s cada) quando a imagem é a MESMA e só a
duração muda um pouco é desperdício. Se cachear o video sem áudio e adaptar a duração (speed up/down de
até ±25% via setpts=PTS*ratio, ou re-gen se >25%), pula a parte pesada.

**Solução proposta (cache de vídeo + adaptação de velocidade + variação visual)**:

1. No render pt, salvar os clips de VÍDEO (sem áudio) em `workspace/clip_cache/<slug>/clip_NNN.mp4`
   com metadata da duração e do tipo (2.5D ou normal)
2. Para outro idioma:
   a. Gerar TTS (edge-tts, ~1s/clip) → obter duração do áudio
   b. Se a duração do áudio for ±25% da do clip: usar setpts para ajustar velocidade do vídeo (praticamente instantâneo via ffmpeg)
   c. Se >25% diferença: regenerar esse clip (só os ~5% dos clips com muita diferença)
   d. Muxar o áudio novo no clip adaptado (ffmpeg -c:v copy -c:a aac, ~0.1s/clip)
3. **Variação visual por idioma** (custo zero ou mínimo):
   - Cor/vinheta diferentes por idioma (EffectsManager com seed=idioma)
   - Espelhar (hflip) ~30% dos painéis aleatoriamente por idioma
   - Overlay atmosférico diferente (neve em vez de chuva, etc.)
   - Tudo isso entra no passe final (que já roda) sem custo extra
4. O passe final continua rodando (~5 min) — as legendas/ASS são diferentes, a cor/vinheta aplicada lá

**Economia estimada**: de ~13 min/idioma para ~7 min/idioma (tradução 1 + TTS+mux 2 + acabamento 3 + passe final 5, mas acabamento+passe final se sobrepõem parcialmente). 8 idiomas: ~104 min → ~56 min.

**Não é tanto quanto cachear 100% porque** o passe final (5 min) precisa rodar sempre (legendas diferentes).
O ganho real é nos clips 2.5D: 8 min → ~0.5 min = **~60 min salvos** no total de 8 idiomas.

**Riscos**:
- setpts altera a velocidade do parallax/zoom (pode parecer estranho se muito esticado)
- O espelhar pode confundir se o texto do balão (em pt) aparecer espelhado → espelhar só painéis sem balão
- Precisa cache cleanup (os clips cacheados ocupam ~500 MB por capítulo)

**Status (14/10 13h45)**: IMPLEMENTADO só pra parte 2.5D (ver "FEITO ~13h45"); os clips comuns (ffmpeg
zoompan, ~5 s) continuam refeitos — cachear não compensa porque o passe que refaz cor/voz custa quase o
mesmo. Overlay diferente por língua: não feito.

## Revisão de falantes por LLM — testada e DESLIGADA

`HIPER_FALANTES_LLM=1` liga. No cap 2 o LLM propôs 3 trocas, 2 erradas ("Obrigada por me esperar" pro
rapaz) e não achou o erro real ("Ele faleceu, né?" na voz dela). O certo é olhar a SETA do balão: ver B2.

## PENDENTE

**Do lado do postador** (`D:\postador-de-videos`, da sessão claude-e9 — não estava aberta):
- `youtube_web_poster.py:587` corta tags em 480 caracteres SEM contar as aspas → mesmo bug pra outros projetos.
- Mensagem "O limite diário de envios foi alcançado" aparece no rodapé depois do Detalhes; o poster não
  reconhece e devolve `erro` (timeout de clique) em vez de `limite` → a fila trata como falha.
- A1: ler o passo "Verificações" (direitos autorais) antes de publicar; se acusar, não publica.
- D1: Short com "vídeo relacionado" apontando pro completo. D2: tela final/cards. D3: comentário fixado.
  D4: teste A/B de capa. D5: horário por fuso do idioma.

**No hipercool**:
- B2: OCR dos balões (manga-ocr local) + direção da seta → texto exato e quem fala.
- C1: upscale anime (Real-ESRGAN/waifu2x ncnn-vulkan) só nos painéis com close.
- C4: ritmo (tempo de tela por painel; corte no tempo da música na ação).
- C5: "no capítulo anterior" / "no próximo capítulo".
- D6: ler retenção dos caps 1–2 no Studio.
- E2: testar Gemini TTS nas línguas que mais rendem (hoje edge-tts).
- Longo 16:9: biblioteca de efeitos em `docs/longo_efeitos.md`.
- Normais de hi/id/it do cap 1 (~900 MB) ainda nas subpastas `normal/` (renderizados antes do "só censurada"):
  saem sozinhos no próximo render dessas línguas; apagar antes só com confirmação do dono.
- Shorts dos idiomas não ligam no catálogo (mesmo nome `the-inheritor_cap1_parteNN.mp4` em pt/hi/id/it e
  `workspace/shorts` não casa por nome) → o backup não leva pro Drive nem o reuso oferece pro TikTok/Insta.
- Mixagem: o abaixar a música sob a voz JÁ existe (`fx_acabamento.masterizar_audio`, sidechaincompress).

**URGENTE (21/10 02:30, achado pela sessão do painel — nada foi mexido):** `fila.py pc2-trazer` (tarefa
HipercoolPC2) trava 1 h inteira trazendo `cap09/th/censurado` (ssh pc2 "tar -cf - ..." | tar -xf, 0 CPU) até o
`TimeoutExpired 3600 s`; pid 16632 (até ~01:20) e pid 25640 (desde 01:35). Enquanto isso todo `fila.py pc2` sai com
"outro pc2 rodando" (controlador disparou hipercool_pc2 16 vezes hoje em vão) e o PC2 fica PARADO a noite toda.
Sugestão: trazer com timeout curto por pasta + checar progresso (tamanho do destino crescendo), pular a pasta que
falhou 2x e avisar; e não usar a mesma trava do disparo das línguas para o "trazer".
