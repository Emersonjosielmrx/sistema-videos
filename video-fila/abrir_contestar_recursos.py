r"""abrir_contestar_recursos.py — abre, UM canal por vez, o Studio na página de Recursos (qualificação) pra dona
contestar os recursos avançados (13/11, dona: "abre que eu contesto os recursos avançados que ainda não foram").

Espera ela FECHAR a janela antes de abrir o próximo (nunca 2 contas abertas juntas pelo mesmo IP). Ordem: prazo
mais longo primeiro. Pula quem já foi contestado (obs "contestou" em config\recursos_negados.json), quem não tem
botão (Assist-IA) e quem não tem login no cofre. Ao fechar, marca "dona contestou <data>" no recursos_negados.json.

    python abrir_contestar_recursos.py            # abre a fila toda, um por vez
    python abrir_contestar_recursos.py fiodameada # só este
"""
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\logins-google")
import cofre  # noqa: E402

NEG = Path(r"D:\postador-de-videos\config\recursos_negados.json")
CANAIS = Path(r"D:\postador-de-videos\config\canais.json")
CONTAS = Path(r"D:\logins-google\cofre\contas.json")
LOG = Path(r"D:\video-fila\logs\contestar_recursos.log")
SEM_BOTAO = {"assistiainvestimentos"}


def log(m):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {m}"
    print(linha, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _channel_id(slug):
    txt = CANAIS.read_text(encoding="utf-8")
    try:
        d = json.loads(txt)
        itens = d if isinstance(d, list) else (d.get("canais") or list(d.values()))
        for c in itens:
            if isinstance(c, dict) and slug in json.dumps(c, ensure_ascii=False).lower() and c.get("channel_id"):
                return c["channel_id"]
    except ValueError:
        pass
    return None


def _email(slug):
    c = json.loads(CONTAS.read_text(encoding="utf-8"))["contas"]
    return next((e for e, v in c.items() if slug in [y.lower() for y in ((v.get("usos") or {}).get("youtube") or [])]),
                None)


def _aberta(porta):
    try:
        return bool(json.loads(urllib.request.urlopen(f"http://127.0.0.1:{porta}/json", timeout=4).read()))
    except Exception:  # noqa: BLE001
        return False


def um(slug):
    email, cid = _email(slug), _channel_id(slug)
    if not email:
        log(f"{slug}: sem login no cofre — pulado")
        return
    url = (f"https://studio.youtube.com/channel/{cid}/editing/details" if cid else "https://studio.youtube.com/")
    porta, _p = cofre.abrir(email, url, visivel=True)
    log(f"{slug}: aberto ({email}) — Studio > Configurações > Canal > Qualificação de recursos > Recursos avançados")
    time.sleep(10)
    fim = time.time() + 45 * 60
    while time.time() < fim and _aberta(porta):
        time.sleep(5)
    d = json.loads(NEG.read_text(encoding="utf-8"))
    if slug in d:
        d[slug]["obs"] = (d[slug].get("obs", "") + f"; janela aberta pra contestar {datetime.now():%d/%m %H:%M}").strip("; ")
        NEG.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"{slug}: janela fechada — próximo")


def main():
    d = json.loads(NEG.read_text(encoding="utf-8"))
    pedidos = [a for a in sys.argv[1:] if not a.startswith("-")]
    fila = pedidos or [s for s, v in sorted(d.items(), key=lambda kv: kv[1].get("ate") or "9999", reverse=True)
                       if "contestou" not in v.get("obs", "").lower() and s not in SEM_BOTAO]
    log(f"fila: {', '.join(fila)}")
    for s in fila:
        um(s)
    log("fim da fila")


if __name__ == "__main__":
    main()
