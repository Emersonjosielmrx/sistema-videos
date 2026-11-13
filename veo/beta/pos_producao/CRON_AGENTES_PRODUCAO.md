# MODO PRODUCAO 2026-07-27 - Agentes Cron (10h)

## Objetivo
Acompanhar a pipeline de pos-producao rodando continuamente por 10h.
Cada cron tem funcao clara, intervalos definidos, e loga tudo em JSONL
pra auditoria pelo agente da manha.

## Diretorios chave
- Source: D:/veo/beta/videos/cron_shorts/ (entrada - Veo solta MP4 aqui)
- Pos:   D:/veo/beta/videos_pos/cron_shorts/ (saida - pipeline completa)
- Logs:  D:/veo/beta/pos_producao/cron_logs/<agente>.jsonl

## Agentes cron (total: 6)

### 1. cron_video_watcher (a cada 5 min)
Funcao: detecta MP4 novo em cron_shorts/ que ainda nao foi processado
Saida: lista de (stem, path) novos em logs/cron_video_watcher.jsonl
Comando: scan D:/veo/beta/videos/cron_shorts/ -name "*.mp4" -mmin -X

### 2. cron_pipeline_runner (a cada 10 min, apos watcher)
Funcao: pega lista do watcher e roda pipeline em ate 3 videos/vez
Saida: log de "processado N video(s)" em cron_pipeline_runner.jsonl
Comando: python -m pos_producao.runner (modo incremental)

### 3. cron_health_check (a cada 15 min)
Funcao: valida que ffmpeg/edge-tts/onnx/parallax_engine estao saudaveis
Saida: status JSON em cron_health_check.jsonl
Comando: ffmpeg -version; python -c "import edge_tts"; python -c "import onnxruntime"

### 4. cron_disk_monitor (a cada 30 min)
Funcao: checa espaco em D: e tamanho de videos_pos/ (alerta se >80% cheio)
Saida: cron_disk_monitor.jsonl

### 5. cron_quarantine (a cada 30 min, intercalado com health)
Funcao: roda deteccao de cena ruim (histograma+frame diff) nos videos
recem-processados. Se 90%+ estatico, marca como _QUARANTINE.mp4 e
move pra subpasta _quarentine/.
Saida: cron_quarantine.jsonl com decisao por video

### 6. cron_alert (a cada 60 min)
Funcao: agrega logs das ultimas 1h, se tem erro critico ou mais de 5
avisos, cria D:/veo/beta/ALERTA.txt pro agente da manha ver primeiro.
Saida: cron_alert.jsonl + ALERTA.txt (se houver)

## Por que 6 agentes (nao 1 so)
- Separacao de responsabilidades: cada um tem 1 funcao clara
- Logs independentes: falha num nao impede os outros
- Intervalos diferentes: video_watcher precisa ser rapido (5min),
  disk_monitor pode esperar (30min)

## Documentacao pra auditoria
Cada .jsonl tem 1 linha por execucao no formato:
  {"ts": "2026-07-27T22:35:00", "agente": "nome", "acao": "X",
   "input": "...", "output": "...", "status": "ok|warn|erro",
   "detalhes": {...}}

Agente da manha: ler primeiro o ALERTA.txt (se existir), depois
cron_alert.jsonl das ultimas 10h, depois os outros.

## Estado atual da pipeline (2026-07-27 22:35)
- Plugin ffmpeg_loudnorm: ok
- Plugin crop_9_16: ok
- Plugin legendas: PULANDO (ok=False - investigar)
- Plugin propaganda_inteligente: ok com xfade + TTS expandido
- Plugin branding_watermark: ok com xfade + fade-to-black
- Falta implementar:
  * cron_video_watcher
  * cron_pipeline_runner (wrapper)
  * cron_health_check
  * cron_disk_monitor
  * cron_quarantine
  * cron_alert

## Bugs ja corrigidos (v6 -> v7)
- BUG TTS curto: fala expandida com gancho (~5-6s)
- BUG xfade main->propaganda: 0.3s
- BUG xfade propaganda->outro: 0.3s
- BUG fade-to-black fim do outro: 0.3s (ja estava no outro, mantido)