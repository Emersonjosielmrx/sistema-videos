# -*- coding: utf-8 -*-
"""Cliente do gerador de imagem pelo Google Flow (Nano Banana 2.1) para QUALQUER projeto e qualquer Python — só
biblioteca padrão: roda o gera_imagem.py com o Python do Veo (playwright/filelock moram lá).

Dono 22/10/2026: "nos lugares dos geradores de imagem coloque esse sistema (capas, imagens dos geradores de vídeo)".
Quem chama mantém o gerador antigo como reserva: gerar() devolve None quando o Flow não entrega e o projeto segue.

    import sys; sys.path.insert(0, r"D:\\flow-imagens")
    import cliente
    p = cliente.gerar("prompt", r"saida.jpg", formato="16:9")   # Path ou None

None rápido (sem esperar) quando: FLOW_IMAGEM=0 (desliga), o PC não tem o Flow (PC2, desktop) ou o Flow ficou fora
há pouco (nenhuma conta entregou: pausa de 30 min em logs\\cliente_pausa.json, pra não gastar minutos em cada imagem).
"""
import json
import os
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
PY = Path(r"D:\veo\venv\Scripts\python.exe")
SCRIPT = BASE / "gera_imagem.py"
# 14/11/2026 (dona): TRIO de imagem = 1º Gemini sem navegador (D:\gemini-argo\gemini_midia_http.py, ~15 s, não gasta
# Argon) -> 2º Flow sem navegador (HTTP do gera_imagem) -> 3º Flow com navegador (tela, o próprio gera_imagem cai nela).
# O Gemini roda com o Python do Argon (requests). GEMINI_IMAGEM=0 / GEMINI_MIDIA=0 desligam só o 1º passo.
PY_GEMINI = Path(r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe")
SCRIPT_GEMINI = Path(r"D:\gemini-argo\gemini_midia_http.py")


def _gemini(prompt, saida, formato, log, timeout=150):
    """1º do trio. Path ou None (nunca levanta). Sem foto de referência (o HTTP do Gemini ainda não anexa)."""
    if os.environ.get("GEMINI_MIDIA", "1") == "0" or os.environ.get("GEMINI_IMAGEM", "1") == "0":
        return None
    if not (PY_GEMINI.exists() and SCRIPT_GEMINI.exists()):
        return None
    t0 = time.time()
    try:
        r = subprocess.run([str(PY_GEMINI), "-X", "utf8", "-I", str(SCRIPT_GEMINI), "imagem", prompt, str(saida),
                            "--formato", formato], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as e:  # noqa: BLE001
        log(f"[gemini] não rodou ({type(e).__name__}) -> Flow")
        return None
    if r.returncode == 0 and saida.exists() and saida.stat().st_size > 10_000:
        log(f"[gemini] ok {saida.name} em {time.time() - t0:.0f}s ({(r.stdout or '').strip()[-80:]})")
        return saida
    log(f"[gemini] não gerou em {time.time() - t0:.0f}s ({((r.stdout or '') + (r.stderr or '')).strip()[-160:]}) -> Flow")
    return None
PAUSA = BASE / "logs" / "cliente_pausa.json"
PAUSA_S = 1800
FORMATOS = {"16:9": 16 / 9, "4:3": 4 / 3, "1:1": 1.0, "3:4": 3 / 4, "9:16": 9 / 16}


def _pausado():
    try:
        return json.loads(PAUSA.read_text("utf-8")).get("ate", 0) > time.time()
    except Exception:  # noqa: BLE001
        return False


def _pausar(motivo):
    try:
        PAUSA.parent.mkdir(parents=True, exist_ok=True)
        PAUSA.write_text(json.dumps({"ate": time.time() + PAUSA_S, "motivo": motivo[:300],
                                     "quando": time.strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=False), "utf-8")
    except Exception:  # noqa: BLE001
        pass


def disponivel():
    return os.environ.get("FLOW_IMAGEM", "1") != "0" and PY.exists() and SCRIPT.exists() and not _pausado()


def formato_mais_proximo(aspect):
    """'16:9', '1344x768', '1024x1792', 1.78... -> um dos formatos do Flow."""
    try:
        if isinstance(aspect, (int, float)):
            r = float(aspect)
        else:
            a, b = str(aspect).lower().replace("x", ":").split(":")
            r = float(a) / float(b)
    except Exception:  # noqa: BLE001
        return "9:16"
    return min(FORMATOS, key=lambda f: abs(FORMATOS[f] - r))


def gerar(prompt, saida, formato="9:16", refs=(), timeout=780, max_contas=3, log=None):
    """Path da imagem salva em `saida` (png/jpg pela extensão) ou None. Nunca levanta.
    Ordem (14/11): Gemini sem navegador -> Flow HTTP -> Flow tela."""
    log = log or (lambda m: None)
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    if not refs:
        feito = _gemini(prompt, saida, formato_mais_proximo(formato), log)
        if feito:
            return feito
    if not disponivel():
        return None
    cmd = [str(PY), str(SCRIPT), prompt, str(saida), "--formato", formato_mais_proximo(formato),
           "--max-contas", str(max_contas)]
    if refs:
        cmd += ["--ref", *[str(r) for r in refs]]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        _pausar(f"passou de {timeout}s")
        log(f"[flow] passou de {timeout}s — Flow em pausa 30 min, segue o gerador antigo")
        return None
    except Exception as e:  # noqa: BLE001
        log(f"[flow] não rodou: {e}")
        return None
    if r.returncode == 0 and saida.exists() and saida.stat().st_size > 10_000:
        log(f"[flow] ok {saida.name} em {time.time() - t0:.0f}s")
        return saida
    saida_txt = (r.stdout or "")[-600:] + (r.stderr or "")[-600:]
    if "recusou" not in saida_txt:  # recusa por política é do pedido, não do Flow: não pausa
        _pausar(saida_txt.strip().splitlines()[-1] if saida_txt.strip() else "falhou")
    log(f"[flow] não gerou em {time.time() - t0:.0f}s ({(saida_txt.strip().splitlines() or ['?'])[-1][:160]})")
    return None
