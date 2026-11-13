"""compile_guards.py — guardas de robustez pro compilado paisagem (T12 + T13-capítulos).

Porte das ideias do fluxo n8n "4" (DiskMonitor / QuarentenaManager / GapDetector / capitulos),
adaptado pro Windows (shutil.disk_usage, não comandos Linux). Funções puras, atrás de flags no
landscape-compiler. NÃO portam telemetria/webhook/multi-idioma do n8n.
"""
import os
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


# ─── T12.1 disk_guard: CRF adaptativo por espaço livre ───────────────────────
def disk_guard(base_crf=20, path="D:/"):
    """Retorna (crf_ajustado, msg). Sobe o CRF se o disco está cheio (comprime mais p/ não
    estourar). Limiares do n8n: 85%→+2, 90%→+4, 95%→aborta(None)."""
    try:
        total, used, free = shutil.disk_usage(path)
        pct = used / total * 100
    except Exception:
        return base_crf, "disk_guard: não medível, mantém CRF"
    if pct >= 95:
        return None, f"disk_guard: disco {pct:.0f}% — ABORTAR (risco de corromper)"
    if pct >= 90:
        return base_crf + 4, f"disk_guard: disco {pct:.0f}% — CRF +4 (comprime mais)"
    if pct >= 85:
        return base_crf + 2, f"disk_guard: disco {pct:.0f}% — CRF +2"
    return base_crf, f"disk_guard: disco {pct:.0f}% ok"


# ─── T12.2 quarentena: isola vídeo que falhou ────────────────────────────────
def quarantine(video_path, motivo=""):
    """Move um vídeo defeituoso pra workspace/videos/quarentena/ e retorna o novo caminho
    (ou None se falhar). O compilado segue sem ele."""
    try:
        src = Path(video_path)
        if not src.exists():
            return None
        qdir = PROJECT_DIR / "workspace" / "videos" / "quarentena"
        qdir.mkdir(parents=True, exist_ok=True)
        dst = qdir / src.name
        shutil.move(str(src), str(dst))
        try:
            (qdir / (src.name + ".motivo.txt")).write_text(motivo or "falha", encoding="utf-8")
        except Exception:
            pass
        return str(dst)
    except Exception:
        return None


# ─── T12.3 detect_gaps: páginas/caps faltando na sequência ───────────────────
def detect_gaps(caps):
    """Recebe lista de números de cap presentes; retorna lista dos FALTANTES no range.
    Ex: [1,2,4,5] → [3]. Pra alertar antes de compilar."""
    nums = sorted(int(c) for c in caps if str(c).isdigit())
    if len(nums) < 2:
        return []
    return [n for n in range(nums[0], nums[-1] + 1) if n not in nums]


# ─── T13.2 capítulos YouTube: arquivo de timestamps ──────────────────────────
def gerar_capitulos(segmentos, out_txt=None, intervalo=10, fmt="Páginas {inicio}-{fim}"):
    """segmentos: lista de (cap_num, duracao_seg). Gera texto de capítulos YouTube agrupando
    a cada `intervalo` caps. Retorna o texto; grava em out_txt se dado.
    Ex: '00:00 Páginas 1-10'."""
    linhas = []
    t = 0.0
    grupo_ini = None
    grupo_dur = 0.0
    n_no_grupo = 0
    last_cap = None

    def _hms(s):
        s = int(s)
        h, m, sec = s // 3600, (s % 3600) // 60, s % 60
        return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

    grupo_start_t = 0.0
    for cap, dur in segmentos:
        if grupo_ini is None:
            grupo_ini = cap
            grupo_start_t = t
            n_no_grupo = 0
        n_no_grupo += 1
        last_cap = cap
        t += float(dur or 0)
        if n_no_grupo >= intervalo:
            linhas.append(f"{_hms(grupo_start_t)} {fmt.format(inicio=grupo_ini, fim=last_cap)}")
            grupo_ini = None
    if grupo_ini is not None:
        linhas.append(f"{_hms(grupo_start_t)} {fmt.format(inicio=grupo_ini, fim=last_cap)}")
    txt = "\n".join(linhas)
    if out_txt:
        try:
            Path(out_txt).write_text(txt, encoding="utf-8")
        except Exception:
            pass
    return txt


# ─── T13.1 CTAs: seleção por peso + anti-repetição (lê arquivo editável) ──────
_CTA_FILE = PROJECT_DIR / "workspace" / "assets" / "cta_frases.json"
_cta_last = None


def pick_cta():
    """Escolhe uma frase de CTA (categoria por peso, anti-repetição da última frase).
    Lê workspace/assets/cta_frases.json (editável pela usuária). None se indisponível."""
    global _cta_last
    import json as _j
    import random as _r
    try:
        cats = _j.loads(_CTA_FILE.read_text(encoding="utf-8")).get("categorias", {})
    except Exception:
        return None
    nomes = [k for k in cats if cats[k].get("frases")]
    if not nomes:
        return None
    pesos = [cats[k].get("peso", 1) for k in nomes]
    cat = _r.choices(nomes, weights=pesos, k=1)[0]
    frases = [f for f in cats[cat]["frases"] if f != _cta_last] or cats[cat]["frases"]
    frase = _r.choice(frases)
    _cta_last = frase
    return {"categoria": cat, "frase": frase}

