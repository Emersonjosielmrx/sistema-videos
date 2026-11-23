"""teste_publico_punidos.py — 23/11 dona: "pode postar 1 Short em cada um dos punidos agora mesmo, já como PÚBLICO (não
programado). Se até o final do dia todos tiverem 1 visualização, é mais da metade de certeza que estão mortos."

Hipótese: a punição pega os Shorts AGENDADOS (subidos dias antes); Short público na hora pode furar. Dado de 17-22/11:
Comédia Noturna — 1 Short público na hora = 624 views x 20 agendados = mediana 2.

Para cada canal marcado "punido" em config/rampa_canais.json: 1 Short pronto (Fish primeiro, local primeiro), sobe
pela mesma política do parceiro_diario (pol.postar_youtube) com privacy public e SEM publish_at = abre na hora.
Anota em estado/teste_publico_punidos.json (canal, vídeo, hora) pra medir à noite: medir_teste_publico_punidos().
Exceção à regra "todo Short agendado" (26/10) SÓ neste teste, aprovada pela dona 23/11.
    python teste_publico_punidos.py [--ensaio]        python teste_publico_punidos.py --medir
"""
import json
import sys
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import parceiro_diario as pd  # noqa: E402

pol = pd._politica()
EST = BIN.parent / "estado" / "teste_publico_punidos.json"


def punidos():
    rampa = json.loads(Path(r"D:\postador-de-videos\config\rampa_canais.json").read_text(encoding="utf-8"))
    return {cid for cid, c in (rampa.get("canais") or {}).items() if c.get("punido")}


def rodar(ensaio=False):
    c = pd.cfg()
    its = pd.itens(c)
    est = json.loads(EST.read_text(encoding="utf-8")) if EST.exists() else {"postados": []}
    ja = {p["canal_id"] for p in est["postados"] if p.get("em", "")[:10] == datetime.now().date().isoformat()}
    alvo = punidos()
    for dst in c.get("pt") or []:
        cid = dst["canal"]
        if cid not in alvo or cid in ja:
            continue
        nome = dst["nome"]
        canal, err = pol.achar_canal(cid)
        if not canal:
            pd.log(f"[teste público] {nome}: {err}")
            continue
        prontos = [x for x in its if x["canal"] == cid and x["estado"] == "pronto"]
        prontos.sort(key=lambda y: (0 if pd._motor_novo(y) else 1, 1 if (y["pj"].parent / "_NO_DRIVE.txt").exists() else 0))
        if not prontos:
            pd.log(f"[teste público] {nome}: nenhum Short pronto")
            continue
        x = prontos[0]
        if (x["pj"].parent / "_NO_DRIVE.txt").exists() and not ensaio and not pd._trazer_do_drive(x, nome):
            continue
        tit = x["d"].get("titulo") or x["pj"].parent.name
        if ensaio:
            pd.log(f"[teste público][ensaio] {nome}: {x['pj'].parent.name} | {tit[:60]}")
            continue
        thumb = x["pj"].parent / x["d"]["thumb"] if x["d"].get("thumb") else None
        if thumb and not (thumb.is_file() and thumb.stat().st_size < 2_000_000):
            thumb = None
        pol.marcar_aprovacao(x["mp4"], "aprovado", pd.NOTA_APROVACAO)
        status, info = pol.postar_youtube(
            cid, str(x["mp4"]), tit, x["d"].get("descricao", ""), x["d"].get("tags") or [], privacy="public",
            publish_at=None, projeto=pd.PROJETO, thumbnail=thumb, tipo=x["d"].get("tipo") or "short",
            sintetico=bool(x["d"].get("sintetico")))
        pd.log(f"[teste público] {nome}: {status} {info} | {tit[:60]}")
        if status != "ok":
            continue
        agora = datetime.now().astimezone().isoformat(timespec="seconds")
        pd._gravar(x["pj"], posted_url=info, posted_at=agora, agendado_para=agora, canal_postado=nome,
                   teste_publico_punido=True)
        est["postados"].append({"canal_id": cid, "canal": nome, "url": info, "em": agora, "pasta": x["pj"].parent.name})
        EST.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")


def medir():
    import urllib.request
    est = json.loads(EST.read_text(encoding="utf-8")) if EST.exists() else {"postados": []}
    for p in est["postados"]:
        vid = str(p.get("url", "")).rsplit("/", 1)[-1]
        try:
            html = urllib.request.urlopen(urllib.request.Request(
                f"https://www.youtube.com/shorts/{vid}", headers={"Accept-Language": "pt-BR"}), timeout=30).read().decode(
                "utf-8", "ignore")
            import re
            m = re.search(r'"viewCount":"(\d+)"', html)
            v = int(m.group(1)) if m else None
        except Exception:  # noqa: BLE001
            v = None
        print(f"{p['canal'][:24]:24} {p['em'][11:16]} {v if v is not None else '?':>6} views  {p['url']}")


if __name__ == "__main__":
    if "--medir" in sys.argv:
        medir()
    else:
        rodar(ensaio="--ensaio" in sys.argv)
