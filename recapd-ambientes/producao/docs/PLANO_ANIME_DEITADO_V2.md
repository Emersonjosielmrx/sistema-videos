# Plano de Arquitetura — Recap Anime DEITADO V2

> Documento mestre de planejamento. Escrito em 2026-07-27 enquanto o render de validação rodava.
> NADA aqui está implementado ainda — é o blueprint detalhado pra execução.
> Fonte das decisões: conversa com a dona (ver memória `anime-deitado-blueprint-graus`).

---

## 0. Contexto e estado atual

- Pipeline de recap deitado (16:9, 1h+) roda no worker PC2 (`C:\recapd-e-animes`), disparado via daemon HTTP porta 8772.
- Fonte = vídeo de recap de anime do YouTube. Re-narra em PT-BR (voz própria), descaracteriza pra anti-ban.
- Máquinas: **só Intel UHD 620, SEM CUDA**. Decodifica HEVC em hardware (Quick Sync). Qualquer efeito tem que rodar em CPU ou iGPU sem depender de GPU dedicada.
- Fixes de duração aplicados em 2026-07-27 (ver `PLANO` seção 1). O pipeline atual gera 1 clipe por frase de roteiro, concatena com xfade, adiciona música dinâmica e queima legendas.

### Arquitetura de execução atual (caminho crítico)
```
daemon run_task()
  ├─ anime_fetch: download + legenda/whisper
  ├─ t_lines = f(orig_dur)              # nº de frases-alvo
  ├─ anime_script.rewrite_to_file()     # LLM em blocos → roteiro.txt (1 frase/linha)
  └─ subprocess anime-pipeline.py --formato deitado
       ├─ anime_segments.build_segments()  # 1 clipe por frase (TTS + corte do source)
       ├─ fx_clips.concat_with_xfade()      # junta com transições
       ├─ effects_engine.add_dynamic_music()
       └─ anime_captions.burn_captions()    # legendas libass/PNG
```

---

## 1. Duração: PARAR de reduzir 1% (decisão da dona)

**Racional:** ao adicionar freezes, pausas dramáticas e transições, o vídeo naturalmente fica MAIOR que a narração pura. Ficar maior/diferente do original é melhor pro anti-ban do que ficar menor. Logo, não vale gastar trabalho mirando 99% da duração.

**Mudança:**
- `_pc2_daemon.py` linha ~88: remover o `* 0.99`.
- Fórmula nova: `t_lines = max(40, round(orig_dur / 3.8))` (3.8s de narração por frase, medido em job real com edge-tts).
- **PENDÊNCIA CRÍTICA:** o daemon precisa ser reiniciado pra carregar o `÷3.8` do disco. O job de validação (Q26qYNl9FyE) rodou com a fórmula ANTIGA (`÷6.6` = 1075 frases) que estava na memória do daemon antes do último upload. O disco já tem `÷3.8`. Reiniciar após o job atual terminar.
- Depois do fix, um source de 119min gera ~1880 frases (não 1075).

---

## 2. Motor de GRAUS 1-5 (o coração — decisão da dona)

### Filosofia central
**CPU e GPU no MÁXIMO, JUNTAS e em PARALELO.** Uma nunca espera a outra. O gargalo hoje é serial: gera TTS → gera clipes → concatena. No V2, tarefas de iGPU/CPU-pesado (rembg, depth, encode) rodam concorrentes com as de CPU-leve.

### Definição dos graus
| Grau | Tempo alvo/vídeo | Efeitos | Uso |
|---|---|---|---|
| 1 | ~render atual | Nenhum extra (só narração + xfade + música) | Rápido, teste |
| 2 | +20% | Tier 1 parcial: transições boas | Produção leve |
| 3 | +50% | Tier 1 completo: cutout+move personagem em beats + transições | Padrão |
| 4 | ~2× | Tier 1 + Tier 2 (parallax em stills, zoompan contextual) | Capricho |
| 5 | até 1 dia | Tudo: Tier 1+2+3, upscale, todos SFX, CTAs | Vídeo-vitrine |

Grau controla: quantos beats recebem efeito, se roda upscale, densidade de SFX, nº de CTAs.

### Paralelismo (implementação)
- Fila de trabalho com 2 pools: **pool-encode** (ffmpeg, satura CPU) e **pool-fx** (rembg/depth, satura iGPU+CPU restante).
- Enquanto o ffmpeg encoda o clipe N, o rembg já processa o frame do beat N+k.
- Pré-computar decisões de efeito (que efeito em qual clipe) ANTES do encode, em passo de planejamento — padrão "Motion Director em camadas" do hipercool: regra resolve >60% sem IA; só o resto vai pra LLM.
- **Nunca** deixar iGPU ociosa enquanto CPU trabalha e vice-versa.

### Botões no desktop
- .bat/atalhos por grau (Grau1.bat ... Grau5.bat) pra dona calibrar tempo×qualidade na prática.
- Cada .bat seta env `ANIME_GRAU=N` e dispara.

---

## 3. Efeitos por TIER (prioridade)

Aplicar sempre os MELHORES primeiro. Ordem de valor:

### Tier 1 (grau 2-3, sempre que possível)
1. **Transições boas** (styled_transitions `blend=screen`) — a dona destacou que transições podem ter prioridade MAIOR que movimentação. MP4 de transição são luz-sobre-preto, precisam blend=screen.
2. **CUTOUT_FX**: recortar personagem (rembg em 1 frame) e MOVER na tela sobre os beats dramáticos. Viável na 620 (~3.8s/recorte, ~12 por vídeo). Ver tabela em memória `cutout-fx-viabilidade-uhd620`.

### Tier 2 (grau 4)
3. **zoompan contextual** (PANEL_FX por regex de cena) — zoom/pan por tipo de momento.
4. **Parallax 2.5D SÓ em stills/cards** (não no corpo, a fonte já se move). Versão mood-aware do historias.
5. **Anti-repetição (EffectsMemory)** — não repetir mesmo efeito seguido.

### Tier 3 (grau 5)
6. Elementais (21 transições alpha aprovadas), mascote overlay, efeitos pontuais.

### Padrões obrigatórios (copiar do hipercool)
- **Fallback universal:** todo builder retorna False em falha → cai no Ken Burns. Efeito NUNCA trava pipeline.
- **Overlays em LOTES** (6-100 por passada, não filtergraph gigante) — senão estoura RAM do ffmpeg na 620.
- **Duração casada pelo áudio** (ffprobe + -shortest/-t).

---

## 4. Pós-produção SEPARADA (não-destrutivo)

Esteira de plugins após o render (modelo `pos_producao/` do veo). Cada plugin lê o vídeo, aplica, passa adiante. Configurável por grau.

### Etapas
1. **Gerar em 720p** no render pesado (rápido) → **UPSCALE no pós** (grau 4-5). Economiza tempo no gargalo.
2. **loudnorm** `I=-16:TP=-1.5:LRA=11` — masterização. ANTES/DURANTE/DEPOIS.
3. **Legendas** (já existe, manter).
4. **Abertura / cold-open empolgante** — resumo curto que prende: "hoje você vai ver um homem que superou tudo...". Gancho no início do deitado. TAMBÉM vira short (ver seção 6).
5. **Anúncios finais / CTA** — nossos comerciais colados (ver seção 5).
6. **Branding/watermark** (opcional).

---

## 5. APIs de mídia (OmniRoute — `157.173.207.22:20128`)

### Imagem = EXTREMAMENTE importante (decisão da dona)
- Combo `image-gen` do OmniRoute (Gemini/GPT image, failover automático). Doc: `docs/OMNIROUTE-MEDIA-COMBOS.md`.
- Uso #1: **CTAs personalizados** — gerar imagem do nosso comercial temático pra AQUELE anime (ex: anime de magia → arte de fundo mágica com nosso produto).
- Uso #2: thumbnails, backgrounds, cards da abertura.
- Mesma API que historias-em-frames usa (`omniroute_image.py`).

### Música / voz = delicado, POR ÚLTIMO
- Lyria (free tier) pra trilhas/moods. GPT Audio (pago) evitar.
- "Pode ou não ter música" — opcional/pausável, risco de acabar tokens. Dona quer várias opções antes de fixar.
- Veo3: só 1 abertura cinematográfica eventual, custo ~US$4/8s. Deixar por último de tudo.

---

## 6. Shorts como SUBPRODUTO do deitado (ideia-chave da dona)

Resolve a dor: algoritmo não acha bons trechos curtos, e cortar-e-juntar fica artificial. O short NASCE do deitado.

### 6a. Abertura → short (TRIVIAL, fazer primeiro)
- O cold-open (seção 4.4) já é short perfeito: gancho + auto-contido + serve de trailer pro longo.
- Exportar o cold-open separado como 9:16. Zero trabalho extra.

### 6b. Melhores trechos → shorts (junto do Tier 1)
- Os beats dramáticos marcados pro cutout/freeze (seção 3) SÃO os melhores pontos de short. Pipeline já terá as marcações — não precisa adivinhar.
- Pegar ~5-10 frases ao redor do beat (narração + legenda já prontas), reenquadrar 9:16.
- **Exceção à regra "short só de fonte vertical":** aqui a fonte é o NOSSO recap produzido, não o anime cru. Testar reframe vs blur-bordas vs crop no personagem (via cutout).
- **DECISÃO PENDENTE da dona:** automático (top 3-5 beats sozinho) OU curadoria (lista candidatos, ela aprova)?

---

## 7. Ordem de execução recomendada

1. **[bloqueante] Reiniciar daemon** pós-job atual → validar `÷3.8` no próximo render (dur_ratio deve subir).
2. **[base] Motor de graus + paralelismo CPU/GPU** (seção 2) — fundação de tudo.
3. **[Tier 1] Transições boas + cutout com marcação de beats** (seção 3) — maior ganho visual.
4. **[trivial paralelo] Cold-open → short 6a + loudnorm 4.2 + SFX** (seção 4-6, baixo custo alto impacto).
5. **[pós] 720p→upscale, CTA por imagem OmniRoute** (seção 4-5).
6. **[subproduto] Melhores-trechos → shorts 6b** (depende das marcações do passo 3).
7. **[último] Música Lyria opcional, Veo3 aberturas eventuais.**

---

## 8. Riscos e mitigação
- **RAM da 620 (11.7GB):** overlays em lotes; nunca filtergraph gigante; 1 só daemon (matar órfãos).
- **Daemon single-thread já resolvido** (ThreadingHTTPServer) — não reiniciar no meio de job.
- **Tokens de imagem/música:** CTAs por imagem cacheados por tema; música opcional.
- **Reframe de short pode ficar ruim:** ter fallback (blur nas bordas) e testar antes de automatizar.
- **Upscale na 620:** validar que Real-ESRGAN NÃO roda (é CUDA). Alternativa CPU: lanczos do ffmpeg ou upscale leve; upscale IA pesado provavelmente inviável — CONFIRMAR antes de prometer 4K.
