"""buscar_fontes_campeas.py — fontes NOVAS do YouTube parecidas com o que está dando certo (12/11/2026).

Dona 12/11: "pesquisar aquele conteúdo que está dando certo, não só nos parceiros mas nos vídeos do YouTube, e deixar
numa lista pra pedir autorização — sempre sem o dono do canal aparecer, um vídeo que possa ser replicado como fazemos".

Como:
  1. Lê o relatório do dia (relatorios\\shorts_foco_<data>.csv, do analise_shorts_foco.py): os Shorts nossos que mais
     renderam (views >= 2x a mediana do canal e >= 500) e os tipos campeões.
  2. Busca no YouTube (yt-dlp, busca anônima, pela vez única do PC — ytdlp_vez; máx. BUSCAS por rodada) pelos temas
     dos títulos campeões + "#shorts".
  3. Para cada canal achado: inscritos, nº de Shorts vistos na busca, views do Short achado e um FILTRO DE ROSTO por
     texto (título/descrição com "eu", "meu canal", "vlog", "minha opinião", "react ao vivo"... = provável dono
     aparecendo -> fica de fora; quem passa ainda é marcado "conferir rosto" pra dona olhar antes de pedir).
  4. Tira quem já é fonte (parceiro.json) e quem já está na lista.
Saída: estado\\fontes_candidatas.json (acumula; nunca apaga o que a dona marcou) + FONTES_PARA_AUTORIZAR.md (lista
pronta pra pedir autorização, melhores primeiro). Só leitura do YouTube; nada posta, nada loga.

    python buscar_fontes_campeas.py [--buscas 12]
"""
import csv
import json
import os
import re
import statistics as st
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
if sys.stdout is None:  # pythonw (tarefa)
    sys.stdout = sys.stderr = open(BASE / "logs" / "buscar_fontes_campeas.log", "a", encoding="utf-8")
else:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\recapd-ambientes\producao\bin")
import ytdlp_vez  # noqa: E402

YTDLP = r"D:\veo\venv\Scripts\yt-dlp.exe"
PARCEIRO = Path(r"D:\recapd-ambientes\producao\config\parceiro.json")
SAIDA = BASE / "estado" / "fontes_candidatas.json"
LISTA = BASE / "FONTES_PARA_AUTORIZAR.md"
ROSTO = re.compile(r"\b(eu|meu canal|minha opini|vlog|react ao vivo|reagindo|ao vivo|live|meu dia|minha rotina|"
                   r"me siga|comigo|minha vida|eu fui|eu testei|reagi)\b", re.I)
OFICIAL = re.compile(r"\b(globo\w*|netflix|prime video|disney\w*|hbo|warner|sbt|record|band|paramount|sony|universal|crunchyroll|studios?|oficial|official|novelas|tv)\b", re.I)
NOME_PESSOA = re.compile(r"[A-ZÀ-Ú][a-zà-ú]+ [A-ZÀ-Ú][a-zà-ú]+( [A-ZÀ-Ú][a-zà-ú]+)?")  # "Fulana Silva" = canal de pessoa
PALAVRAS_VAZIAS = set("de da do das dos e a o as os um uma que com em no na nos nas por para pra mais muito voce você "
                      "isso esse essa ele ela foi mas como quando shorts short sua seu".split())


def campeoes(minimo_views=500):
    arqs = sorted((BASE / "relatorios").glob("shorts_foco_*.csv"))
    if not arqs:
        return []
    with open(arqs[-1], encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    por_canal = defaultdict(list)
    for l in linhas:
        por_canal[l["canal"]].append(float(l["views"] or 0))
    med = {c: st.median(v) for c, v in por_canal.items()}
    out = [l for l in linhas if float(l["views"] or 0) >= max(minimo_views, 2 * med.get(l["canal"], 0))]
    return sorted(out, key=lambda l: -float(l["views"]))


def termo(titulo):
    t = re.sub(r"#\S+|[^\wÀ-ú ]", " ", titulo or "")
    ps = [p for p in t.lower().split() if len(p) > 2 and p not in PALAVRAS_VAZIAS]
    return " ".join(ps[:5])


def buscar(q, n=15):
    with ytdlp_vez.vez(f"fontes campeãs: {q[:40]}"):
        if ytdlp_vez.pausado():
            return []
        r = subprocess.run([YTDLP, f"ytsearch{n}:{q} #shorts", "--flat-playlist", "-J", "--no-warnings"],
                           capture_output=True, text=True, timeout=120, encoding="utf-8", errors="replace",
                           creationflags=0x08000000)
    try:
        return json.loads(r.stdout).get("entries") or []
    except ValueError:
        if "Sign in to confirm" in (r.stderr or "") or "429" in (r.stderr or ""):
            ytdlp_vez.bloqueio(r.stderr)
        return []


def main():
    nbuscas = int(sys.argv[sys.argv.index("--buscas") + 1]) if "--buscas" in sys.argv else 12
    try:
        est = json.loads(SAIDA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = {"canais": {}, "buscados": []}
    cfg = json.loads(PARCEIRO.read_text(encoding="utf-8"))
    ja_fontes = " ".join(f.get("url", "").lower() + " " + f.get("nome", "").lower() for f in cfg.get("fontes", []))
    camps = campeoes()
    termos, vistos = [], set(est.get("buscados") or [])
    for l in camps:
        q = termo(l["titulo"])
        if q and q not in vistos and q not in termos:
            termos.append((q, l))
        if len(termos) >= nbuscas:
            break
    novos = 0
    for q, l in termos:
        for e in buscar(q):
            cid = e.get("channel_id") or e.get("uploader_id")
            nome = e.get("channel") or e.get("uploader") or ""
            if not cid or cid.lower() in ja_fontes or (e.get("uploader_id") or "").lower() in ja_fontes:
                continue
            if OFICIAL.search(nome):  # emissora/streaming/estúdio: não autoriza corte
                continue
            texto = f"{e.get('title') or ''} {e.get('description') or ''}"
            rosto = bool(ROSTO.search(texto)) or bool(NOME_PESSOA.fullmatch(nome.strip()))
            c = est["canais"].setdefault(cid, {"nome": nome, "url": e.get("channel_url") or
                                               f"https://www.youtube.com/channel/{cid}", "achados": [],
                                               "primeiro": datetime.now().isoformat(timespec="minutes"),
                                               "status": "novo"})
            if c["status"] == "novo" and not c["achados"]:
                novos += 1
            if e.get("url") not in [a.get("url") for a in c["achados"]]:
                c["achados"].append({"url": e.get("url"), "titulo": (e.get("title") or "")[:100],
                                     "views": e.get("view_count"), "parecido_com": l["titulo"][:80],
                                     "tipo": l["tipo"], "nosso_canal": l["canal"], "nossas_views": l["views"]})
            c["rosto_provavel"] = c.get("rosto_provavel", False) or rosto
            c["inscritos"] = e.get("channel_follower_count") or c.get("inscritos")
        est.setdefault("buscados", []).append(q)
    est["buscados"] = est["buscados"][-500:]
    est["_quando"] = datetime.now().isoformat(timespec="minutes")
    SAIDA.write_text(json.dumps(est, ensure_ascii=False, indent=1), encoding="utf-8")
    escrever_lista(est)
    print(f"{datetime.now():%d/%m %H:%M} buscas={len(termos)} canais novos={novos} total={len(est['canais'])}")


def escrever_lista(est):
    import math

    def nota(c):
        # 13/11 (pesquisador CURTOS, ideia de slaavass/youtube-outlier-finder): OUTLIER = views muito acima do tamanho
        # do canal. Com inscritos: log10(views ÷ inscritos). Sem (busca flat não traz): log10 das views + 0,5 por
        # tema campeão diferente em que o canal apareceu (aparece em vários = acerta o que rende pra nós).
        # FONTES_NOTA_OUTLIER=0 volta à ordem antiga (nº de achados, maior views).
        vs = [a.get("views") or 0 for a in c["achados"]]
        if os.environ.get("FONTES_NOTA_OUTLIER", "1") == "0":
            return (len(c["achados"]), max(vs) if vs else 0)
        mx = max(vs) if vs else 0
        temas = len({a.get("parecido_com") for a in c["achados"]})
        if c.get("inscritos"):
            return round(math.log10((mx + 1) / (c["inscritos"] + 100)) + 0.5 * temas, 2)
        return round(math.log10(mx + 1) / 2 + 0.5 * temas, 2)
    todos = list(est["canais"].values())
    funil = {"total": len(todos), "rosto_provavel": sum(1 for c in todos if c.get("rosto_provavel")),
             "ja_tratados": sum(1 for c in todos if c["status"] != "novo")}
    bons = [(cid, c) for cid, c in est["canais"].items() if c["status"] == "novo" and not c.get("rosto_provavel")]
    funil["na_lista"] = len(bons)
    bons.sort(key=lambda x: nota(x[1]), reverse=True)
    linhas = [f"# Fontes para pedir autorização — {datetime.now():%d/%m/%Y %H:%M}", "",
              "Canais do YouTube com Shorts parecidos com os NOSSOS que mais renderam (buscar_fontes_campeas.py, todo dia).",
              "Filtro: sem sinal de dono aparecendo pelo texto — **confira o rosto** abrindo 1 Short antes de pedir.",
              "Pedido feito/recusado/aceito: mude `status` em estado\\fontes_candidatas.json (pedido/aceito/recusado/rosto).",
              f"Funil: {funil['total']} canais achados → {funil['rosto_provavel']} fora por sinal de rosto → "
              f"{funil['ja_tratados']} já tratados → **{funil['na_lista']} na lista** (fontes atuais e emissoras/"
              "estúdios oficiais nem entram). Ordem = nota de outlier (views muito acima do tamanho do canal + temas "
              "campeões em que aparece).",
              "", "| # | Nota | Canal | Achados | Maior views | Parecido com (nosso Short) | Tipo | Link |",
              "|---|---|---|---|---|---|---|---|"]
    for i, (cid, c) in enumerate(bons[:60], 1):
        a = max(c["achados"], key=lambda a: a.get("views") or 0)
        linhas.append(f"| {i} | {nota(c)} | {c['nome'][:30]} | {len(c['achados'])} | {a.get('views') or '?'} | "
                      f"{a['parecido_com'][:50]} ({int(a['nossas_views'] if isinstance(a['nossas_views'], (int, float)) else float(a['nossas_views']))} views em {a['nosso_canal']}) | "
                      f"{a['tipo']} | {c['url']} |")
    LISTA.write_text("\n".join(linhas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
