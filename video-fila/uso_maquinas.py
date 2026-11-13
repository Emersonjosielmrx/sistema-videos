r"""uso_maquinas.py — % de aproveitamento de cada máquina (12/11, dona: "o relatório deve ter o que cada máquina está
fazendo e o quanto ela está sendo aproveitada na hora e ao longo do dia; não é só estar fazendo, é estar SEMPRE fazendo").

A cada 5 min (tarefa UsoMaquinas) grava em estado/uso_maquinas.jsonl uma amostra por máquina: CPU, se está TRABALHANDO
(render/Flow/postagem/telão) e o quê. Aproveitamento = % das amostras em que a máquina trabalhava.
  - PC1/PC2/desktop: maquinas.medir (CPU e renders) + controlador.json "agora".
  - notebooks (acer, x200ma): vez do Veo/login/Flow (notebooks_reservados.json) ou telão tocando = trabalhando.
  - STI e celulares: celulares.medir (renders ffmpeg) + reserva da vez.
Só leitura das máquinas (1 medida leve cada; sem rajada: celulares/maquinas já guardam a medida por 1-2 min).

    pythonw uso_maquinas.py            # 1 amostra (a tarefa chama de 5 em 5 min)
    python uso_maquinas.py resumo      # % na última hora e no dia, por máquina
"""
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARQ = BASE / "estado" / "uso_maquinas.jsonl"
RES = Path(r"D:\postador-de-videos\config\notebooks_reservados.json")
MAQS = ("pc1", "pc2", "desktop", "sti", "acer", "x200ma", "s20", "s20ultra")


def _reservas():
    try:
        d = json.loads(RES.read_text(encoding="utf-8"))
        return {m: v.get("por") for m, v in d.items() if float(v.get("ate", 0)) > time.time()}
    except (OSError, ValueError):
        return {}


def _flow_recente(min_=6):
    """12/11 dona ("por que PC2, STI, x200ma, acer, desktop e celulares não estão sendo utilizados?"): o painel não
    contava o Flow — PC2+desktop geraram 59 imagens na última hora (via http:pc2/http:desktop) e marcavam 0%.
    Máquina com imagem do Flow nos últimos min_ minutos = trabalhando. USO_CONTA_FLOW=0 desliga."""
    import os
    if os.environ.get("USO_CONTA_FLOW", "1") == "0":
        return set()
    lim = (datetime.now() - timedelta(minutes=min_)).isoformat()
    quem = set()
    try:
        with open(r"D:\flow-imagens\logs\geracoes.jsonl", "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 200_000))
            linhas = f.read().decode("utf-8", "ignore").splitlines()[1:]
    except OSError:
        return quem
    for l in linhas:
        try:
            d = json.loads(l)
        except ValueError:
            continue
        if str(d.get("quando", "")) >= lim:
            m = (d.get("onde") or str(d.get("via") or "").split(":")[-1]).lower()
            quem.add("pc1" if m == "pc1" else m)
    return quem


def amostra():
    sys.path.insert(0, str(BASE))
    res = _reservas()
    out = []
    try:
        ctl = json.loads((BASE / "estado" / "controlador.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ctl = {}
    agora = ctl.get("agora") or {}
    medidas = ctl.get("medidas") or {}
    flow = _flow_recente()
    for m in MAQS:
        o = {"m": m, "t": datetime.now().isoformat(timespec="minutes"), "cpu": None, "fazendo": "", "trab": False}
        try:
            if m in ("sti", "s20", "s20ultra"):
                import celulares
                md = celulares.medir(m, vale_s=240)
                o["cpu"] = md.get("cpu")
                fz = []
                if md.get("vez") or md.get("renders"):
                    fz.append("render ffmpeg")
                if res.get(m):
                    fz.append(f"vez: {res[m]}")
                if "não respondeu" in str(md.get("motivo")):
                    o["fazendo"] = "fora do ar"
                else:
                    o["fazendo"] = ", ".join(fz) or "livre"
                    o["trab"] = bool(fz)
            elif m in ("acer", "x200ma"):
                md = medidas.get(m) or {}
                o["cpu"] = md.get("cpu")
                fz = []
                if res.get(m):
                    fz.append(f"vez: {res[m]}")
                if "mostrando" in str(md.get("motivo", "")) or "visualizador" in str(md.get("motivo", "")):
                    fz.append("telão")
                o["fazendo"] = ", ".join(fz) or "livre"
                # 12/11: o telão é a função dele, mas a dona mede o aproveitamento pra PRODUZIR: só a vez de trabalho
                # (Veo/Flow/login de produção) conta; telão sozinho = "só telão" (não conta)
                o["trab"] = bool(res.get(m))
            else:
                md = medidas.get(m) or {}
                o["cpu"] = md.get("cpu")
                itens = [x.get("o_que", "")[:60] for x in (agora.get(m) or [])]
                if res.get(m):
                    itens.append(f"vez: {res[m]}")
                o["fazendo"] = "; ".join(i for i in itens if i) or str(md.get("motivo", "livre"))[:60]
                # 12/11: o "agora" do controlador fica velho entre rodadas (desktop "100%" com CPU 0): trabalho de
                # verdade = CPU >= 30% (render/encode) — tarefa listada com CPU parada não conta
                o["trab"] = (o["cpu"] or 0) >= 30
                # 12/11: a CPU do desktop vem SEMPRE 0 pelo ssh (LoadPercentage vazio lá) — ele fez 3 Shorts hoje e o
                # painel dizia 0%. Short em andamento lá (estado\pc3_parceiro.json, apagado quando volta) = trabalhando.
                if m == "desktop" and (BASE / "estado" / "pc3_parceiro.json").exists():
                    o["trab"] = True
        except Exception as e:  # noqa: BLE001
            o["fazendo"] = f"sem medida ({type(e).__name__})"
        if m in flow and not o["trab"]:
            o["trab"] = True
            o["fazendo"] = ("Flow (imagens); " + o["fazendo"]).rstrip("; ")
        out.append(o)
    with ARQ.open("a", encoding="utf-8") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    return out


def resumo():
    agora = datetime.now()
    h1, dia = (agora - timedelta(hours=1)).isoformat(timespec="minutes"), agora.strftime("%Y-%m-%d")
    por = {}
    for l in ARQ.read_text(encoding="utf-8").splitlines() if ARQ.exists() else []:
        try:
            o = json.loads(l)
        except ValueError:
            continue
        d = por.setdefault(o["m"], {"h": [], "d": [], "ult": o})
        if o["t"] >= h1:
            d["h"].append(o["trab"])
        if o["t"].startswith(dia):
            d["d"].append(o["trab"])
        d["ult"] = o
    out = {}
    for m in MAQS:
        d = por.get(m)
        if not d:
            continue
        pct = lambda xs: round(100 * sum(xs) / len(xs)) if xs else None  # noqa: E731
        out[m] = {"hora": pct(d["h"]), "dia": pct(d["d"]), "amostras_dia": len(d["d"]),
                  "agora": d["ult"]["fazendo"], "cpu": d["ult"]["cpu"]}
    return out


if __name__ == "__main__":
    if sys.argv[1:2] == ["resumo"]:
        for m, r in resumo().items():
            print(f"{m:9} hora {str(r['hora']) + '%' if r['hora'] is not None else '-':>5} | dia "
                  f"{str(r['dia']) + '%' if r['dia'] is not None else '-':>5} ({r['amostras_dia']} amostras) | "
                  f"cpu {r['cpu']} | {r['agora']}")
    else:
        amostra()
