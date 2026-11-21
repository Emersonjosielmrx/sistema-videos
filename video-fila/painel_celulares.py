r"""painel_celulares.py — ranking dos canais postados pelos CELULARES (dona 20/11: "gráfico separado na página inicial,
mais difícil de atualizar; botão de atualização e ranking separado").

Fonte: D:\projeto celular sub controle\canal_pronto\escada.json (a escada mede de 2 em 2 h pela tela "Seus vídeos" do
app). Atualizar = roda `escada_celulares.py medir` escondido (um celular por vez; leva alguns minutos).
Doc com o ranking escrito: D:\projeto celular sub controle\RANKING_VISUALIZACOES_CELULARES.md.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

PROJ = Path(r"D:\projeto celular sub controle")
ESCADA = PROJ / "canal_pronto" / "escada.json"
PEDIDOS = PROJ / "canal_pronto" / "pedidos"
PY = r"C:\Users\Haylla\AppData\Local\Programs\Python\Python313\python.exe"
VBS = r"D:\rodar_oculto.vbs"
_MEDINDO = PROJ / "canal_pronto" / "_medindo_painel.txt"


def _nome_canal(email):
    for a in sorted(PEDIDOS.glob("*.json"), reverse=True):
        try:
            p = json.loads(a.read_text("utf-8"))
        except (OSError, ValueError):
            continue
        if str(p.get("email", "")).lower() == str(email).lower() and p.get("nome"):
            return p["nome"]
    return email


def api_ranking(_p=None):
    try:
        d = json.loads(ESCADA.read_text("utf-8"))["canais"]
    except (OSError, ValueError, KeyError) as e:
        return {"erro": f"escada.json: {e}"}
    canais, shorts = [], []
    # 21/11: o mesmo canal aparece com chave antiga ("A2") e nova ("A2:email") — junta pelo e-mail, e cada Short vale a
    # MAIOR leitura já vista (uma medida pode ler só parte da tela; ontem o Oculto Mundial "caiu" de 5.000 pra 1.806)
    junto = {}
    for chave, ch in d.items():
        em = (ch.get("email") or chave).lower()
        j = junto.setdefault(em, {"chave": chave, "email": ch.get("email", ""), "handle": ch.get("handle"),
                                  "medidas": [], "melhor": {}})
        j["medidas"] += ch.get("medidas") or []
        for x in ch.get("medidas") or []:
            for t, n in x.get("videos") or []:
                j["melhor"][t] = max(n, j["melhor"].get(t, 0))
    d = {v["chave"]: {"email": v["email"], "handle": v["handle"],
                      "medidas": sorted(v["medidas"], key=lambda x: x["em"]) + [
                          {"em": max((x["em"] for x in v["medidas"]), default=""), "videos": list(v["melhor"].items())}]}
         for v in junto.values()}
    for chave, ch in d.items():
        m = ch.get("medidas") or []
        # última medida COM vídeos (a de celular sem banda volta vazia)
        ult = next((x for x in reversed(m) if x.get("videos")), None)
        nome = _nome_canal(ch.get("email", ""))
        cel = chave.split(":")[0]
        if not ult:
            canais.append({"canal": nome, "handle": ch.get("handle"), "celular": cel, "views": 0, "shorts": 0,
                           "melhor": "", "medido": None, "serie": []})
            continue
        vids = [(t, n) for t, n in ult["videos"]]
        tot = sum(n for _t, n in vids)
        melhor = max(vids, key=lambda x: x[1]) if vids else ("", 0)
        serie = [{"em": x["em"], "views": sum(n for _t, n in x.get("videos") or [])} for x in m if x.get("videos")][-24:]
        canais.append({"canal": nome, "handle": ch.get("handle"), "celular": cel, "views": tot,
                       "shorts": sum(1 for _t, n in vids if n > 0), "melhor": melhor[0][:60], "melhor_v": melhor[1],
                       "medido": ult["em"], "serie": serie})
        for t, n in vids:
            if n > 0:
                shorts.append({"titulo": t[:90], "views": n, "canal": nome, "celular": cel})
    canais.sort(key=lambda x: -x["views"])
    shorts.sort(key=lambda x: -x["views"])
    medindo = _MEDINDO.exists() and (datetime.now().timestamp() - _MEDINDO.stat().st_mtime) < 3600
    return {"canais": canais, "shorts": shorts[:20], "medindo": medindo,
            "total": sum(c["views"] for c in canais), "doc": str(PROJ / "RANKING_VISUALIZACOES_CELULARES.md")}


def api_medir(_body=None):
    """Botão 'atualizar': roda a medição da escada escondida (não posta nada)."""
    if _MEDINDO.exists() and (datetime.now().timestamp() - _MEDINDO.stat().st_mtime) < 3600:
        return {"ok": True, "msg": "já está medindo"}
    _MEDINDO.write_text(datetime.now().isoformat(timespec="minutes"), "utf-8")
    cmd = PROJ / "canal_pronto" / "_medir_painel.cmd"
    cmd.write_text("@echo off\r\nchcp 65001 >nul\r\ncd /d \"%s\"\r\nset PYTHONIOENCODING=utf-8\r\n"
                   "\"%s\" canal_pronto\\escada_celulares.py medir >> canal_pronto\\_medir_painel.log 2>&1\r\n"
                   "del \"%s\"\r\n" % (PROJ, PY, _MEDINDO), encoding="utf-8")
    subprocess.Popen(["wscript.exe", VBS, str(cmd)], creationflags=0x08000000)
    return {"ok": True, "msg": "medindo os canais dos celulares (um por vez, alguns minutos)"}
