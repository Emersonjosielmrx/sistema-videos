"""Validacao automatica do Short final: duracao, loudness, frames pretos e integridade. Marca pronto=false no postar.json se falhar."""
import json
import re
from pathlib import Path
from .common import run, ffprobe_json, log


def validate_output(cfg, mp4, expected_duration=None, lufs_target=-14.0):
    report = {"ok": True, "problems": []}
    try:
        info = ffprobe_json(cfg, mp4)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "problems": [f"ffprobe falhou: {e}"]}
    dur = float(info["format"].get("duration", 0))
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    report["duration"] = round(dur, 2)
    if not v or not a:
        report["problems"].append("faltando video ou audio")
    if v and (int(v.get("width", 0)), int(v.get("height", 0))) != (cfg["output"]["width"], cfg["output"]["height"]):
        report["problems"].append(f"resolucao {v.get('width')}x{v.get('height')}")
    if expected_duration and abs(dur - expected_duration) > 1.0:
        report["problems"].append(f"duracao {dur:.1f}s (esperado {expected_duration:.1f}s)")
    if dur < 5:
        report["problems"].append("video curto demais")
    # loudness e frames pretos numa passada so
    res = run([cfg["paths"]["ffmpeg"], "-hide_banner", "-i", str(mp4), "-vf", "blackdetect=d=0.6:pix_th=0.10", "-af", "ebur128",
               "-f", "null", "-"], check=False)
    # o ebur128 imprime "I:" a cada frame; o valor integrado final e o ultimo (bloco "Integrated loudness")
    ms = re.findall(r"I:\s+(-?[\d.]+) LUFS", res.stderr)
    if ms:
        lufs = float(ms[-1])
        report["lufs"] = lufs
        if abs(lufs - lufs_target) > 2.0:
            report["problems"].append(f"loudness {lufs} LUFS")
    blacks = re.findall(r"black_start:(\S+) black_end:(\S+)", res.stderr)
    if blacks:
        report["problems"].append(f"{len(blacks)} trecho(s) preto(s)")
    report["ok"] = not report["problems"]
    log(f"validacao: {'OK' if report['ok'] else 'PROBLEMAS ' + '; '.join(report['problems'])}")
    return report


def mark_postar(postar_path, ok, problems):
    try:
        d = json.load(open(postar_path, encoding="utf-8"))
        d["pronto"] = bool(ok)
        if problems:
            d["validacao"] = problems
        json.dump(d, open(postar_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as e:  # noqa: BLE001
        log(f"validacao: nao atualizei {postar_path}: {e}")


def cleanup_work(part_dir):
    """Apaga intermediarios pesados apos render OK."""
    n = 0
    for name in ("mixed.wav", "base.mp4"):
        p = Path(part_dir) / name
        if p.exists():
            p.unlink()
            n += 1
    raw = Path(part_dir).parent / "raw.wav"
    if raw.exists():
        raw.unlink()
        n += 1
    return n
