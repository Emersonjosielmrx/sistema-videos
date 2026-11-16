"""mascote_overlay.py — sobrepõe a MASCOTE (garota-propaganda) reagindo à narração.

TAREFA 14. Assets prontos (14 MOVs ProRes 4444 alpha real, 1080x1920, 1.8s) em
workspace/assets/mascote_mov/. A garota sobe de baixo, faz "bob" e solta um balão de reação.

Mecânica = mesma das transições elementais: overlay ffmpeg do MOV alpha sobre o vídeo FINAL,
no timestamp do clip que casou, áudio=copy. Flag MASCOTE_OVERLAY=1 (default OFF).
Regras: só reage à narração do NARRADOR; parcimônia (máx 2-3/vídeo); não cobre legenda/watermark
(a animação já sobe do canto inferior). Anti-repetição de pose consecutiva.
"""
import os
import re
import shutil
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
MOV_DIR = PROJECT_DIR / "workspace" / "assets" / "mascote_mov"

MAX_APARICOES = int(os.environ.get("MASCOTE_MAX", "5"))

# pose -> (arquivo MOV, keywords PT). Ordem = prioridade quando várias casam.
# Emoções fortes ANTES de wave/point (genéricos). wave só com saudação real de abertura
# ("história" foi removido — casava em narração descritiva e roubava o cry/love).
POSE_TABLE = [
    ("love",     "fx_mascot_love.mov",     ["apaixon", "coração", "coracao", "beij", "crush", "casal", "romântic", "romantic", " fofo", "que fofo"]),
    ("cry",      "fx_mascot_cry.mov",      ["chor", "lágrim", "lagrim", "triste", "sofr", "morre", "perdeu", "luto"]),
    ("shock",    "fx_mascot_shock.mov",    ["chocad", "não acredito", "nao acredito", "impossível", "impossivel", "de repente", "plot twist", "revelaç", "revelac"]),
    ("angry",    "fx_mascot_angry.mov",    ["raiva", "furioso", "irritad", "ódio", "odio", "bravo", "revolt", "injust"]),
    ("shy",      "fx_mascot_shy.mov",      ["vergonha", "envergonh", "corou", "tímid", "timid", "encabul", "constrang"]),
    ("cheer",    "fx_mascot_cheer.mov",    ["feliz", "consegui", "vitória", "vitoria", "ganhou", "comemor", "finalmente"]),
    ("popcorn",  "fx_mascot_popcorn.mov",  ["suspense", "aguarde", "expectativa", "vai acontecer", "tensão", "tensao", "clímax", "climax"]),
    ("laugh",    "fx_mascot_laugh.mov",    ["risada", "riu", "engraçad", "engracad", "hilári", "hilari", "cômic", "comic", "piada", "kkk"]),
    ("sleepy",   "fx_mascot_sleepy.mov",   ["cansad", "sono", "dormir", "tédio", "tedio", "entediad"]),
    ("think",    "fx_mascot_think.mov",    ["confus", "não entend", "nao entend", "será que", "sera que", "dúvida", "duvida", "misté", "miste", "enigm"]),
    ("wave",     "fx_mascot.mov",          ["oi pessoal", "olá pessoal", "ola pessoal", "bem-vindo", "bem vindo", "vamos começar", "vamos comecar", "fala galera", "e aí"]),
    ("point",    "fx_mascot_point.mov",    ["olha", "viu", "repare", "perceb", "presta atenção", "presta atencao"]),
]


def _ff():
    f = shutil.which("ffmpeg")
    if f:
        return f
    import glob as _g
    for pat in (str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/**/ffmpeg.exe"),
                "C:/Users/*/AppData/Local/Microsoft/WinGet/**/ffmpeg.exe"):
        h = _g.glob(pat, recursive=True)
        if h:
            return h[0]
    return "ffmpeg"


def _asset(mov):
    p = MOV_DIR / mov
    return str(p) if p.exists() else None


# Fallback: clima (mood) → pose, quando nenhuma keyword específica casa. Isso faz a
# mascote VARIAR as poses (antes quase sempre caía na mesma, pois as keywords são raras).
_MOOD_POSE = {
    "romantic_sexy": "love", "romantic": "love",
    "sad_emotional": "cry", "sad": "cry", "emotional": "cry",
    "tense_dramatic": "popcorn", "tense": "popcorn", "suspense": "popcorn",
    "funny_lighthearted": "laugh", "funny": "laugh", "comedic": "laugh",
    "epic_action": "cheer", "action": "cheer", "epic": "cheer",
    "calm_chill": "think", "neutral_chill": "think", "chill": "think",
}


def pick_pose(text, mood=None):
    """Retorna nome da pose (ou None) pela narração. Keyword específica tem prioridade;
    senão, cai pro mood (variedade). point por último (genérico)."""
    t = (text or "").lower()
    if not t.strip():
        return None
    for pose, _mov, kws in POSE_TABLE:
        for k in kws:
            if k in t:
                return pose
    # fallback por mood — amplia a variedade de poses
    if mood is None:
        try:
            import effects_engine as _fx
            mood = _fx.detect_mood_from_text(text)
        except Exception:
            mood = None
    if mood:
        return _MOOD_POSE.get(mood)
    return None


def pick_eventos(clip_texts, clip_personas, abs_starts, sensual=None):
    """Decide quando a mascote aparece. SÓ narrador, anti-repetição, máx MAX_APARICOES.
    Pula painéis +18 (sensual) — não sobrepor mascote em cena que vai ser censurada.
    Retorna lista de {t, pose, file, dur}."""
    eventos = []
    last_pose = None
    _sens = set(sensual or [])
    pose_mov = {p: m for p, m, _ in POSE_TABLE}
    n = min(len(clip_texts), len(abs_starts))
    for i in range(n):
        if len(eventos) >= MAX_APARICOES:
            break
        if i in _sens:
            continue  # painel +18 → sem mascote
        persona = (clip_personas[i] if i < len(clip_personas) else "") or ""
        pclean = re.sub(r"\s*[\(\[\{].*?[\)\]\}]", "", persona).strip().lower()
        if pclean not in ("narrador", "narradora"):
            continue
        pose = pick_pose(clip_texts[i])
        if pose is None or pose == last_pose:
            continue
        mov = _asset(pose_mov.get(pose, ""))
        if not mov:
            continue
        dur = _probe_dur(mov)
        eventos.append({"t": abs_starts[i] + 0.1, "pose": pose, "file": mov, "dur": dur})
        last_pose = pose
    return eventos


def _probe_dur(f):
    try:
        fp = shutil.which("ffprobe") or _ff().replace("ffmpeg", "ffprobe")
        r = subprocess.run([fp, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(f)], capture_output=True, text=True, timeout=15)
        return float(r.stdout.strip())
    except Exception:
        return 1.8


def overlay_mascote(base_mp4, out_mp4, eventos):
    """Sobrepõe os MOVs alpha da mascote no vídeo. Áudio=copy. Retorna True/False."""
    base_mp4, out_mp4 = Path(base_mp4), Path(out_mp4)
    if not eventos:
        return False
    try:
        fp = shutil.which("ffprobe") or _ff().replace("ffmpeg", "ffprobe")
        r = subprocess.run([fp, "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(base_mp4)],
                           capture_output=True, text=True, timeout=15)
        bw, bh = (int(x) for x in r.stdout.strip().split("x"))
    except Exception:
        return False
    inputs = ["-i", str(base_mp4)]
    for e in eventos:
        inputs += ["-i", str(e["file"])]
    fc = []
    last = "[0:v]"
    for idx, e in enumerate(eventos, start=1):
        t0 = e["t"]
        t1 = t0 + e["dur"]
        fc.append(f"[{idx}:v]scale={bw}:{bh}:flags=bicubic,setpts=PTS-STARTPTS+{t0:.3f}/TB[mv{idx}]")
        out = f"[m{idx}]"
        fc.append(f"{last}[mv{idx}]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})'{out}")
        last = out
    cmd = [_ff(), "-y", *inputs, "-filter_complex", ";".join(fc),
           "-map", last, "-map", "0:a?",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "veryfast",
           "-c:a", "copy", str(out_mp4)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        return r.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 0
    except Exception:
        return False
