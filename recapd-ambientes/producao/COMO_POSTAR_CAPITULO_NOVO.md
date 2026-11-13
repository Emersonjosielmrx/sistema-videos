# ▶️ COMO POSTAR UM CAPÍTULO NOVO (handoff curto pro agente que gera os caps)

> Você acabou de gerar um capítulo (ex: The Meek Cat cap 6)? Siga estes 4 passos.
> Detalhes/limites completos: **`POSTAGEM_YOUTUBE_PLAYBOOK.md`** (mesma pasta).
> ⚠️ REGRA #1: **só posta a versão CENSURADA** (`*_CENSURADO_ULTIMO.mp4`). Postar
> não-censurada = risco de BAN. Os shorts TÊM que ser cortados do vídeo censurado.

## Setup (cole antes)
```bash
cd /d/hipercool-producao          # scripts iguais existem em /d/hipercool-inferior-fix tb
export PYTHONUTF8=1
PY="D:/hipercool-videos/venv/Scripts/python.exe"
```

## PASSO 1 — ache o vídeo CENSURADO do capítulo
Ele sai em `D:\hipercool-materiais\videos\` (o workspace/videos é junction pra lá).
Procure o mais novo com `CENSURADO` no nome, ex:
`hipercool_the-meek-cat-cap-tulo-6_..._CENSURADO_ULTIMO.mp4`
```bash
ls -t "D:/hipercool-materiais/videos/"*cap*6*CENSURADO*ULTIMO.mp4 | head -1
```
Confira que abre e áudio≈vídeo:
```bash
ffprobe -v quiet -show_entries format=duration -of csv=p=0 "ARQUIVO.mp4"
```

## PASSO 2 — corte os shorts (do CENSURADO)
```bash
"$PY" bin/split-shorts.py --video "ARQUIVO_CENSURADO.mp4" --obra "The Meek Cat" --capitulo 6
```
Saída em `workspace/shorts/the-meek-cat-cap6/`.

## PASSO 3 — adicione o cap ao config e regenere a fila do manga
Edite `_LEIA_POSTAR_VIDEOS/config_fila.json` e ACRESCENTE um bloco em `"caps"`:
```json
{ "cap": 6,
  "completo": "D:/hipercool-materiais/videos/ARQUIVO_CENSURADO.mp4",
  "shorts_dir": "D:/hipercool-producao/workspace/shorts/the-meek-cat-cap6" }
```
(Se quiser postar SÓ o cap 6, deixe apenas o bloco dele em `"caps"`.)
Depois:
```bash
"$PY" bin/montar-fila.py --config "_LEIA_POSTAR_VIDEOS/config_fila.json"
```
Isso distribui nos 2 canais de manga, respeitando cota, e agenda horários.
Confira o plano impresso.

## PASSO 4 — postar
Duas opções:
- **Automático (recomendado):** não faça nada. O **Postador do Windows**
  (`PostadorDeVideos`, roda 06:40 diário) sobe tudo que estiver na fila, em catch-up.
- **Agora, à mão:**
  ```bash
  "$PY" bin/postar-fila.py --plano "_LEIA_POSTAR_VIDEOS/fila_meek_caps234.json" --dry-run   # confere
  "$PY" bin/postar-fila.py --plano "_LEIA_POSTAR_VIDEOS/fila_meek_caps234.json"             # posta
  ```
  Privado + `publishAt` agendado. Idempotente (roda de novo sem duplicar).

## Atalho (corta + posta 1 cap de uma vez)
```bash
"$PY" bin/batch-post-shorts.py --video "ARQUIVO_CENSURADO.mp4" \
  --obra "The Meek Cat" --capitulo 6 --canal "inovare recap manga" --hora-inicio 14:00
# use --dry-run primeiro
```

## Limites (resumo — detalhes no PLAYBOOK)
- Canal de conta: ~9-21 uploads/dia (`uploadLimitExceeded` quando estoura).
- Projeto de API compartilhado (canais de IA): teto de "Video Uploads per day"
  (429) que se recupera ao longo das horas. Os 2 canais de manga têm projeto
  próprio → não sofrem disso.
- Se estourar, o que faltou fica pendente e o Postador sobe no dia seguinte sozinho.
- publishAt é UTC (BRT = UTC−3).
