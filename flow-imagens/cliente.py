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


def _gemini(prompt, saida, formato, log, refs=(), timeout=180):
    """1º do trio. Path ou None (nunca levanta). Com foto de referência desde 14/11 (sobe por HTTP, sem navegador)."""
    if os.environ.get("GEMINI_MIDIA", "1") == "0" or os.environ.get("GEMINI_IMAGEM", "1") == "0":
        return None
    if not (PY_GEMINI.exists() and SCRIPT_GEMINI.exists()):
        return None
    t0 = time.time()
    try:
        cmd = [str(PY_GEMINI), "-X", "utf8", "-I", str(SCRIPT_GEMINI), "imagem", prompt, str(saida), "--formato", formato]
        if refs:
            cmd += ["--ref", *[str(Path(r).resolve()) for r in refs]]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
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


CELULAR = Path(r"D:\projeto celular sub controle\celular_midia.py")


def _celular(prompt, saida, formato, log, refs=(), timeout=420):
    """16/11 dona ("já pode usar os celulares pra gerar imagem"): 4º degrau = app Gemini num celular livre
    (celular_midia.py). Só sem referência (o app não recebe foto pelo adb) e só 9:16 (o pedido do app é vertical).
    CELULAR_IMAGEM=0 desliga. Path ou None, nunca levanta."""
    if refs or formato != "9:16" or os.environ.get("CELULAR_IMAGEM", "1") == "0" or not CELULAR.exists():
        return None
    t0 = time.time()
    try:
        r = subprocess.run([str(PY_GEMINI), "-X", "utf8", str(CELULAR), "imagem", prompt, str(saida)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as e:  # noqa: BLE001
        log(f"[celular] não rodou ({type(e).__name__})")
        return None
    if r.returncode == 0 and saida.exists() and saida.stat().st_size > 10_000:
        log(f"[celular] ok {saida.name} em {time.time() - t0:.0f}s ({(r.stdout or '').strip().splitlines()[-2][:90]})")
        return saida
    log(f"[celular] não gerou em {time.time() - t0:.0f}s ({(r.stdout or '').strip()[-160:]})")
    return None


def gerar(prompt, saida, formato="9:16", refs=(), timeout=780, max_contas=3, log=None):
    """Path da imagem salva em `saida` (png/jpg pela extensão) ou None. Nunca levanta.
    Ordem (14/11): Gemini sem navegador -> Flow HTTP -> Flow tela -> (16/11) celular."""
    log = log or (lambda m: None)
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    feito = _gemini(prompt, saida, formato_mais_proximo(formato), log, refs=refs)
    if feito:
        return feito
    # 18/11 dona ("manter os celulares sempre ocupados"): o celular era o ÚLTIMO degrau e quase nunca recebia pedido
    # (13 tentativas em 24 h). Agora, com celular LIVRE (sem trava/pausa) e pedido 9:16 sem referência, ele vem antes do
    # Flow; ocupado ou falhou = segue pro Flow como antes. CELULAR_ANTES_FLOW=0 volta à ordem antiga.
    if os.environ.get("CELULAR_ANTES_FLOW", "1") != "0" and not refs and formato_mais_proximo(formato) == "9:16":
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("celular_midia_livres", CELULAR)
            cm = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cm)
            tem_livre = cm.ligado("imagem") and bool(cm.livres("imagem"))
        except Exception:  # noqa: BLE001
            tem_livre = False
        if tem_livre:
            feito = _celular(prompt, saida, "9:16", log, refs=refs)
            if feito:
                return feito
    if not disponivel():
        return _celular(prompt, saida, formato_mais_proximo(formato), log, refs=refs)
    cmd = [str(PY), str(SCRIPT), prompt, str(saida), "--formato", formato_mais_proximo(formato),
           "--max-contas", str(max_contas)]
    if refs:
        cmd += ["--ref", *[str(r) for r in refs]]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                           env={**os.environ, "GEMINI_JA_TENTOU": "1"})  # o gera_imagem não repete o Gemini
    except subprocess.TimeoutExpired:
        _pausar(f"passou de {timeout}s")
        log(f"[flow] passou de {timeout}s — Flow em pausa 30 min, tenta o celular")
        return _celular(prompt, saida, formato_mais_proximo(formato), log, refs=refs)
    except Exception as e:  # noqa: BLE001
        log(f"[flow] não rodou: {e}")
        return _celular(prompt, saida, formato_mais_proximo(formato), log, refs=refs)
    if r.returncode == 0 and saida.exists() and saida.stat().st_size > 10_000:
        log(f"[flow] ok {saida.name} em {time.time() - t0:.0f}s")
        return saida
    saida_txt = (r.stdout or "")[-600:] + (r.stderr or "")[-600:]
    if "recusou" not in saida_txt:  # recusa por política é do pedido, não do Flow: não pausa
        _pausar(saida_txt.strip().splitlines()[-1] if saida_txt.strip() else "falhou")
    log(f"[flow] não gerou em {time.time() - t0:.0f}s ({(saida_txt.strip().splitlines() or ['?'])[-1][:160]})")
    if "recusou" in saida_txt:  # recusa por política: o celular recusaria igual
        return None
    return _celular(prompt, saida, formato_mais_proximo(formato), log, refs=refs)
