# PLANO PRO AGENTE — Parallax 2.5D (movimento real) com cache + cron + integração seletiva

> Cole isto pro agente implementador. Trabalhe em `D:\hipercool-inferior-fix`.
> Esta é a feature "movimentação real nas imagens" — substitui o Ken Burns falso por
> parallax 2.5D com depth real. Análise/testes já feitos: ver §"Contexto" abaixo.

---

## Contexto (já testado e validado — NÃO re-investigar do zero)
- Hardware das 3 máquinas é Intel SEM GPU dedicada → image-to-video com IA (Wan/SVD) está
  FORA. Parallax 2.5D local é o caminho. **A usuária já aprovou visualmente.**
- Teste isolado pronto em `_testes/parallax/test_parallax.py` + `saida_fake.mp4` e
  `saida_real.mp4`. **A versão "real" (Depth-Anything V2) ficou melhor e é a escolhida.**
- Medições reais nesta CPU (i5-8365U, sem GPU):
  - depth real (Depth-Anything-V2-Small via transformers): **~20s/painel** + 8s pra carregar
    o modelo (1x por processo). render ffmpeg do parallax: **~3s/painel**.
  - cap típico = 55-58 painéis → **~18min de depth em background por cap**.
- `transformers` 5.12 já foi instalado no venv `D:\hipercool-videos\venv`. torch é 2.12 CPU.
- Confirme cópia certa: `grep -c render_subtitles_short bin/hiper-pipeline.py` → >0.
- Pode ter render rodando: `tasklist | grep -i ffmpeg`. Se tiver, NÃO edite os .py em uso;
  o trabalho de cron/módulo novo pode rodar mesmo assim (arquivos novos).

## O que a usuária pediu (requisitos exatos)
1. **Movimento real nas imagens** via parallax (depth real), substituindo/complementando o
   Ken Burns atual.
2. **Cache das imagens/clips de parallax**, igual ao cache de áudio: gera UMA vez por painel,
   reusa em todas as variantes. Nunca reprocessar à toa.
3. **Aplicar SÓ na versão final que vai ser postada**: a versão **Gemini + vozes masculinas
   + censura**. NÃO aplicar na prévia edge (que é só pra revisão rápida).
4. **Fallback de cache na hora de gerar**: se a versão edge/prévia já tiver os clips de
   parallax prontos (pré-fabricados), REUSA; se não tiver, fabrica na hora na versão Gemini.
5. **Cron de pré-processamento em background**: assim que um cap está baixado (painéis
   prontos), um cron roda o parallax SEM IA-pesada nos painéis já baixados, aproveitando que
   a GPU/máquina fica ociosa a maior parte do tempo. Quando for gerar o vídeo de verdade,
   os clips já estão prontos.

## Arquitetura proposta (ajuste se achar melhor, mas explique)

### 1. Novo módulo `bin/parallax_engine.py`
Porte e limpe a lógica de `_testes/parallax/test_parallax.py` (versão `--real`). Funções:
- `depth_map(img_path) -> PIL.Image`: Depth-Anything-V2-Small via transformers. **Carrega o
  modelo 1x** (singleton de módulo — não recarregar a cada painel, são 8s). CPU.
- `build_parallax_clip(img_path, out_mp4, duration, seed=None) -> bool`: gera o clip 2.5D
  (3 camadas por limiar de depth + crop animado por camada, como no teste). Duração casa com
  o áudio do painel.
- Fallback: qualquer erro → retorna False, e o caller usa o `build_clip` atual (Ken Burns).
  NUNCA travar o pipeline.

### 2. Cache de parallax (espelhar o tts_cache)
- Dir: `workspace/parallax_cache/` (é junction compartilhada entre as cópias — bom, vale pra
  todas). Veja como `bin/tts_cache.py` faz: `hashlib.sha256[:16]` da chave.
- Chave do clip = hash de `(md5_da_imagem + duração_arredondada + versão_do_algoritmo)`.
  Incluir a duração porque o clip casa com o áudio; arredonde a 0.1s pra não furar o cache à
  toa. Incluir um `PARALLAX_ALGO_VER` (int) pra invalidar tudo quando melhorar o algoritmo.
- **Depth é cacheado separado do clip**: `parallax_cache/depth/<md5_img>.png`. O depth é a
  etapa CARA (~20s) e independe da duração → cacheia por imagem só. O clip (3s) recalcula
  rápido a partir do depth se a duração mudar. Isso atende o pedido #4 (não reprocessar
  imagens) de forma ótima: a etapa cara fica salva, só o ffmpeg leve re-roda se preciso.
- `lookup(img_path, duration)` → caminho do clip se existe, senão None.
- `store(...)` → salva clip + depth.

### 3. Integração no `hiper-pipeline.py` (SELETIVA — ponto crítico)
O clip de cada painel é montado em `hiper-pipeline.py:1170-1184` (build_clip_with_shake /
build_clip_animated / build_clip). Adicione um ramo de parallax ANTES, atrás de gate:
- **Gate de quando usar parallax** (requisito #3): só quando a run for a versão FINAL de
  postagem. Detecte por: `TTS_ENGINE in ("gemini","eleven")` (linha 706 já lê isso pra "male
  engine") **E** censura ligada **E** flag `PARALLAX=1`. Na prévia edge, NÃO gera parallax
  novo — mas USA o do cache se existir (requisito #4).
  - Pseudo:
    ```
    quer_parallax_novo = PARALLAX and engine_final and censura
    clip_cache = parallax_cache.lookup(panel_path, dur)
    if clip_cache:                      # ja existe (cron pre-fabricou): reusa sempre
        usar clip_cache
    elif quer_parallax_novo:            # versao final e nao tinha: fabrica agora
        ok = parallax_engine.build_parallax_clip(...); cacheia; se falhar -> build_clip atual
    else:                               # previa edge sem cache: Ken Burns barato de sempre
        build_clip atual
    ```
- IMPORTANTE: o clip de parallax já é o vídeo do painel — ele entra no MESMO lugar do
  `clip_path` que vai pro concat. Não muda áudio, legenda, censura, elementais (tudo isso roda
  DEPOIS sobre o vídeo concatenado e continua igual). Confirme que a duração do clip parallax
  bate exatamente com `durs_eff` (o projeto força isso pra não dar drift — ver concat).

### 4. Cron de pré-processamento `bin/cron_parallax_prefetch.py`
- Varre `workspace/panels/<obra>-capNN/` dos caps já baixados, e pra cada painel SEM clip no
  `parallax_cache` (na duração "padrão" — ver nota), gera o depth + clip em background.
- **Roda 1 painel por vez, prioridade baixa**, e SÓ quando a máquina está ociosa: cheque
  `tasklist | grep ffmpeg` — se já tem render rodando, PULA esta rodada (não competir por CPU,
  respeitar a regra "nunca 2 caps simultâneos" no espírito). A usuária disse que a GPU/máquina
  fica ociosa a maior parte do tempo — o cron aproveita isso.
- Nota sobre duração: no pré-fetch não sabemos a duração exata do áudio ainda (depende do TTS).
  Por isso **cacheie o DEPTH** (que independe de duração) no pré-fetch — é a etapa cara. O clip
  final com a duração certa sai rápido (~3s) na hora de gerar. Assim o cron entrega 90% do
  ganho (o depth pronto) sem precisar adivinhar duração.
- Registrar progresso em `logs/night-shift.md` (regra do projeto). NÃO commitar.
- Criar via mecanismo de cron do projeto (sessão principal, não subagent — proxy quebra
  subagent). Sugira intervalo tipo a cada 20-30min, off-peak.

## Flags (todas default seguras)
- `PARALLAX=1` liga o parallax na geração (default OFF = comportamento atual intacto).
- `PARALLAX_ALGO_VER` (int no módulo) pra versionar/invalidar cache.
- `PARALLAX_FORCE=1` força parallax mesmo na prévia edge (só teste).

## Validação obrigatória (sem gastar quota)
1. Gera um cap curto (cache de narração já existe, zero Gemini) com `PARALLAX=1` na config
   final (gemini+censura simulada) e confere VISUALMENTE com a usuária: movimento natural,
   sem tremor/artefato, profundidade boa.
2. ffprobe: áudio NÃO pode ficar >5s menor que vídeo (regra). Duração do clip = duração do áudio.
3. Roda 2x: a 2ª tem que reusar o cache (medir que não re-gerou depth — log "CACHE").
4. Confirma que a prévia edge SEM cache continua rápida (Ken Burns), e que SE houver cache do
   cron ela reusa.
5. NÃO afirmar "pronto" sem ffprobe + olho da usuária.

## Regras do projeto
- Persistir etapas caras (depth!) — nunca reprocessar. Variante normal/prévia intacta.
- Parallax só afeta a versão final postada (gemini+masc+censura), conforme pedido.
- Fallback total: depth/ffmpeg falhou → Ken Burns atual, pipeline nunca trava.
- Trabalhar local; commit/push só com confirmação. Cron não commita.
- Após estável+aprovado: congelar snapshot datado `bin/_VERSAO_CORRENTE_AAAAMMDD/` + atualizar
  `_VERSAO_CORRENTE_LEIA.md` (md5 novos). Não renomear diretório.
- ANTES de editar .py: `md5sum bin/*.py` e comparar com `_VERSAO_CORRENTE_LEIA.md`.

## Melhorias futuras (NÃO agora, anotar)
- Matting do personagem (separar do fundo) reusando o hyperframes/HeyGen → parallax premium
  (só o personagem se move sobre o fundo). Eleva de "foto com profundidade" pra "cena viva".
- API de image-to-video (fal.ai/Replicate free tier) só nos 3-5 painéis-clímax (o pipeline já
  detecta impacto via `is_impact_panel`). Busca de preços ficou pendente (web search fora do ar).
