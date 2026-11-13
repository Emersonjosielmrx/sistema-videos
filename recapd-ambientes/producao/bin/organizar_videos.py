# -*- coding: utf-8 -*-
"""organizar_videos.py — move vídeos SOLTOS pra estrutura videos/<obra>/capNN/{engine}/normal + censored.

Regra: pra cada (cap, engine), mantém a versão MAIS RECENTE (timestamp no nome).
Normal (limpo) → <obra>/capNN/<engine>/normal/vN.mp4
Censurada       → <obra>/capNN/censored/vN.mp4  (nível do cap)
Versões antigas do mesmo cap+engine → <obra>/capNN/<engine>/_anteriores/

Uso:
  python bin/organizar_videos.py            # DRY-RUN (só mostra o plano)
  python bin/organizar_videos.py --apply    # move de verdade
Idempotente. Fallback: erro num arquivo não interrompe os outros.
"""
import re
import sys
import json
import shutil
from pathlib import Path
from collections import defaultdict

PROJECT = Path(__file__).resolve().parent.parent
VIDEOS = PROJECT / "workspace" / "videos"
APPLY = "--apply" in sys.argv

# título-slug → obra-slug (pasta de painéis). Estende conforme novas obras.
# gap-hibrido = testes de efeito antigos (sem cap) → ficam ignorados de propósito.
TITULO2OBRA = {
    "o-guerreiro-regressou": "regressed-warriors",
    "the-warrior-who-returned": "regressed-warriors",  # mesmo manhwa, título EN antigo
    "the-meek-cat": "the-meek-cat",
}

def obra_de(nome):
    for tslug, obra in TITULO2OBRA.items():
        if tslug in nome:
            return obra
    return None

def engine_de(mp4: Path):
    meta = mp4.with_suffix(".meta.json")
    if meta.exists():
        try:
            e = json.loads(meta.read_text(encoding="utf-8")).get("tts_engine", "")
            if e in ("edge", "gemini", "eleven"):
                return e
        except Exception:
            pass
    n = mp4.name.lower()
    if "gemini" in n or "cap1gemini" in n:
        return "gemini"
    return "edge"

# agrupa por (obra, cap, censurada?) → escolhe mais recente por timestamp no nome
pat = re.compile(r"cap(?:itulo|-tulo)?-(\d+)_(\d{8}_\d{4})")
grupos = defaultdict(list)   # (obra,cap,engine,is_cens) -> [(ts, path)]
ignorados = []
for mp4 in sorted(VIDEOS.glob("*_ULTIMO*.mp4")):
    if mp4.parent != VIDEOS:  # já está em subpasta
        continue
    # _hd é a versão HD (1080p) do MESMO vídeo — não é um vídeo separado.
    # Fica como companheiro do arquivo base (movido junto). Pula aqui.
    if mp4.stem.endswith("_hd"):
        continue
    obra = obra_de(mp4.name)
    m = pat.search(mp4.name)
    if not obra or not m:
        ignorados.append(mp4.name)
        continue
    cap = int(m.group(1)); ts = m.group(2)
    is_cens = "_CENSURADO" in mp4.name
    eng = engine_de(mp4)
    grupos[(obra, cap, eng, is_cens)].append((ts, mp4))

if not grupos:
    print("Nenhum vídeo solto do tipo conhecido pra organizar.")
    sys.exit(0)

def next_v(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    ex = [int(mm.group(1)) for p in d.glob("v*.mp4") if (mm := re.match(r"v(\d+)\.mp4$", p.name))]
    return f"v{(max(ex)+1) if ex else 1}.mp4"

print(f"{'=== PLANO (DRY-RUN) ===' if not APPLY else '=== APLICANDO ==='}")
moves = []  # (src, dest, tipo)
for (obra, cap, eng, is_cens), items in sorted(grupos.items()):
    items.sort()  # timestamp asc → último é o mais recente
    ts_recent, mp4_recent = items[-1]
    cap_key = f"cap{cap:02d}"
    if is_cens:
        dest_dir = VIDEOS / obra / cap_key / "censored"
    else:
        dest_dir = VIDEOS / obra / cap_key / eng / "normal"
    moves.append((mp4_recent, dest_dir, f"{obra}/{cap_key}/{'censored' if is_cens else eng+'/normal'} [{'CENS' if is_cens else eng}]"))
    # anteriores
    for ts_old, mp4_old in items[:-1]:
        ant_dir = VIDEOS / obra / cap_key / (eng if not is_cens else "censored") / "_anteriores"
        moves.append((mp4_old, ant_dir, f"  (anterior) → _anteriores/"))

for src, dest_dir, label in moves:
    print(f"  {src.name}\n      → {label}")

print(f"\nTotal: {len(moves)} arquivos. Ignorados (obra/cap não reconhecido): {len(ignorados)}")
for ig in ignorados[:8]:
    print(f"  ignorado: {ig}")

if not APPLY:
    print("\n(DRY-RUN — nada foi movido. Rode com --apply pra executar.)")
    sys.exit(0)

# aplica
done = 0
for src, dest_dir, label in moves:
    try:
        if not src.exists():
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        vname = next_v(dest_dir) if "_anteriores" not in str(dest_dir) else src.name
        dest = dest_dir / vname
        shutil.move(str(src), str(dest))
        meta = src.with_suffix(".meta.json")
        if meta.exists():
            shutil.move(str(meta), str(dest.with_suffix(".meta.json")))
        # _hd companheiro
        hd = src.with_name(src.stem + "_hd.mp4")
        if hd.exists():
            shutil.move(str(hd), str(dest_dir / (dest.stem + "_hd.mp4")))
        done += 1
    except Exception as e:
        print(f"  ⚠ erro movendo {src.name}: {e}")
print(f"\n✓ {done} arquivos movidos.")
