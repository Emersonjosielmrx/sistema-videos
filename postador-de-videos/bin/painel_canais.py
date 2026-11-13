#!/usr/bin/env python3
"""painel_canais.py - painel HTML da rede de canais (config/rede_canais.json).

Coleta (Data API, ~4 unidades de cota por canal): inscritos, views, videos; ultimos 30 uploads com views/likes/comentarios,
privacidade e agendamento; ultimos comentarios do publico (para responder). Grava:
  painel/index.html                      painel (abre no navegador)
  painel/historico.jsonl                 1 linha por canal por coleta (crescimento)
  _analise/rede_aprendizado.json         nota de cada video em ~48 h por estrategia (titulo/gancho/comentario/horario)
Uso: python bin/painel_canais.py [--abrir]
"""
import html
import json
import sys
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout:  # pythonw (tarefa agendada) não tem stdout

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import politica  # noqa: E402
import youtube_poster as yp  # noqa: E402

ROOT = BIN.parent
OUT = ROOT / "painel"
HIST = OUT / "historico.jsonl"
APREND = ROOT / "_analise" / "rede_aprendizado.json"
REG = Path(r"D:\hipercool-materiais\_postados\react\publicados.json")
API = "https://www.googleapis.com/youtube/v3"


def get(tok, url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def coletar(canal, cred):
    tok = yp.refresh_access_token(cred)
    ch = get(tok, f"{API}/channels?part=snippet,statistics,contentDetails&mine=true")["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    pl = get(tok, f"{API}/playlistItems?part=snippet,status&maxResults=30&playlistId={up}").get("items", [])
    ids = [i["snippet"]["resourceId"]["videoId"] for i in pl]
    vids = []
    if ids:
        for v in get(tok, f"{API}/videos?part=snippet,statistics,status&id={','.join(ids)}").get("items", []):
            s, st = v.get("statistics", {}), v["status"]
            vids.append({"id": v["id"], "titulo": v["snippet"]["title"], "pub": v["snippet"]["publishedAt"],
                         "privacy": st.get("privacyStatus"), "publishAt": st.get("publishAt"),
                         "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                         "coments": int(s.get("commentCount", 0))})
    coms = []
    try:
        d = get(tok, f"{API}/commentThreads?part=snippet&allThreadsRelatedToChannelId={ch['id']}&maxResults=15&order=time")
        for t in d.get("items", []):
            c = t["snippet"]["topLevelComment"]["snippet"]
            if c.get("authorChannelId", {}).get("value") == ch["id"]:
                continue  # comentario do proprio canal
            coms.append({"video": t["snippet"].get("videoId"), "autor": c.get("authorDisplayName"),
                         "texto": c.get("textOriginal", "")[:300], "quando": c.get("publishedAt"),
                         "respostas": t["snippet"].get("totalReplyCount", 0)})
    except urllib.error.HTTPError:
        pass
    s = ch["statistics"]
    return {"slug": canal["slug"], "nome": canal["nome"], "handle": canal.get("handle"), "status": canal.get("status"),
            "yt_id": ch["id"], "inscritos": int(s.get("subscriberCount", 0)), "views": int(s.get("viewCount", 0)),
            "videos": int(s.get("videoCount", 0)), "uploads": vids, "comentarios": coms}


def aprender(dados):
    """Fecha o ciclo de aprendizado da rede: cada video agendado pela rede e medido UMA vez entre 40 e 60 h depois de
    abrir. nota = views / mediana de views-48h do canal, x (1 + engajamento), com engajamento = (likes + 3*coment.)/views
    (limitado a 0,5). A nota vai para cada braco da estrategia usada (titulo, gancho, comentario, horario) em
    _analise/rede_aprendizado.json, que o mr/rede.py le para escolher a proxima estrategia de cada canal."""
    reg = json.loads(REG.read_text(encoding="utf-8")) if REG.exists() else {}
    apr = json.loads(APREND.read_text(encoding="utf-8")) if APREND.exists() else {}
    canais = apr.setdefault("canais", {})
    hist = apr.setdefault("historico", {})
    medidos = set(apr.setdefault("_medidos", []))
    agora = datetime.now(timezone.utc)
    stats = {v["id"]: v for c in dados for v in c["uploads"]}
    novos = 0
    for r in reg.values():
        if not isinstance(r, dict) or r.get("script") != "rede":
            continue
        vid, slug = r.get("video_id"), r.get("canal_slug")
        if not vid or vid in medidos or vid not in stats or not slug:
            continue
        try:
            aberto = datetime.fromisoformat(r["publish_at"].replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            continue
        if not 40 <= (agora - aberto).total_seconds() / 3600 <= 60:
            continue
        v = stats[vid]
        anteriores = sorted(h["views"] for h in hist.get(slug, [])) + [v["views"]]
        mediana = max(1, sorted(anteriores)[len(anteriores) // 2])
        eng = min(0.5, (v["likes"] + 3 * v["coments"]) / max(1, v["views"]))
        nota = round(v["views"] / mediana * (1 + eng), 3)
        est = dict(r.get("estrategia") or {})
        if r.get("horario"):
            est["horario"] = r["horario"]
        for dim, braco in est.items():
            canais.setdefault(slug, {}).setdefault(dim, {}).setdefault(braco, []).append(nota)
        hist.setdefault(slug, []).append({"vid": vid, "titulo": r.get("titulo", ""), "views": v["views"], "likes": v["likes"],
                                          "coments": v["coments"], "nota": nota, "estrategia": est,
                                          "medido_em": agora.isoformat(timespec="minutes")})
        hist[slug] = hist[slug][-40:]
        medidos.add(vid)
        novos += 1
    apr["_medidos"] = sorted(medidos)
    APREND.parent.mkdir(parents=True, exist_ok=True)
    tmp = APREND.with_suffix(".tmp")
    tmp.write_text(json.dumps(apr, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(APREND)
    return apr, novos


def bloco_falta():
    """Canais que a rede nao conseguiu abastecer na ultima rodada (o que gravar/produzir)."""
    p = APREND.with_name("rede_sem_video.json")
    if not p.exists():
        return ""
    d = json.loads(p.read_text(encoding="utf-8"))
    if not d.get("canais"):
        return ""
    li = "".join(f"<li><b>{e(s)}</b> ({e(', '.join(v['dias']))}): grave/produza sobre <i>{e(v['nicho'])}</i></li>"
                 for s, v in sorted(d["canais"].items()))
    return f"<h3>Falta video bom para (rodada de {e(d.get('em', '')[:16].replace('T', ' '))})</h3><ul>{li}</ul>"


def bloco_estrategias(apr):
    """Tabela do que cada canal esta aprendendo (media da nota por braco, com nº de amostras)."""
    linhas = []
    for slug, dims in sorted((apr.get("canais") or {}).items()):
        partes = []
        for dim, bracos in dims.items():
            melhor = sorted(bracos.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))
            partes.append(f"<b>{e(dim)}</b>: " + ", ".join(f"{e(b)} {sum(v) / len(v):.2f} ({len(v)})" for b, v in melhor[:3]))
        linhas.append(f"<tr><td>{e(slug)}</td><td>{' | '.join(partes)}</td></tr>")
    if not linhas:
        return ("<h3>Estrategias em teste</h3><p><small>Ainda sem medicoes: cada video da rede e medido 40-60 h depois de "
                "abrir. Os primeiros resultados aparecem 2 dias depois das primeiras postagens.</small></p>")
    return ("<h3>Estrategias em teste (nota media: 1,00 = mediana do canal; amostras entre parenteses)</h3>"
            f"<table><tr><th>Canal</th><th>Melhores bracos por dimensao</th></tr>{''.join(linhas)}</table>")


def e(x):
    return html.escape(str(x or ""))


def render(dados, erros, apr=None):
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    hist = {}
    if HIST.exists():
        for ln in HIST.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
                hist.setdefault(r["slug"], []).append(r)
            except Exception:  # noqa: BLE001
                pass
    tot = {k: sum(c[k] for c in dados) for k in ("inscritos", "views", "videos")}
    linhas, blocos = [], []
    for c in sorted(dados, key=lambda c: -c["inscritos"]):
        h = hist.get(c["slug"], [])
        ant = next((x for x in h if x["ts"][:10] < datetime.now().strftime("%Y-%m-%d")), None)
        d_ins = c["inscritos"] - ant["inscritos"] if ant else 0
        d_vw = c["views"] - ant["views"] if ant else 0
        pub = [v for v in c["uploads"] if v["privacy"] == "public"]
        lk = sum(v["likes"] for v in pub)
        cm = sum(v["coments"] for v in pub)
        agend = [v for v in c["uploads"] if v.get("publishAt")]
        linhas.append(f"<tr><td><a href='https://youtube.com/channel/{e(c['yt_id'])}' target=_blank>{e(c['nome'])}</a>"
                      f"<br><small>{e(c['handle'])}</small></td><td class=n>{c['inscritos']}<small> {d_ins:+d}</small></td>"
                      f"<td class=n>{c['views']}<small> {d_vw:+d}</small></td><td class=n>{c['videos']}</td>"
                      f"<td class=n>{lk}</td><td class=n>{cm}</td><td class=n>{len(agend)}</td>"
                      f"<td class=n>{len(c['comentarios'])}</td></tr>")
        mx = max([v["views"] for v in c["uploads"]] + [1])
        vrows = "".join(
            f"<tr class='{e(v['privacy'])}'><td><a href='https://youtu.be/{v['id']}' target=_blank>{e(v['titulo'][:80])}</a></td>"
            f"<td>{e((v.get('publishAt') or v['pub'])[:16].replace('T', ' '))}</td><td>{e(v['privacy'])}</td>"
            f"<td class=n><span class=bar style='width:{int(80 * v['views'] / mx)}px'></span>{v['views']}</td>"
            f"<td class=n>{v['likes']}</td><td class=n>{v['coments']}</td></tr>" for v in c["uploads"][:15])
        crows = "".join(f"<li><b>{e(x['autor'])}</b> <a href='https://youtu.be/{e(x['video'])}' target=_blank>(video)</a>: "
                        f"{e(x['texto'])} <small>{e(x['quando'][:16].replace('T', ' '))}"
                        f"{' - ja respondido' if x['respostas'] else ' - RESPONDER'}</small></li>" for x in c["comentarios"])
        blocos.append(f"<details><summary>{e(c['nome'])} - {c['inscritos']} inscritos, {len(c['comentarios'])} comentarios recentes"
                      f"</summary><table><tr><th>Video</th><th>Abre/abriu</th><th>Status</th><th>Views</th><th>Likes</th>"
                      f"<th>Coment.</th></tr>{vrows}</table><h4>Comentarios do publico</h4><ul>{crows or '<li>nenhum</li>'}</ul></details>")
    err = "".join(f"<li>{e(k)}: {e(v)}</li>" for k, v in erros.items())
    return f"""<!doctype html><html lang=pt-br><meta charset=utf-8><title>Painel da rede</title>
<style>body{{font-family:Segoe UI,Arial;margin:24px;background:#fafafa;color:#222}}table{{border-collapse:collapse;margin:8px 0}}
td,th{{padding:5px 9px;border-bottom:1px solid #ddd;text-align:left;font-size:14px}}.n{{text-align:right}}small{{color:#888}}
.kpi{{display:inline-block;margin:0 24px 12px 0}}.kpi b{{font-size:28px;display:block}}tr.private td{{color:#999}}
.bar{{display:inline-block;height:9px;background:#3b82f6;margin-right:6px;vertical-align:middle}}details{{margin:8px 0}}
summary{{cursor:pointer;font-weight:600}}</style>
<h1>Painel da rede de canais</h1><p><small>atualizado {ts} - roda sozinho (tarefa PainelCanais)</small></p>
<div class=kpi><b>{tot['inscritos']}</b>inscritos</div><div class=kpi><b>{tot['views']}</b>views</div>
<div class=kpi><b>{tot['videos']}</b>videos</div><div class=kpi><b>{len(dados)}</b>canais ativos</div>
<table><tr><th>Canal</th><th>Inscritos (vs ontem)</th><th>Views (vs ontem)</th><th>Videos</th><th>Likes (30 ult.)</th>
<th>Coment. (30 ult.)</th><th>Agendados</th><th>Coment. p/ ver</th></tr>{''.join(linhas)}</table>
{bloco_falta()}{bloco_estrategias(apr or {})}{''.join(blocos)}{'<h3>Erros na coleta</h3><ul>' + err + '</ul>' if err else ''}</html>"""


def main():
    creds = {c["id"]: c for c in politica.carregar_creds()}
    dados, erros = [], {}
    for canal in politica.rede().get("canais", []):
        # 09/11 (dona: "o painel não sai de 18 mil de views"): só os 'ativo' (12 de 23) eram medidos — hipercool,
        # parceiro e comentarios postam e ficavam fora da soma. Agora mede todo canal com credencial, menos
        # suspenso/pausado. Voltar ao antigo: PAINEL_SO_ATIVOS=1
        import os as _os
        if _os.environ.get("PAINEL_SO_ATIVOS") == "1":
            if canal.get("status") != "ativo":
                continue
        elif canal.get("status") in ("suspenso", "pausado"):
            continue
        cred = next((creds[i] for i in canal.get("creds", []) if i in creds), None)
        try:
            dados.append(coletar(canal, cred))
        except urllib.error.HTTPError as ex:
            erros[canal["nome"]] = f"{ex.code} {ex.read()[:150]!r}"
        except Exception as ex:  # noqa: BLE001
            erros[canal["nome"]] = str(ex)[:150]
    OUT.mkdir(exist_ok=True)
    ts = datetime.now().isoformat(timespec="minutes")
    with open(HIST, "a", encoding="utf-8") as f:
        for c in dados:
            f.write(json.dumps({"ts": ts, "slug": c["slug"], "inscritos": c["inscritos"], "views": c["views"],
                                "videos": c["videos"]}) + "\n")
    # 10/11 (dona: "o painel parou em 52 mil desde a tarde"): o total do canal (statistics.viewCount) o YouTube só
    # atualiza 1-2x/dia; as views de CADA vídeo atualizam em minutos. Grava as views por vídeo (30 recentes de cada
    # canal) em historico_videos.jsonl — o painel soma o ganho de cada vídeo entre medições (vídeo novo entra do zero).
    with open(OUT / "historico_videos.jsonl", "a", encoding="utf-8") as f:
        for c in dados:
            f.write(json.dumps({"ts": ts, "slug": c["slug"],
                                "v": {u["id"]: u["views"] for u in c["uploads"]}}) + "\n")
    apr, novos = aprender(dados)
    (OUT / "index.html").write_text(render(dados, erros, apr), encoding="utf-8")
    print(f"painel: {len(dados)} canais, {len(erros)} erro(s), {novos} video(s) medido(s) p/ aprendizado -> {OUT / 'index.html'}")
    if "--abrir" in sys.argv:
        webbrowser.open(str(OUT / "index.html"))


if __name__ == "__main__":
    main()
