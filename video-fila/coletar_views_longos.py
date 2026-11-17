# -*- coding: utf-8 -*-
r"""coletar_views_longos.py — 1 foto por rodada das views dos LONGOS (dona 16/11: "views e horas ganhas hoje nos longos,
em gráfico no painel, separado dos Shorts"). O views_longos.json só guarda o total atual; sem histórico não dá pra saber o
ganho do dia. Grava em estado\views_longos_hist.jsonl: {ts, views, horas, n, por_canal{canal:[views,horas]}}.
Horas = views x duração média (leitura MAIS NOVA do Studio, metricas_studio.json ret_lista). Tarefa ColetarViewsLongos
(hora em hora, oculta). Desligar: COLETAR_VIEWS_LONGOS=0.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

VL = Path(r"D:\recapd-ambientes\producao\colab\views_longos.json")
MS = Path(r"D:\postador-de-videos\_analise\metricas_studio.json")
SAIDA = Path(r"D:\video-fila\estado\views_longos_hist.jsonl")


def _dur(ms, k):
    m = ms.get(k) or {}
    rl = m.get("ret_lista") or {}
    if rl.get("dur_media") and (rl.get("em") or "") > (m.get("lido_em") or ""):
        return float(rl["dur_media"])
    return float(m.get("dur_media") or 0)


def foto():
    vl = json.loads(VL.read_text(encoding="utf-8"))
    try:
        ms = json.loads(MS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        ms = {}
    tv, th, pc = 0, 0.0, {}
    for k, x in vl.items():
        v = int(x.get("views") or 0)
        h = v * _dur(ms, k) / 3600
        tv += v
        th += h
        c = pc.setdefault(x.get("canal") or "?", [0, 0.0])
        c[0] += v
        c[1] = round(c[1] + h, 2)
    lido = max((x.get("lido") or "" for x in vl.values()), default="")
    return {"ts": datetime.now().isoformat(timespec="minutes"), "lido": lido, "views": tv, "horas": round(th, 2),
            "n": len(vl), "por_canal": pc}


def fila_melhorador():
    """Foto da fila do melhorador dos longos (vídeos esperando análise) pro gráfico do painel."""
    for p in (Path(r"D:\recapd-ambientes\producao\melhorador_estado.json"),
              Path(r"D:\video-fila\linhas\LONGOS\melhorador_estado.json")):
        try:
            fa = json.loads(p.read_text(encoding="utf-8")).get("fila_analise") or {}
        except (OSError, ValueError):
            continue
        if fa:
            with Path(r"D:\video-fila\estado\fila_melhorador_hist.jsonl").open("a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": datetime.now().isoformat(timespec="minutes"),
                                    "atrasados": fa.get("atrasados", 0)}) + "\n")
            return


def main():
    if os.environ.get("COLETAR_VIEWS_LONGOS", "1") == "0":
        return
    try:
        fila_melhorador()
    except Exception:  # noqa: BLE001
        pass
    # 17/11 dona ("horas dos longos são as mesmas de ontem — ninguém assistiu?"): o views_longos.json só era relido
    # pelo postar_longos de 6 em 6 h (última leitura 06:10 até 13 h). Aqui relê os com mais de 2 h (página pública do
    # vídeo, sem conta, 1 pedido a cada 3 s). COLETAR_RELER_LONGOS=0 desliga.
    if os.environ.get("COLETAR_RELER_LONGOS", "1") != "0":
        try:
            os.environ.setdefault("VIEWS_LONGOS_IDADE_H", "2")
            sys.path.insert(0, str(VL.parent))
            import views_longos
            views_longos.atualizar()
        except Exception as e:  # noqa: BLE001
            if sys.stdout:
                print(f"releitura falhou: {type(e).__name__}: {e}")
    r = foto()
    # só grava se a leitura mudou (views_longos é relido a cada ~6 h) ou se passou 1 dia — o arquivo não incha à toa
    ult = None
    if SAIDA.exists():
        try:
            ult = json.loads(SAIDA.read_text(encoding="utf-8").strip().splitlines()[-1])
        except (OSError, ValueError, IndexError):
            ult = None
    if ult and ult.get("lido") == r["lido"] and ult.get("views") == r["views"] and ult["ts"][:10] == r["ts"][:10]:
        return
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("a", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
    if sys.stdout:
        print(r["ts"], r["views"], r["horas"])


if __name__ == "__main__":
    main()
