# PROMPT — implementar efeitos "mexe-no-painel" (colar pro agente implementador)

> Gerado 2026-06-30. Fonte de verdade: este arquivo + TAREFA_15 + COMANDOS_PROTOTIPOS.sh + logs/night-shift.md.

```
CONTEXTO
Você vai integrar ao pipeline de vídeo (cópia D:\hipercool-inferior-fix) uma biblioteca
de ~90 efeitos que "mexem no painel" (zoom/recorte/máscara/camadas/tempo), TODOS já
prototipados, testados e APROVADOS pela usuária. NÃO precisa inventar efeito nenhum —
só plugar no pipeline. Trabalhe SÓ na cópia D:\hipercool-inferior-fix (edge-tts).
Python: use SEMPRE D:\hipercool-videos\venv\Scripts\python.exe. Exporte PYTHONUTF8=1.

ANTES DE QUALQUER COISA — LER (é a fonte de verdade):
1. TAREFAS_AGENTE/TAREFA_15_efeitos_mexe_no_painel.md
   → catálogo dos efeitos, encaixe de cada um (transição / dentro do quadro / legenda),
     as REGRAS de roteamento e as NOTAS TÉCNICAS do build de ffmpeg (obrigatórias).
2. _testes/COMANDOS_PROTOTIPOS.sh
   → o comando ffmpeg EXATO de cada efeito, como função pronta (A_*, B_*, C_*, D_*,
     Dp_*, F_*, G_*, I_*, J_*, K_*). É só copiar/adaptar por painel. Já validado.
3. logs/night-shift.md (entradas de 2026-06-30 e 2026-07-01) → histórico do que foi feito.

O QUE JÁ EXISTE E DEVE SER REUSADO (não reescrever):
- bin/elemental_transitions.py — módulo de roteamento por keyword/emoção já existente.
  O gancho no pipeline é bin/hiper-pipeline.py:1336 (flag ELEMENTAL_TRANS=1, import elemental_transitions).
  Siga EXATAMENTE esse padrão para os efeitos de painel.
- bin/parallax_engine.py::get_depth(img,(W,H)) — depth real (Depth-Anything V2, CPU, cacheado).
  Os efeitos de profundidade (parallax-3layer, depth-dolly, dofpull, fogdepth, bgslidedepth)
  dependem disso. Cacheie o depth por painel (já é cacheado por md5).
- rembg (já no venv) — recorte de personagem p/ o grupo D/D+. Gere 1x por painel e CACHEIE
  o PNG alpha (é caro, ~4s/painel). Não recorte o mesmo painel duas vezes.
- overlays de partícula em workspace/assets/overlays/elemental/ (fx_snow/godrays/etc.), usados pelo grupo I.

TAREFA
1. Criar um módulo de aplicação dos efeitos de painel (ex.: bin/panel_effects.py), portando
   os builders do COMANDOS_PROTOTIPOS.sh para Python (subprocess ffmpeg), com cache de
   recorte/depth por painel. NÃO altere a assinatura do pipeline; entre por trás de uma flag
   de ambiente (ex.: PANEL_FX=1), do mesmo jeito que ELEMENTAL_TRANS.
2. Roteamento por contexto (reaproveite a lógica do elemental_transitions):
   keyword/emoção da narração → efeito. Exemplos no TAREFA_15
   ("olhou/encarou"→facezoom, "de repente"→freezeimpact, "lembrou"→rewind, troca de cena→mangaslide).
3. Encaixe conforme a coluna "encaixe" do TAREFA_15: "transição" entra no lugar do xfade entre
   clips; "dentro" soma/substitui o zoompan do clip; "legenda" (word-strike) casa no relógio das legendas.

REGRAS OBRIGATÓRIAS (não violar):
- Grupo F (multi-painel): usar SÓ em clips SEM balão de fala. Nunca disparar F onde houver
  balão/texto no painel (atrapalha leitura). Regra da usuária.
- word-strike: EXIGE sincronia perfeita com a legenda — pendurar no MESMO relógio
  (effects_engine._CLIP_ABS_STARTS), reaproveitando a substituição de censura que já existe.
  Se não conseguir garantir a sincronia, NÃO ative o word-strike (deixe atrás de flag desligada).
- Grupo K (ritmo): os protótipos usam batida MOCK fixa. Ao integrar, plugue no BPM/áudio real
  da trilha (ver workspace/assets/trilhas/moods.json e a análise de áudio existente).
- NÃO repetir o mesmo efeito em clips consecutivos (mesma regra dos SFX do projeto).
- Efeitos com overlay .mov herdam a duração do overlay (~1.5s) → loopar o overlay p/ cobrir o clip.
- Notas técnicas do build (TAREFA_15): drawtext segfauta → texto só via HyperFrames;
  gblur/boxblur com eval=frame não funcionam → animar via sendcmd; imagem estática precisa -loop 1 -t N.
- Persistir etapas caras (depth, recorte). Nunca regerar à toa.
- Todas as variantes de saída reusam o MESMO áudio/visão (hyperframes vem do normal).

VALIDAÇÃO (sempre):
- Depois de gerar qualquer clip/vídeo, validar com ffprobe (duração, áudio, pix_fmt/alpha).
  Se áudio >5s menor que vídeo = QUEBRADO. NUNCA afirmar "pronto" sem validar com ffprobe.
- Rode um capítulo curto de ponta a ponta (com PANEL_FX=1) e confira o resultado antes de dar por feito.
- Snapshot datado após estável: bin/_VERSAO_CORRENTE_AAAAMMDD/ (cópia dos .py + _MD5.txt) e
  atualizar _VERSAO_CORRENTE_LEIA.md. NUNCA renomear diretórios (quebra venv/junction).

PRIORIDADE
- Comece pela família D/D+ (recorte de personagem + camadas) — é a preferida da usuária.
  Depois profundidade (I + depth), depois o resto. F por último e restrito.

ENTREGA
- Registrar o que fez em logs/night-shift.md.
- Trabalhar LOCAL; commit/push só com confirmação da usuária.
- Se travar/faltar contexto, o TAREFA_15 + COMANDOS_PROTOTIPOS.sh + logs/night-shift.md têm tudo.
```
