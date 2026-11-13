#!/usr/bin/env python3
"""painel-progresso.py — painel de acompanhamento AO VIVO da geração de capítulos.

READ-ONLY: só lê processos, logs e estado. NUNCA gera vídeo nem toca no pipeline.
Pode rodar junto com um render sem competir (não usa ffmpeg pesado).

Detecta o render pelo PROCESSO (não por log fresco) — assim pega render em qualquer
cópia (-fix ou -producao) e com log em qualquer lugar (raiz ou logs/).

Mostra, atualizando a cada poucos segundos:
  - Render ativo: QUAL CÓPIA, qual capítulo, etapa atual, %, ETA, log.
  - Detalhe fino: último painel/clip, voz, transição, SFX, trilha.
  - Fila (night_shift_state.json).
  - Worker/parallax (depths em cache) + processos.
  - Últimos erros (logs/errors.jsonl).

Uso:
  PYTHONUTF8=1 D:/recapd-ambientes/producao/venv/Scripts/python.exe bin/painel-progresso.py
  --once = imprime uma vez e sai.
"""
import os
import re
import sys
import glob
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_DIR / "logs"
STATE_FILE = PROJECT_DIR / "workspace" / "night_shift_state.json"
DEPTH_CACHE = Path("D:/hipercool-motionframes/cache/depth")
REFRESH_S = 4

# Etapas do pipeline em ordem, com peso aproximado no tempo total (p/ % global).
ETAPAS = [
    ("scrape",   "Baixando/cortando painéis",        0.02),
    ("vision",   "Descrevendo painéis (Gemini Vision)", 0.10),
    ("narracao", "Gerando narração (LLM)",            0.04),
    ("tts",      "Gerando vozes (TTS)",               0.34),
    ("render",   "Renderizando clips (efeitos)",      0.30),
    ("trilha",   "Trilha dinâmica",                   0.03),
    ("legenda",  "Queimando legendas + watermark",    0.06),
    ("upscale",  "Upscalando 720p→1080p",             0.05),
    ("censura",  "Aplicando censura +18",             0.05),
    ("pos",      "Finalizando / shorts",              0.01),
]
ETAPA_NOME = {k: n for k, n, _ in ETAPAS}

RE_VISION   = re.compile(r"vis[ãa]o\s+(\d+)/(\d+)")
RE_DESCR_OK = re.compile(r"✓ Descreveu (\d+) pain")
RE_NARR     = re.compile(r"Chamando Gemini pra|Narração:|Coerência")
RE_TTS      = re.compile(r"wrote audio_(\d+)\.wav")
RE_CLIP     = re.compile(r"Clip\s+(\d+)/(\d+)")
RE_CLIP_DET = re.compile(r"Clip\s+(\d+)/(\d+).*?painel=(\S+).*?voz=(\S+).*?trans=(\S+)(?:.*?sfx=(\S+))?")
RE_PAINEIS  = re.compile(r"\((\d+)\s+pain[ée]is\)")
RE_PRONTO   = re.compile(r"V[íi]deo pronto:\s*(.+)")
RE_TITULO   = re.compile(r"Pipeline:\s*(.+?)\s*\(")
RE_TRILHA   = re.compile(r"\[TRILHA\] Bloco (\d+)/(\d+)")
RE_TRILHA_OK= re.compile(r"✓ Trilha din[âa]mica")
RE_LEGENDA  = re.compile(r"Gerando legendas|cards")
RE_LEGENDA_OK = re.compile(r"✓ Legendas.*queimad")
RE_UPSCALE  = re.compile(r"Upscalando")
RE_CENSURA  = re.compile(r"[Cc]ensura|censurad")


def _run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=15)
        raw = r.stdout or b""
        # PowerShell/tasklist saem em cp1252 no Windows PT; tenta utf-8 e cai pra cp1252.
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("cp1252", errors="replace")
    except Exception:
        return ""


def snapshot_processos():
    """UMA única chamada ao PowerShell coleta tudo (evita flicker por lentidão):
    processos hiper-pipeline (pid/cmdline), cópia real via ffmpeg, e contagens.
    Retorna (renders, n_ffmpeg, n_python)."""
    ps = (
        "[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
        "$ps = Get-CimInstance Win32_Process; "
        "$ff = $ps | Where-Object { $_.Name -eq 'ffmpeg.exe' }; "
        "$py = $ps | Where-Object { $_.Name -eq 'python.exe' }; "
        "Write-Output ('FFCOUNT|' + @($ff).Count); "
        "Write-Output ('PYCOUNT|' + @($py).Count); "
        "$ff | ForEach-Object { Write-Output ('FFCMD|' + $_.CommandLine) }; "
        "$ps | Where-Object { $_.CommandLine -match 'hiper-pipeline' } | "
        "ForEach-Object { Write-Output ('PIPE|' + $_.ProcessId + '|' + $_.CommandLine) }"
    )
    out = _run(["powershell.exe", "-NoProfile", "-Command", ps])
    nf = np = 0
    copia = None
    renders = []
    for line in out.splitlines():
        if line.startswith("FFCOUNT|"):
            try: nf = int(line.split("|", 1)[1])
            except Exception: pass
        elif line.startswith("PYCOUNT|"):
            try: np = int(line.split("|", 1)[1])
            except Exception: pass
        elif line.startswith("FFCMD|"):
            for m in re.finditer(r"D:\\(hipercool-[\w-]+)\\", line):
                if m.group(1) != "hipercool-videos":
                    copia = m.group(1)
        elif line.startswith("PIPE|"):
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            pid, cmd = parts[1], parts[2]
            cap = "?"
            mc = re.search(r"cap(\d+)", cmd)
            if mc:
                cap = f"cap{int(mc.group(1)):02d}"
            mt = re.search(r'--titulo\s+"?([^"]+?)"?\s+--', cmd)
            titulo = mt.group(1).strip() if mt else ""
            renders.append({"pid": pid.strip(), "cap": cap, "titulo": titulo})
    for r in renders:
        r["copia"] = copia or "?"
    # Vários processos hiper-pipeline (pai + filhos). Prioriza os que têm cap/título
    # detectado — o processo-pai tem os args completos; os filhos não.
    renders.sort(key=lambda r: (r["cap"] == "?", not r["titulo"]))
    return renders, nf, np


def achar_log(cap):
    """Acha o log MAIS recente que corresponde ao cap em geração (raiz ou logs/)."""
    cands = []
    for pat in (f"cap{cap[-2:]}_*.log", f"*{cap}*.log",
                f"logs/nightshift_{cap}_*.log", f"logs/*{cap}*.log", f"logs/cap{cap[-2:]}_*.log"):
        cands += glob.glob(str(PROJECT_DIR / pat))
    # também considera o log mais recente da raiz/logs em geral
    cands += glob.glob(str(PROJECT_DIR / "cap*_*.log"))
    cands += glob.glob(str(PROJECT_DIR / "logs" / "nightshift_*.log"))
    cands = [c for c in cands if os.path.exists(c)]
    if not cands:
        return None
    return max(cands, key=os.path.getmtime)


def parse_log(path):
    """Extrai etapa + progresso + detalhe fino do log."""
    try:
        txt = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    info = {"titulo": "?", "n_paineis": 0, "etapa": "scrape", "feito": 0, "total": 0,
            "pronto": None, "detalhe": "", "trilha": ""}

    m = RE_TITULO.search(txt)
    if m:
        info["titulo"] = m.group(1).strip()
    m = RE_PAINEIS.search(txt)
    if m:
        info["n_paineis"] = int(m.group(1))

    pronto = None
    for m in RE_PRONTO.finditer(txt):
        pronto = m.group(1).strip()

    clips = RE_CLIP.findall(txt)
    ttss = RE_TTS.findall(txt)
    visions = RE_VISION.findall(txt)
    trilhas = RE_TRILHA.findall(txt)

    # Determina etapa pela marca mais avançada presente.
    if pronto:
        info.update(etapa="pos", pronto=pronto)
    elif RE_UPSCALE.search(txt) and RE_LEGENDA_OK.search(txt):
        info["etapa"] = "upscale"
    elif RE_LEGENDA_OK.search(txt) or (RE_LEGENDA.search(txt) and RE_TRILHA_OK.search(txt)):
        info["etapa"] = "legenda"
    elif RE_TRILHA_OK.search(txt) or trilhas:
        info["etapa"] = "trilha"
        if trilhas:
            cur, tot = trilhas[-1]
            info.update(feito=int(cur), total=int(tot))
    elif clips:
        cur, tot = clips[-1]
        info.update(etapa="render", feito=int(cur), total=int(tot))
        dm = None
        for dm in RE_CLIP_DET.finditer(txt):
            pass
        if dm:
            painel, voz, trans, sfx = dm.group(3), dm.group(4), dm.group(5), dm.group(6)
            info["detalhe"] = f"{painel} · voz={voz} · trans={trans}" + (f" · sfx={sfx}" if sfx else "")
    elif ttss:
        n = max(int(x) for x in ttss) + 1
        info.update(etapa="tts", feito=n, total=info["n_paineis"] or n)
    elif RE_NARR.search(txt) and RE_DESCR_OK.search(txt):
        info["etapa"] = "narracao"
    elif visions:
        cur, tot = visions[-1]
        info.update(etapa="vision", feito=int(cur), total=int(tot))

    # se a etapa é censura (aparece perto do fim)
    if not pronto and info["etapa"] in ("upscale", "legenda") and RE_CENSURA.search(txt.split("Upscalando")[-1] if "Upscalando" in txt else ""):
        info["etapa"] = "censura"
    return info


def pct_global(info):
    acc = 0.0
    for key, _, peso in ETAPAS:
        if key == info["etapa"]:
            frac = (info["feito"] / info["total"]) if info["total"] else 0.5
            return min(99, int((acc + peso * frac) * 100))
        acc += peso
    return 100


def barra(pct, larg=34):
    cheio = int(larg * pct / 100)
    return "█" * cheio + "░" * (larg - cheio)


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def depth_info():
    try:
        pngs = list(DEPTH_CACHE.glob("*.png"))
        recente = max((p.stat().st_mtime for p in pngs), default=0)
        idade = time.time() - recente if recente else 1e9
        return len(pngs), idade
    except Exception:
        return 0, 1e9


def eta_str(log_path, pct):
    """Estima o tempo restante cruzando o tempo JÁ decorrido (início do log → agora)
    com a % concluída. ETA = decorrido × (100-pct)/pct. Grosseira mas útil."""
    try:
        if not log_path or pct <= 0 or pct >= 100:
            return None
        # tempo decorrido = mtime atual - tempo de criação do log
        st = os.stat(log_path)
        inicio = getattr(st, "st_ctime", None) or st.st_mtime
        decorrido = time.time() - inicio
        if decorrido < 5:
            return None
        restante = decorrido * (100 - pct) / pct
        restante = min(restante, 3 * 3600)  # teto de sanidade 3h
        m = int(restante // 60)
        s = int(restante % 60)
        if m >= 60:
            return f"~{m//60}h{m%60:02d}min restantes"
        if m >= 1:
            return f"~{m}min{s:02d}s restantes"
        return f"~{s}s restantes"
    except Exception:
        return None


def render():
    L = []
    agora = datetime.now().strftime("%H:%M:%S")
    L.append("╔════════════════════════════════════════════════════════════════╗")
    L.append(f"║  PAINEL HIPERCOOL — geração ao vivo              {agora}       ║")
    L.append("╚════════════════════════════════════════════════════════════════╝")

    renders, of, op = snapshot_processos()

    if renders:
        for r in renders[:1]:  # normalmente 1 (regra: nunca 2 caps juntos)
            log = achar_log(r["cap"] if r["cap"] != "?" else "")
            info = parse_log(log) if log else None
            L.append(f"\n▶ GERANDO AGORA — {r['cap'].upper()}   [cópia: {r['copia']}]")
            if r["titulo"]:
                L.append(f"  título: {r['titulo']}")
            if info:
                pct = pct_global(info)
                eta = eta_str(log, pct)
                L.append(f"  {barra(pct)} {pct}%" + (f"   ⏱ {eta}" if eta else ""))
                det = f" {info['feito']}/{info['total']}" if info["total"] else ""
                L.append(f"  ETAPA: {ETAPA_NOME.get(info['etapa'], info['etapa'])}{det}")
                if info["detalhe"]:
                    L.append(f"  → {info['detalhe']}")
                if info["pronto"]:
                    L.append(f"  ✓ VÍDEO PRONTO: {Path(info['pronto']).name}")
                if log:
                    idade = int(time.time() - os.path.getmtime(log))
                    L.append(f"  log: {Path(log).name} (há {idade}s) · pid {r['pid']}")
            else:
                L.append(f"  (log ainda não encontrado — pid {r['pid']})")
    else:
        L.append("\n▶ Nenhum render de vídeo ativo agora.")

    # Fila
    st = load_state()
    if st:
        oks = sorted(int(k) for k, v in st.items() if v.get("status") == "ok")
        ref = sorted(int(k) for k, v in st.items() if v.get("status") != "ok")
        L.append("\n📋 FILA (the-meek-cat):")
        L.append(f"  ✓ prontos: {', '.join(f'cap{n:02d}' for n in oks) or '—'}")
        if ref:
            L.append(f"  ⟳ refazer: {', '.join(f'cap{n:02d}' for n in ref)}")

    # Worker / parallax
    nd, idade_d = depth_info()
    ativo = "ativo agora" if idade_d < 120 else f"parado há {int(idade_d/60)}min" if idade_d < 1e8 else "—"
    L.append(f"\n🔧 WORKER/PARALLAX: {nd} depths em cache ({ativo})")
    L.append(f"⚙  processos: {of} ffmpeg · {op} python")

    # Erros recentes
    errf = LOGS_DIR / "errors.jsonl"
    if errf.exists():
        try:
            ults = errf.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-3:]
            if ults:
                L.append("\n⚠ ÚLTIMOS ERROS/AVISOS:")
                for ln in ults:
                    try:
                        rr = json.loads(ln)
                        L.append(f"  [{rr.get('ts','')[-8:]}] {rr.get('msg','')[:56]}")
                    except Exception:
                        pass
        except Exception:
            pass
    return "\n".join(L)


def main():
    if "--once" in sys.argv:
        print(render())
        return
    if os.name == "nt":
        os.system("")  # habilita sequências ANSI no console do Windows
    print("\033[2J", end="")  # limpa 1 vez só
    try:
        while True:
            # 1) MONTA o texto (parte lenta: ~1 chamada PowerShell) — tela ainda visível.
            texto = render() + f"\n\n(atualiza a cada {REFRESH_S}s — Ctrl-C pra sair)"
            # 2) Só então reposiciona o cursor no topo e reescreve de uma vez (sem apagar
            #    a tela antes → sem flicker). \033[H = cursor pro topo; \033[J = limpa daqui pra baixo.
            sys.stdout.write("\033[H" + texto.replace("\n", "\033[K\n") + "\033[J")
            sys.stdout.flush()
            time.sleep(REFRESH_S)
    except KeyboardInterrupt:
        print("\nSaindo.")


if __name__ == "__main__":
    main()
