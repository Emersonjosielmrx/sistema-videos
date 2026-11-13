# 📌 PENDÊNCIAS PÓS-IMPLEMENTAÇÃO — validar/ajustar quando a máquina liberar

> Escrito 2026-06-30 ~22:15 (agente da -fix). Tudo abaixo está CODADO e passou em SELF-TEST
> isolado, mas NÃO foi validado em RENDER COMPLETO porque a máquina está ocupada pelo render
> contínuo da versão -producao (não dá pra rodar 2 renders pesados juntos — competem CPU/ffmpeg
> e workspace/videos é junction compartilhada). Editar código na -fix é livre; só o RENDER espera.
> Quando sobrar janela ociosa (tasklist sem ffmpeg/python de pipeline), rodar os testes abaixo.

## COMO VALIDAR (render de teste, reusa cache, zero Gemini)
Checar máquina ociosa primeiro:
`powershell.exe -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'ffmpeg|python' } | Select ProcessId,Name"`
Comando base (cap pequeno, cache, ~poucos min):
```bash
cd /d/hipercool-inferior-fix && rm -f workspace/.queue_lock
export PYTHONUTF8=1 ENSEMBLE_NARRATION=0 TTS_ENGINE=edge GEMINI_TTS_PROXY_ENABLED=0
# ligar as flags do que quer testar, ex:
ELEMENTAL_TRANS=1 MASCOTE_OVERLAY=1 CONTENT_ADAPT=1 PARALLAX=1 \
  /d/hipercool-videos/venv/Scripts/python.exe bin/hiper-pipeline.py \
  --panels-dir workspace/panels/the-meek-cat-cap05 --titulo "Teste Features" \
  --max-panels 14 --subtitles --karaoke --skip-notify --output-suffix _TESTEFEATURES > teste.log 2>&1
```
ffprobe sempre (áudio não pode ser >5s menor que vídeo).

## 1. FRENTE 1-B — 3 categorias de efeito (CAT1/CAT2/CAT3)
- Codado: EFFECT_CAT (21/20/23) + posicionamento (CAT1 no corte, CAT2/3 durante painel) em elemental_transitions.py.
- VALIDAR: render com ELEMENTAL_TRANS=1 e conferir VISUALMENTE que overlay atmosférico (snow/rain/petals) aparece SOBRE o painel (não só no corte) e que reativos (hearts) caem na fala certa.

## 2. MASCOTE (TAREFA 14)
- Codado: bin/mascote_overlay.py + integração 3a-ter atrás de MASCOTE_OVERLAY=1. Self-test pick_pose 6/6.
- VALIDAR: render com MASCOTE_OVERLAY=1; conferir que a garota sobe no canto, reage à narração (love/cry/shock), máx 3x, NÃO cobre legenda/watermark. Ajustar posição/escala se cobrir.

## 3. CENSURA modo cor (nível 2) + integração no pipeline
- Codado: CENSURA_MODO=tarja|cor (nivel1/2/3 alias) em censura_visual.py. Detecção Sightengine no pipeline.
- PENDENTE REAL: a APLICAÇÃO da censura visual (banda/cor na imagem do painel) ainda NÃO está
  plugada no fluxo da variante censurada — hoje o pipeline ainda usa a censura antiga (blur tela
  + timing fix). Integrar: gerar <painel>_censored.jpg via censura_visual e a variante censurada
  montar clip a partir dela. Ponto: antes de build_clip (~1170) lista paralela clip_censored_img[i].
- NÍVEL 3: a usuária vai passar a referência (placeholder hoje cai no nível 2). Ver project_censura_por_cor_ideia (memória).

## 4. CONTENT_ADAPT (T5)
- Codado: content_analyzer.py + anexa eq adaptativo no build_clip atrás de CONTENT_ADAPT=1.
- LIMITAÇÃO: YDIF (contraste) dá 0 em imagem estática (signalstats) — só o brilho corrige. Avaliar
  se vale medir contraste por outro método (std do histograma) num próximo passo.
- VALIDAR: render com CONTENT_ADAPT=1 num cap com painel escuro; conferir que clareou sem estourar.

## 5. CLASSIFICADOR texto_plano + gate parallax
- Codado: panel_classifier.py + gate no parallax (on, hiper-pipeline ~1191). Calibragem agressiva.
- PENDENTE lado OFF: o prefetch de depth (projeto D:\hipercool-motionframes) deve usar o MESMO
  panel_classifier pra não gerar depth de texto_plano. Copiar/importar bin/panel_classifier.py lá.
- VALIDAR: render com PARALLAX=1 e ver no log "↪ painel N é texto/plano → pula parallax".

## 6. PASSO C — posicionamento espacial CAT3a (pointer/zoomdetail/objectglow)
- Codado: apply() do elemental aceita pick["pos"]=(x,y) fração 0-1 → desloca overlay (Opção B, sem re-render).
- FALTA A FONTE DA COORDENADA: adicionar campo `foco:{x,y}` ao prompt de descrição do Gemini Vision
  e guardar no narration_cache; pick_transitions passar pos pros 3 críticos. Mexe na visão → só
  validável com geração nova (gasta Gemini). Keywords dos 3 já estão [] (não disparam errado). 
- Alternativa sem LLM: saliency/rosto via OpenCV (Opção C do doc).

## 7. PARALLAX — testar/calibrar/ligar (FRENTE 3)
- Já implementado por outro agente; falta TESTAR no pipeline completo + calibrar speed/blur + ligar nos finais.
- Ver PLANO_AGENTE_PARALLAX_MOVIMENTO_REAL.md. Gate já pronto (PARALLAX=1, sem FORCE = só versão final).

## 8. DRIFT de sync (voz Eleven) — espelhar da -producao
- O agente da -producao está corrigindo o drift (WAV Eleven container≠samples). Quando achar o fix,
  ESPELHAR aqui na -fix. Ver PROMPT_AGENTE_DRIFT_SYNC.md.

## md5 do código nesta sessão (-fix, 2026-06-30 ~22h)
- hiper-pipeline.py = a8469a85 (voz eleven + censura detect + gate parallax + mascote)
- elemental_transitions.py = a8c712b0 (3 categorias + pos + mascot entry)
- censura_visual.py = 550c3d53 (3 níveis + resolver ffmpeg)
- mascote_overlay.py = cbbe60aa (NOVO)
- content_analyzer.py / panel_classifier.py (NOVOS)
- effects_engine.py = ef5055c1 (CONTENT_ADAPT)
