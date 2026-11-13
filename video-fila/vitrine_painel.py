"""vitrine_painel.py — dados do PAINEL dos telões (dono, 22/10/2026: "a tela não fica ociosa; cada um exibe uma coisa
diferente e fica rodando: vídeos saindo, os horários em letra GRANDE, dados, o que chega no Telegram, mil views com botão
pra abrir o vídeo, quando volta o limite do Opus, bloqueios do Studio, o Flow").

Monta um JSON pequeno (painel.json) a partir do que os projetos já gravam — nada aqui posta nem muda nada — e o
vitrine.py manda pros notebooks a cada passada. Lá o player.py mostra ~/vitrine/painel.html (gira os quadros).
Também atende os botões do telão: "abrir vídeo" e "ver" (vídeo esperando aprovação) chegam em ~/vitrine/pedidos.txt.

    python vitrine_painel.py            # mostra o JSON que iria pros telões
"""
import json
import re
import shutil
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
AVISOS = BASE / "estado" / "avisos.jsonl"
LIMITE = Path(r"D:\postador-de-videos\config\limite_diario.json")
CHECAGEM = Path(r"D:\postador-de-videos\logs\checagem_direitos.jsonl")
HIPER_ESTADO = Path(r"D:\hipercool-videos\workspace\fila_estado.json")
HIPER_VIDEOS = Path(r"D:\hipercool-videos\workspace\videos")
ANIMES = Path(r"D:\hipercool-materiais\animes recap")
PENDENTES_CACHE = BASE / "estado" / "vitrine_pendentes.json"
FUSO = timezone(timedelta(hours=-3))
# cada telão gira os SEUS quadros (dono: "cada um pode exibir uma coisa diferente")
# 12/11 dona: saiu o quadro do Telegram; entraram "Vídeos do dia" (feitos e postados em todas as redes) e
# "Acima do normal" (canais com views e/ou inscritos acima da média, o mesmo do painel :8790)
# 12/11 dona (2ª): telão = STI e PC2. Próximos/saindo só longos; ranking do dia + ranking de todos os tempos (saem os de
# 5 mil e 1.200); no lugar de "novos inscritos", só os canais acima do normal no dia (views e inscritos)
_QUADROS = ["producao", "acima", "rankdia", "maisvistos", "proximos", "saindo", "pendentes", "bloqueios", "opus"]
TELAS = {"sti": _QUADROS, "pc2": _QUADROS, "desktop": _QUADROS,
         "acer": ["saindo", "proximos", "acima", "rankdia", "maisvistos", "pendentes", "producao"],
         "x200ma": ["producao", "acima", "rankdia", "maisvistos", "bloqueios", "opus", "proximos"]}
PAINEL = "http://localhost:8790/api/"
SHORTS_DIR = Path(r"D:\hipercool-materiais\animes recap\shorts")
POSTED_TT = Path(r"D:\postador-de-videos\logs\tiktok_auto_posted.json")
POSTED_IG = Path(r"D:\postador-de-videos\logs\instagram_auto_posted.json")
LONGO = ("completo", "longo", "compilado")
NOMES_PROJ = {"parceiro": "Recap parceiros", "rede": "Rede react", "hipercool": "Hipercool", "veo": "Veo",
              "historias": "Histórias", "anime": "Anime"}


def _dt(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=FUSO)
    except (ValueError, TypeError):
        return None


def _jsonl(caminho, ultimas=4000):
    try:
        linhas = caminho.read_text(encoding="utf-8", errors="replace").splitlines()[-ultimas:]
    except OSError:
        return []
    out = []
    for l in linhas:
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out


def _url(r):
    longo = (r.get("tipo") or "") in ("completo", "longo", "compilado")
    vid = r.get("video_id")
    return f"https://www.youtube.com/watch?v={vid}" if longo else f"https://www.youtube.com/shorts/{vid}"


def _hora(d, agora):
    loc = d.astimezone(FUSO)
    hoje = agora.astimezone(FUSO).date()
    if loc.date() == hoje:
        return loc.strftime("%H:%M")
    if loc.date() == hoje + timedelta(days=1):
        return "amanhã " + loc.strftime("%H:%M")
    return loc.strftime("%d/%m %H:%M")


def videos(agora):
    """Próximos a abrir (horário grande), os que abriram nas últimas 24 h e a contagem do dia por projeto."""
    vistos, prox, saidos = set(), [], []  # sem corte em 10: o montar() filtra os longos depois
    hoje = agora.astimezone(FUSO).date()
    por_proj, futuros = Counter(), Counter()
    for r in reversed(_jsonl(LEDGER)):
        vid = r.get("video_id")
        if not vid or vid in vistos:
            continue
        vistos.add(vid)
        abre = _dt(r.get("publish_at") or r.get("ts"))
        if not abre:
            continue
        proj = NOMES_PROJ.get(r.get("projeto") or "", r.get("projeto") or "?")
        item = {"hora": _hora(abre, agora), "canal": r.get("canal") or "?", "projeto": proj,
                "tipo": r.get("tipo") or "short", "url": _url(r), "t": abre.timestamp()}
        if abre.astimezone(FUSO).date() == hoje:
            por_proj[proj] += 1
        if abre > agora:
            prox.append(item)
            futuros[proj] += 1
        elif agora - abre < timedelta(hours=24):
            saidos.append(item)
    prox.sort(key=lambda x: x["t"])
    saidos.sort(key=lambda x: -x["t"])
    return {"proximos": prox, "saidos": saidos, "hoje": dict(por_proj.most_common()),
            "agendados": dict(futuros.most_common())}


def telegram(agora):
    """O que chegou no Telegram (o portão único grava tudo), sem os repetidos."""
    msgs, opus, flow, inscritos = [], None, [], []
    volta_conhecida = None
    for a in _jsonl(AVISOS, 3000):
        em = _dt(a.get("em"))
        if not em:
            continue
        if a.get("origem") == "opus-monitor":
            opus = a
            v = re.search(r"[Vv]olta ([^.\n/]+?\d{1,2}:\d{2})", a.get("texto") or "")
            if v:
                volta_conhecida = (v.group(1).strip(), em)
            elif re.search(r"FUNCIONANDO", a.get("texto") or ""):
                volta_conhecida = None
        if a.get("origem") == "inscritos" and agora - em < timedelta(hours=48):
            t = a.get("texto") or ""
            canal = re.search(r"Canal:\s*(.+)", t)
            total = re.search(r"Total agora:\s*([\d.]+)", t)
            ganhou = re.search(r"Ganhou:\s*\+?(\d+)", t)
            inscritos.append({"id": f"i:{a.get('em')}:{canal.group(1).strip() if canal else ''}", "tipo": "inscrito",
                              "canal": canal.group(1).strip() if canal else "?",
                              "ganhou": int(ganhou.group(1)) if ganhou else 1, "total": total.group(1) if total else None,
                              "em": em.astimezone(FUSO).strftime("%d/%m %H:%M"), "t": em.timestamp()})
        if re.search(r"flow|veo|forja", a.get("origem") or "", re.I):
            flow.append({"em": em.astimezone(FUSO).strftime("%d/%m %H:%M"), "texto": (a.get("texto") or "")[:240]})
        if a.get("situacao") == "repetido" or agora - em > timedelta(hours=24):
            continue
        msgs.append({"em": em.astimezone(FUSO).strftime("%H:%M"), "origem": a.get("origem") or "",
                     "texto": (a.get("texto") or "")[:260], "importante": bool(a.get("importante"))})
    op = None
    if opus:
        t = opus.get("texto") or ""
        op = {"ok": bool(re.search(r"FUNCIONANDO|voltou|com crédito e respondendo", t)),
              "volta": (f"{volta_conhecida[0]} (aviso de {volta_conhecida[1].astimezone(FUSO):%d/%m %H:%M})"
                        if volta_conhecida else None),
              "texto": t[:260], "em": _dt(opus["em"]).astimezone(FUSO).strftime("%d/%m %H:%M")}
    return {"opus": op, "flow": flow[-6:][::-1], "inscritos": inscritos[-12:][::-1]}


def _api(caminho):
    import urllib.request
    with urllib.request.urlopen(PAINEL + caminho, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def acima_normal():
    """Canais acima do normal hoje (ritmo = ganho de hoje / média diária do canal; >= 2 = acima), igual ao gráfico
    "Melhores canais" do painel :8790. Painel fora = None (o quadro avisa)."""
    try:
        r = _api("ranking_canais")
    except Exception:  # noqa: BLE001
        return None
    out = []
    for c in r.get("canais") or []:
        rv, ri = c.get("ritmo_views") or 0, c.get("ritmo_insc") or 0
        if rv >= 2 or ri >= 2:
            out.append({"canal": c.get("canal"), "views_hoje": c.get("views_hoje") or 0, "insc_hoje": c.get("insc_hoje") or 0,
                        "rv": round(rv, 1), "ri": round(ri, 1), "media_views": c.get("media_views_dia") or 0,
                        "media_insc": c.get("media_insc_dia") or 0, "views_acima": rv >= 2, "insc_acima": ri >= 2})
    out.sort(key=lambda x: (-(x["views_acima"] and x["insc_acima"]), -x["views_hoje"]))
    return {"canais": out, "em": (r.get("em") or "")[11:16]}


def _hoje_ts(lista, hoje):
    try:
        return [x for x in json.loads(lista.read_text(encoding="utf-8")) if str(x.get("timestamp") or "")[:10] == hoje]
    except (OSError, ValueError):
        return []


def producao_dia(agora):
    """Vídeos do dia: feitos (Shorts = pastas do dia de todas as máquinas, mesma conta do painel; longos = subidos hoje)
    e postados em cada rede (YouTube pelo uploads_ledger; TikTok e Insta pelos registros de post automático)."""
    loc = agora.astimezone(FUSO)
    hoje, ymd = loc.date().isoformat(), loc.strftime("%Y%m%d")
    try:
        shorts_feitos = sum(1 for _ in SHORTS_DIR.glob(f"*_{ymd}*/postar.json"))
    except OSError:
        shorts_feitos = None
    yt = {"short": 0, "longo": 0, "veo": 0}
    yt_sub = {"short": 0, "longo": 0, "veo": 0}
    vistos = set()
    for r in reversed(_jsonl(LEDGER, 6000)):
        vid = r.get("video_id")
        if not vid or vid in vistos:
            continue
        vistos.add(vid)
        t = r.get("tipo") or "short"
        k = "longo" if t in LONGO else "veo" if t == "veo" else "short"
        sub = _dt(r.get("ts"))
        if sub and sub.astimezone(FUSO).date().isoformat() == hoje:
            yt_sub[k] += 1
        abre = _dt(r.get("publish_at") or r.get("ts"))
        if abre and abre <= agora and abre.astimezone(FUSO).date().isoformat() == hoje:
            yt[k] += 1
    tt, ig = _hoje_ts(POSTED_TT, hoje), _hoje_ts(POSTED_IG, hoje)
    por_tipo = lambda L: dict(Counter(("veo" if x.get("tipo") == "veo" else "short") for x in L))  # noqa: E731
    return {"shorts_feitos": shorts_feitos, "longos_feitos": yt_sub["longo"], "youtube_no_ar": yt,
            "youtube_subidos": yt_sub, "tiktok": len(tt), "tiktok_tipo": por_tipo(tt), "instagram": len(ig),
            "instagram_tipo": por_tipo(ig), "total_postado": sum(yt.values()) + len(tt) + len(ig)}


def bloqueios(agora):
    lim = []
    try:
        dados = json.loads(LIMITE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dados = {}
    for canal, d in dados.items():
        ate = _dt((d or {}).get("ate") if isinstance(d, dict) else None)
        if ate and ate > agora:
            lim.append({"canal": canal.replace("novo_", ""), "ate": _hora(ate, agora)})
    chec = []
    for c in _jsonl(CHECAGEM, 300)[-40:]:
        rod = str(c.get("rodape") or "")
        if re.search(r"direitos autorais|copyright|bloque|restri", rod, re.I):
            chec.append({"video": c.get("video"), "texto": rod[:140], "em": str(c.get("ts") or "")[5:16]})
    return {"limite": lim, "checagem": chec[-6:][::-1]}


def pendentes(forcar=False):
    """Vídeos que esperam a dona (hipercool em "revisar", anime segurado/reprovado). Varrer as pastas é lento: cache 10 min."""
    try:
        c = json.loads(PENDENTES_CACHE.read_text(encoding="utf-8"))
        if not forcar and time.time() - c.get("t", 0) < 600:
            return c["itens"]
    except (OSError, ValueError, KeyError):
        pass
    itens = []
    try:
        est = json.loads(HIPER_ESTADO.read_text(encoding="utf-8"))
        for chave, e in est.items():
            if isinstance(e, dict) and e.get("situacao") == "revisar" and e.get("video"):
                cam = HIPER_VIDEOS / e["video"]
                if cam.exists():
                    itens.append({"id": f"h:{chave}", "nome": chave, "projeto": "Hipercool",
                                  "motivo": "análise achou nudez", "caminho": str(cam)})
    except (OSError, ValueError):
        pass
    for pj in ANIMES.rglob("postar.json"):
        try:
            d = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rev = str(d.get("revisao") or "")
        if d.get("posted_url") or d.get("revisao_de") or rev in ("", "None", "ok", "ok_manual"):
            continue
        if re.search(r"dispensad|dono \d", rev, re.I):  # já decidido pela dona (descartado/reprovado por ela)
            continue
        mp4 = next(iter(sorted(pj.parent.glob("*.mp4"))), None)
        if mp4:
            itens.append({"id": f"a:{pj.parent.name}", "nome": pj.parent.name, "projeto": "Anime/recap",
                          "motivo": rev[:80], "caminho": str(mp4)})
    PENDENTES_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PENDENTES_CACHE.write_text(json.dumps({"t": time.time(), "itens": itens}, ensure_ascii=False), encoding="utf-8")
    return itens


def maquina():
    livre = {}
    for d in ("C:\\", "D:\\"):
        try:
            livre[d[0]] = round(shutil.disk_usage(d).free / 1e9, 1)
        except OSError:
            pass
    ram = None
    try:
        import ctypes

        class M(ctypes.Structure):
            _fields_ = [("l", ctypes.c_ulong), ("c", ctypes.c_ulong), ("t", ctypes.c_ulonglong),
                        ("a", ctypes.c_ulonglong), ("x", ctypes.c_ulonglong * 5)]
        m = M()
        m.l = ctypes.sizeof(M)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        ram = round(m.a / 1e9, 1)
    except Exception:  # noqa: BLE001
        pass
    return {"disco_livre_gb": livre, "ram_livre_gb": ram}


MAIS_VISTOS_CACHE = BASE / "estado" / "vitrine_maisvistos.json"
MARCOS_TELAO = BASE / "estado" / "vitrine_marcos.json"  # {"<marco>:<video_id>": quando o telão viu passar}
RANKING_MIN = 1200  # 01/11 dona: "faça um ranking real de vídeos acima de 1200"
MARCO_MIN = 5000    # quadro "5 mil visualizações"
DEGRAUS = (5000, 10000, 25000, 50000, 100000)  # mesma escada do notificar_telegram (MARCOS)


def mais_vistos():
    """Ranking dos vídeos com RANKING_MIN+ views, do maior pro menor, de TODOS os canais (videos_canais: lista de
    uploads de cada canal pela API do YouTube, views ao vivo, cache 1 h). Também a fonte do quadro de 5 mil.
    01/11 dona ("o de 5 mil e o de mil mostram vídeo com menos de mil e 1.200, e tem mais vídeos com mais do que isso"):
    o quadro de 5 mil lia marcos_views.jsonl — 7 linhas congeladas no dia do aviso (5 de 1.0xx views de 23/10) e só dos
    canais que o notificar_telegram olha (sem os Noturnos: 4 dos 6 vídeos de 5 mil+ nunca entraram). Agora tudo daqui.
    Sem janela de 30 dias (deixava 14 vídeos de 1.200+ de fora). Cache 15 min."""
    try:
        c = json.loads(MAIS_VISTOS_CACHE.read_text(encoding="utf-8"))
        if time.time() - c.get("t", 0) < 900 and "lido" in c:
            return c
    except (OSError, ValueError, KeyError):
        c = None
    try:
        import videos_canais
        d = videos_canais.dados()
        itens, vistos = [], set()
        for v in sorted(d.get("videos", []), key=lambda v: -(v.get("views") or 0)):
            if (v.get("views") or 0) < RANKING_MIN:
                break
            if v["id"] in vistos:  # mesmo vídeo lido por 2 cadastros do canal
                continue
            vistos.add(v["id"])
            pub = videos_canais.pub_local(v)
            itens.append({"id": v["id"], "titulo": v.get("titulo") or "", "canal": v.get("canal") or "",
                          "views": v["views"], "em": pub.strftime("%d/%m/%y") if pub else "",
                          "url": f"https://www.youtube.com/shorts/{v['id']}"})
        if not itens:
            raise ValueError("lista vazia")  # coleta falhou: não apaga o ranking bom
        c = {"t": time.time(), "lido": (d.get("lido") or "")[-5:], "itens": itens}
        MAIS_VISTOS_CACHE.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
        return c
    except Exception:  # noqa: BLE001 — API fora: mostra a última lista
        return c if c and "lido" in c else {"lido": "", "itens": []}


BASE_DIA = BASE / "estado" / "vitrine_views_base_dia.json"  # {"dia": "AAAA-MM-DD", "em": hh:mm, "views": {id: views}}


def ranking_dia(agora):
    """12/11 dona: "ranking só os melhores do dia". A API do YouTube só dá o total de cada vídeo; guarda a 1ª leitura
    do dia como base e o ganho de hoje = views agora - base. Vídeo publicado hoje (sem base) ganha tudo o que tem."""
    try:
        import videos_canais
        d = videos_canais.dados()
    except Exception:  # noqa: BLE001
        return {"desde": "", "itens": []}
    vs = d.get("videos") or []
    hoje = agora.astimezone(FUSO).date().isoformat()
    try:
        base = json.loads(BASE_DIA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        base = {}
    if base.get("dia") != hoje and vs:
        base = {"dia": hoje, "em": (d.get("lido") or "")[11:16], "views": {v["id"]: v.get("views") or 0 for v in vs}}
        BASE_DIA.write_text(json.dumps(base), encoding="utf-8")
    bv, itens, vistos = base.get("views") or {}, [], set()
    for v in vs:
        if v["id"] in vistos:
            continue
        vistos.add(v["id"])
        pub = videos_canais.pub_local(v)
        ganho = (v.get("views") or 0) - bv[v["id"]] if v["id"] in bv else (
            (v.get("views") or 0) if pub and pub.date().isoformat() == hoje else 0)
        if ganho > 0:
            itens.append({"id": v["id"], "titulo": v.get("titulo") or "", "canal": v.get("canal") or "",
                          "views": ganho, "total": v.get("views") or 0, "em": pub.strftime("%d/%m/%y") if pub else "",
                          "url": f"https://www.youtube.com/shorts/{v['id']}"})
    itens.sort(key=lambda x: -x["views"])
    return {"desde": base.get("em") or "", "itens": itens[:30]}


def marcos_telao(itens):
    """Pop-up de conquista: cada vídeo que passa de um degrau (5 mil, 10 mil...) vira evento UMA vez, com a hora em que
    o telão viu. Na 1ª vez, o que já tinha passado fica anotado com t=0 (não vira pop-up atrasado)."""
    try:
        est = json.loads(MARCOS_TELAO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        est = None
    semear, est, agora = est is None, est or {}, time.time()
    eventos = []
    for v in itens:
        for m in DEGRAUS:
            if v["views"] < m:
                break
            chave = f"{m}:{v['id']}"
            if chave not in est:
                est[chave] = 0 if semear else agora
            # id "m:<video>" no 1º degrau = o mesmo dos pop-ups antigos (o navegador já marcou como visto)
            eventos.append(dict(v, id=f"m:{v['id']}" if m == DEGRAUS[0] else f"m{m}:{v['id']}", marco=m, t=est[chave]))
    MARCOS_TELAO.write_text(json.dumps(est), encoding="utf-8")
    return eventos


def montar():
    agora = datetime.now(timezone.utc)
    mv = mais_vistos()
    p = {"gerado_em": agora.isoformat(timespec="seconds"), "telas": TELAS, **videos(agora), **telegram(agora),
         "maisvistos": mv["itens"], "milviews": [v for v in mv["itens"] if v["views"] >= MARCO_MIN],
         "views_lido": mv["lido"], "ranking_min": RANKING_MIN, "bloqueios": bloqueios(agora), "pc1": maquina(),
         "acima": acima_normal(), "producao": producao_dia(agora), "rank_dia": ranking_dia(agora)}
    # 12/11 dona: próximos e saídos só os LONGOS (os Shorts são centenas por dia e escondiam os longos)
    p["proximos"] = [x for x in p["proximos"] if x["tipo"] in LONGO]
    p["saidos"] = [x for x in p["saidos"] if x["tipo"] in LONGO]
    # pop-up na tela (dono 22/10: "inscritos e mil views aparecem na tela como pop-up, além do histórico")
    p["eventos"] = sorted([dict(e, tipo="mil") for e in marcos_telao(p["milviews"])] + p["inscritos"],
                          key=lambda e: -e.get("t", 0))[:15]
    p["pendentes"] = [{k: v for k, v in i.items() if k != "caminho"} for i in pendentes()]
    # máquinas fora há 6+ min (vitrine\vigia_mutuo.py no PC1): alerta vermelho de tela cheia no telão (dona 23/10)
    try:
        vm = json.loads((Path(r"D:\video-fila\estado") / "vigia_mutuo.json").read_text(encoding="utf-8"))
        p["fora"] = (vm.get("fora") or {}) if time.time() - float(vm.get("em") or 0) < 15 * 60 else {}
    except (OSError, ValueError):
        p["fora"] = {}
    # 29/10 (dona): conta do like/comentário deslogada no telão = alerta de tela cheia no próprio telão (vitrine._avisar_deslogado)
    try:
        p["deslogado"] = json.loads((Path(r"D:\video-fila\estado") / "telao_deslogado.json").read_text(encoding="utf-8"))
        from datetime import datetime as _dt  # 06/11: sinal sem 401 novo há 6 h = vencido (ficou 5 dias no telão)
        if (_dt.now() - _dt.fromisoformat(p["deslogado"].get("em") or "2000-01-01")).total_seconds() > 6 * 3600:
            p["deslogado"] = None
    except (OSError, ValueError):
        p["deslogado"] = None
    return p


def caminho_pendente(ident):
    for i in pendentes():
        if i["id"] == ident:
            return i["caminho"]
    return None


if __name__ == "__main__":
    import sys
    if sys.stdout:  # pythonw (tarefa agendada) não tem stdout
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(montar(), ensure_ascii=False, indent=1)[:6000])
