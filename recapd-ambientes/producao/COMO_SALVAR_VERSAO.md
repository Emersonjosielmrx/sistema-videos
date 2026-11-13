# Como salvar versão estável no GitHub

## Quando salvar
Sempre que terminar uma sessão de trabalho importante (fixes, features novas, mudanças de pipeline) e tudo estiver funcionando.

## Passos

### 1. Verificar o que mudou
```bash
cd D:/recapd-e-animes
git status --short
```

### 2. Commitar com mensagem clara
```bash
git add bin/anime_auto.py bin/anime_discover.py bin/anime_fetch.py
git add bin/edge_tts_engine.py bin/_whisper_sub.py bin/anime-pipeline.py
git add logs/night-shift.md
git commit -m "feat(recapd): descrição do que mudou"
```

### 3. Push pro GitHub
```bash
git push -u origin master
```

## Tag de versão (opcional mas recomendado)
```bash
git tag -a v1.x -m "versão estável - data"
git push origin v1.x
```

## Arquivos importantes pra sempre commitar
- `bin/anime_auto.py` — orchestration
- `bin/anime_discover.py` — busca de candidatos
- `bin/anime_fetch.py` — download + transcrição
- `bin/anime-pipeline.py` — render
- `bin/edge_tts_engine.py` — TTS
- `bin/_whisper_sub.py` — wrapper whisper

## NÃO commitar (arquivos grandes/temporários)
- `_feitos*.txt` — blocklists
- `workspace/anime/` — videos outputs
- `fabrica-viral/` — assets pesados
- `logs/*.json` — métricas
- `bin/*_backup.py` — backups velhos
