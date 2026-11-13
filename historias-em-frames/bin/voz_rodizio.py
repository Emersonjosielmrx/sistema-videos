"""Rodízio da voz clonada (dono 25/10): cada vídeo sai com um narrador parceiro diferente (RVC de
D:\\hipercool-materiais\\bin\\voz_clonada.py). Vai o parceiro menos usado; nunca o mesmo do vídeo anterior.
HISTORIAS_VOZ_CLONADA=0 desliga (volta a voz edge normal)."""
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

RAIZ = Path(r"D:\hipercool-materiais")
VOZES = RAIZ / "models" / "rvc" / "vozes"
PY_VOZES = RAIZ / "python" / "venv_vozes" / "Scripts" / "python.exe"
SCRIPT = RAIZ / "bin" / "voz_clonada.py"
ESTADO = Path(__file__).resolve().parent.parent / "workspace" / "voz_rodizio.json"
BASE_EDGE = "pt-BR-FranciscaNeural"
TOM_BASE = "2_edge_francisca"


def parceiros():
    texto = SCRIPT.read_text(encoding="utf-8")
    bloco = texto[texto.find("PARCEIROS = ["):texto.find("BASES = [")]
    return [v for v in re.findall(r'\("(\w+)", "@', bloco) if (VOZES / v / f"{v}.pth").exists()]


def _ler():
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"usos": {}, "ultima": None, "historico": []}


def proxima(story_id=""):
    """Nome do narrador deste vídeo (e já registra o uso), ou None = sem clone."""
    if os.environ.get("HISTORIAS_VOZ_CLONADA", "1") == "0" or not PY_VOZES.exists() or not SCRIPT.exists():
        return None
    lista = parceiros()
    if not lista:
        return None
    est = _ler()
    cands = [v for v in lista if v != est.get("ultima")] or lista
    voz = min(cands, key=lambda v: (est["usos"].get(v, 0), lista.index(v)))
    est["usos"][voz] = est["usos"].get(voz, 0) + 1
    est["ultima"] = voz
    est["historico"] = (est.get("historico") or [])[-199:] + [
        {"quando": datetime.now().isoformat(timespec="seconds"), "voz": voz, "story_id": story_id}]
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(ESTADO) + ".tmp")
    tmp.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, ESTADO)
    return voz


def converter_lote(voz, pares, lista_json, timeout=2700):
    """pares = [(wav_base, wav_saida)]. Applio carrega 1x para todas as frases. Devolve (ok, fim do log)."""
    itens = [{"entrada": str(a), "saida": str(b), "tom_base": TOM_BASE} for a, b in pares]
    Path(lista_json).write_text(json.dumps(itens, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([str(PY_VOZES), str(SCRIPT), "lote", voz, str(lista_json)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return r.returncode == 0, (r.stderr or r.stdout or "")[-400:]
