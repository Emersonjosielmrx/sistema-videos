# -*- coding: utf-8 -*-
r"""vitrine/checklist_like.py — checklist do like + comentário da conta PESSOAL da dona nos vídeos que o telão exibe
(dona 29/10: "os vídeos que ele exibe nos notebooks ele deveria dar like em todos e comentar; veja se está fazendo;
monitoramento, log, checklist"). Só LÊ logs\vitrine.log (quem faz o like é vitrine.curtir_no_telao) e grava
estado\vitrine_checklist.json para o painel (aba "Telão: like e comentário") e avisa no Telegram quando o like está
falhando em série (ex.: http_401 = conta pessoal deslogada no Acer: só a dona resolve, logando lá).

    python vitrine\checklist_like.py            # grava o checklist (tarefa TelaoChecklist, 30 min)
    python vitrine\checklist_like.py --status   # mostra
"""
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"D:\hipercool-materiais\comum")
try:
    import sem_janela  # noqa: F401
except ImportError:
    pass

BASE = Path(r"D:\video-fila")
LOG = BASE / "logs" / "vitrine.log"
SAIDA = BASE / "estado" / "vitrine_checklist.json"
RE_EXIB = re.compile(r"^\[(\d\d/\d\d) (\d\d:\d\d):\d\d\] telão (\S+): (.*?) \| short https://www\.youtube\.com/shorts/([\w-]{11})")
RE_LIKE = re.compile(r"^\[(\d\d/\d\d) (\d\d:\d\d):\d\d\] telão curtir ([\w-]{11}): ([^|]+?)\s*\| comentar: ([^|]+?)\s*\|(?: fixado: (.*))?$")
RE_LIKE_CURTO = re.compile(r"^\[(\d\d/\d\d) (\d\d:\d\d):\d\d\] telão curtir ([\w-]{11}): ([^|]+?)\s*$")
MOTIVOS = {"http_401": "conta pessoal DESLOGADA no Chrome do telão (logar de novo no Acer)",
           "http_403": "YouTube recusou o like (403): conta limitada ou pedido inválido",
           "deslogado": "Chrome do telão sem a conta pessoal", "video_ja_fechou": "o vídeo fechou antes do like (Short curto)",
           "comentarios_fechados": "o canal está com comentários fechados (ligar nas configurações do canal)",
           "sem_resposta": "a página não respondeu ao comentário", "pulado": "comentário não tentado (sorteio 50% / teto do dia)"}


def _ano(dm):
    hoje = datetime.now()
    d = datetime.strptime(f"{dm}/{hoje.year}", "%d/%m/%Y")
    return d - timedelta(days=365) if d > hoje + timedelta(days=1) else d


def ler(dias=7):
    desde = datetime.now() - timedelta(days=dias)
    exib, likes = {}, defaultdict(list)
    for l in LOG.read_text("utf-8", errors="replace").splitlines():
        m = RE_EXIB.match(l)
        if m and _ano(m.group(1)) >= desde:
            exib.setdefault(m.group(5), []).append({"dia": m.group(1), "hora": m.group(2), "telao": m.group(3).split("@")[-1], "canal": m.group(4)})
            continue
        m = RE_LIKE.match(l)
        if m and _ano(m.group(1)) >= desde:
            likes[m.group(3)].append({"dia": m.group(1), "hora": m.group(2), "like": m.group(4).strip()[:40],
                                      "coment": m.group(5).strip()[:30], "fixado": (m.group(6) or "").strip()[:30]})
            continue
        # 11/11: "video_ja_fechou", "sem_botao", "falhou, volta pra fila" não têm "| comentar:" e ficavam de fora
        m = RE_LIKE_CURTO.match(l)
        if m and _ano(m.group(1)) >= desde:
            likes[m.group(3)].append({"dia": m.group(1), "hora": m.group(2), "like": m.group(4).strip()[:40],
                                      "coment": "-", "fixado": ""})
    return exib, likes


def montar(dias=7):
    exib, likes = ler(dias)
    # 11/11: o like sai DIAS depois da exibição (o vídeo que falha volta pra fila e toca de novo). Contar só like de
    # vídeo exibido na mesma janela dava "hoje: 76 exibidos, 0 likes" com 33 likes saindo no dia. Agora: like e
    # comentário contam no dia em que SAÍRAM; pendente = exibido que nunca recebeu like (em nenhum dia do log).
    _, todos_likes = ler(3650)
    ja_curtido = {v for v, ls in todos_likes.items() if any(x["like"] == "ok" for x in ls)}
    por_dia = defaultdict(lambda: {"exibidos": 0, "like_ok": 0, "coment_ok": 0, "like_falhou": 0})
    motivos = Counter(); pendentes = []
    for vid, ls in likes.items():
        for x in ls:
            if x["like"] == "ok":
                por_dia[x["dia"]]["like_ok"] += 1
            elif not x["like"].startswith("falhou"):  # "falhou, volta pra fila" repete o motivo da linha anterior
                motivos[x["like"].split(":")[0]] += 1
            if x["coment"] == "ok":
                por_dia[x["dia"]]["coment_ok"] += 1
    for vid, ex in exib.items():
        d = ex[-1]["dia"]
        por_dia[d]["exibidos"] += 1
        if vid not in ja_curtido:
            por_dia[d]["like_falhou"] += 1
            ls = likes.get(vid) or []
            ult = ls[-1]["like"] if ls else "sem tentativa"
            pendentes.append({"vid": vid, "canal": ex[-1]["canal"], "dia": d, "hora": ex[-1]["hora"], "telao": ex[-1]["telao"],
                              "like": ult, "coment": ls[-1]["coment"] if ls else "-"})
    hoje = datetime.now().strftime("%d/%m")
    ultimas = sorted(((x["dia"], x["hora"], vid, x["like"], x["coment"]) for vid, ls in likes.items() for x in ls), reverse=True)[:40]
    # série de falhas: os últimos 5 likes tentados
    seq = [x[3] for x in ultimas[:5]]
    alerta = None
    h = por_dia.get(hoje) or {}
    if len(seq) >= 3 and all(s.startswith("http_401") or s == "deslogado" for s in seq[:3]):
        alerta = MOTIVOS["http_401"]
    elif h.get("like_falhou", 0) >= 3 and h.get("like_ok", 0) == 0:
        top = motivos.most_common(1)[0][0] if motivos else "?"
        alerta = f"hoje {h['like_falhou']} vídeos exibidos sem like (0 ok); motivo mais comum: {top} — {MOTIVOS.get(top, '')}"
    return {"em": datetime.now().isoformat(timespec="seconds"), "dias": dias, "hoje": por_dia.get(hoje, {"exibidos": 0, "like_ok": 0, "coment_ok": 0, "like_falhou": 0}),
            "por_dia": dict(sorted(por_dia.items())), "exibidos": len(exib),
            "like_ok": sum(d["like_ok"] for d in por_dia.values()),
            "coment_ok": sum(d["coment_ok"] for d in por_dia.values()),
            "motivos_falha": [{"motivo": k, "n": n, "o_que_e": MOTIVOS.get(k, "")} for k, n in motivos.most_common(8)],
            "pendentes": sorted(pendentes, key=lambda p: (p["dia"], p["hora"]), reverse=True)[:60],
            "ultimas_tentativas": [{"dia": d, "hora": h, "vid": v, "like": lk, "coment": c} for d, h, v, lk, c in ultimas],
            "alerta": alerta}


def main(a):
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--status" in a and SAIDA.exists():
        print(SAIDA.read_text("utf-8")[:3000])
        return 0
    r = montar()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(r, ensure_ascii=False, indent=1), "utf-8")
    print(json.dumps({k: r[k] for k in ("exibidos", "like_ok", "coment_ok", "hoje", "alerta")}, ensure_ascii=False))
    print("motivos:", [(m["motivo"], m["n"]) for m in r["motivos_falha"]])
    if r["alerta"]:
        try:
            sys.path.insert(0, str(BASE))
            import avisos
            avisos.enviar("👍 Telão: o like da conta pessoal está falhando — " + r["alerta"], origem="telao", importante=False,
                          chave="<SEGREDO_REMOVIDO>" + r["alerta"][:30])
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
