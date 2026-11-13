"""Pool de trilhas originais geradas localmente (MusicGen-small via recapd-ambientes), sem risco de Content ID.

Gera N faixas por mood em assets/music_generated/<mood>/ e registra em assets/music_generated/index.json.
Usa o venv e o script ja existentes em D:/recapd-ambientes/producao (transformers + torch CPU). ~2 min por faixa de 30 s.
"""
import json
import subprocess
import time
from pathlib import Path
from .common import log

MOODS = ["tense_dramatic", "sad_emotional", "romantic_sexy", "funny_lighthearted", "neutral_chill", "calm_chill"]


def generated_dir(cfg):
    return Path(cfg["paths"]["assets"]) / "music_generated"


def generate_pool(cfg, per_mood=3, duration=30, moods=None):
    py = cfg["paths"].get("musicgen_python", "D:/recapd-ambientes/producao/venv/Scripts/python.exe")
    script = cfg["paths"].get("musicgen_script", "D:/recapd-ambientes/producao/bin/musicgen_local.py")
    if not Path(py).exists() or not Path(script).exists():
        log("musicgen: script/venv do recapd nao encontrado")
        return 0
    root = generated_dir(cfg)
    idx_path = root / "index.json"
    idx = json.load(open(idx_path, encoding="utf-8")) if idx_path.exists() else []
    made = 0
    for mood in (moods or MOODS):
        d = root / mood
        d.mkdir(parents=True, exist_ok=True)
        have = len(list(d.glob("*.wav")))
        for i in range(have, per_mood):
            out = d / f"{mood}_{i+1:02d}.wav"
            t = time.time()
            res = subprocess.run([py, script, "--mood", mood, "--duration", str(duration), "--out", str(out)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", cwd=str(Path(script).parent.parent), timeout=1800)
            if res.returncode == 0 and out.exists():
                idx.append({"file": str(out), "mood": mood, "duration": duration, "source_id": "musicgen", "title": out.stem})
                json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                made += 1
                log(f"musicgen: {out.name} em {time.time() - t:.0f}s")
            else:
                log(f"musicgen: falhou {mood} #{i+1}: {(res.stderr or res.stdout)[-300:]}")
                break
    log(f"musicgen: {made} faixa(s) nova(s); pool com {len(idx)}")
    return made


def pool_candidates(cfg, mood):
    """Faixas geradas para o mood (ou vazio)."""
    root = generated_dir(cfg)
    idx_path = root / "index.json"
    if not idx_path.exists():
        return []
    try:
        idx = json.load(open(idx_path, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    return [Path(e["file"]) for e in idx if e.get("mood") == mood and Path(e["file"]).exists()]
