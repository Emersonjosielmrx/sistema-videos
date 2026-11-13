# -*- coding: utf-8 -*-
"""painel_controlador.py — painel web local dos projetos de vídeo (http://localhost:8790; a 8787 é do atlas).

    python painel_controlador.py [--port 8790]

Lê o estado do controlador, a fila de render, o ledger de uploads, o catálogo (todas as redes), as métricas do Studio,
o histórico dos canais, o estado do hipercool e os logs de produção de cada projeto. A única escrita é o liga/desliga
(POST /api/controle -> controle.mudar), que só aceita pedido feito pelo próprio painel (cabeçalho X-Painel).
"""
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import urlencode, urlparse, parse_qs

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.path.insert(0, r"D:\postador-de-videos\bin")
PORT = 8790

HIPER_ESTADO = Path(r"D:\hipercool-videos\workspace\fila_estado.json")
HIPER_CFG = Path(r"D:\hipercool-videos\config\fila.json")
HIPER_LOGS = Path(r"D:\hipercool-videos\logs")
PANELS = Path(r"D:\hipercool-materiais\panels")
LEDGER = Path(r"D:\postador-de-videos\logs\uploads_ledger.jsonl")
CATALOGO = Path(r"D:\postador-de-videos\config\catalogo_videos.json")
HISTORICO = Path(r"D:\postador-de-videos\painel\historico.jsonl")
APRENDIZADO = Path(r"D:\postador-de-videos\_analise\aprendizado_global.json")
METRICAS = Path(r"D:\postador-de-videos\_analise\metricas_studio.json")
RECAPD = Path(r"D:\recapd-ambientes\producao")
WS_ANIME = RECAPD / "workspace" / "anime"
MSE = Path(r"D:\ms-energy")
VEO_LOG = Path(r"D:\veo\beta\logs\cron_gerar_llm.log")
MR_LOGS = Path(r"D:\manhwa-react\logs")
POST_LOGS = Path(r"D:\postador-de-videos\logs")

# projetos do painel: id -> nome, projetos do controle.py, marcas na linha de comando, nome no catálogo, logs
PROJETOS = {
    "cortes": {"nome": "Cortes", "sub": "Shorts de parceiros (todos os nichos) + anime longo", "controle": ["parceiro", "anime"],
               "marcas": ["parceiro_diario.py producao", "anime_auto.py", "anime-pipeline.py"], "catalogo": ["parceiro"]},
    "hipercool": {"nome": "Hipercool", "sub": "capítulos do The Inheritor (pt no PC1, línguas no PC2)", "controle": ["hipercool"],
                  "marcas": ["fila.py ciclo", "fila.py faltantes", "fila.py pc2", "hiper-pipeline", "hiper-longo"],
                  "catalogo": ["hipercool"]},
    "msenergy": {"nome": "MS Energy", "sub": "produto real: 2 vídeos/dia no Flow, Insta e TikTok", "controle": ["msenergy"],
                 "marcas": ["gerar_short_veo.py", "cron_gerar_ms_energy"], "catalogo": ["ms-energy"]},
    "veo": {"nome": "Veo", "sub": "limpa os brutos do Drive e gera novo só com o Drive vazio", "controle": ["veo"],
            "marcas": ["cron_gerar_video_llm.py", "limpar_veo.py", "gera_auto.py", "sonda_contas_veo.py"],
            "catalogo": ["veo"]},
    "manhwa-react": {"nome": "ManhwaReact", "sub": "lote das gravações (02:00) e rede de canais", "controle": ["manhwa-react"],
                     "marcas": ["manhwareact.py", "mr.batch", "story_pipeline"], "catalogo": ["manhwa-react"]},
    # 10/11 (dona: "histórias em frames foi absorvido pelo Claude Video; mostrar o que o projeto é hoje e a versão
    # nova pro Insta que funciona de fato"): a chave segue "historias" (liga/desliga e catálogo usam), o card é o
    # do Claude Video (D:\claude-code-video, tarefa ClaudeCodeVideo): Reels em Remotion das solares no Instagram.
    "historias": {"nome": "Claude Video", "sub": "Reels em Remotion das solares (MS, Advance, Globo) no Instagram — absorveu o Histórias em Frames",
                  "controle": ["historias"], "marcas": ["claude-code-video", "gerar.py --auto", "historias-em-frames"],
                  "catalogo": ["historias-em-frames"]},
    "postador": {"nome": "Postador", "sub": "sobe nos canais: YouTube (navegador), TikTok, Instagram", "controle": ["postador"],
                 "marcas": ["youtube_web_poster.py", "parceiro_diario.py postar", "postar_tudo", "tiktok", "instagram_auto",
                            "postar_auto"], "catalogo": []},
}


def _ler(p, padrao=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {} if padrao is None else padrao


def _ler_jsonl(p):
    out = []
    try:
        linhas = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for linha in linhas:
        try:
            out.append(json.loads(linha))
        except ValueError:
            continue
    return out


def _cauda(p, n=25, filtro=None):
    """Últimas n linhas úteis de um log (sem as repetidas de proxy/aviso de ssh)."""
    try:
        with open(p, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 200_000))
            linhas = f.read().decode("utf-8", "replace").splitlines()[1:]
    except OSError:
        return []
    ruido = re.compile(r"Proxy falhou|\[rotaciona\]|post-quantum|store now, decrypt|openssh\.com/pq|^\s*$")
    linhas = [l[:300] for l in linhas if not ruido.search(l) and (not filtro or re.search(filtro, l))]
    return linhas[-n:]


def _periodo(params, dias_padrao=7):
    """(de, até) em AAAA-MM-DD: ?de=&ate= ou ?dias=N (N dias até hoje)."""
    de, ate = params.get("de", [""])[0], params.get("ate", [""])[0]
    if not de:
        dias = max(1, int(params.get("dias", [str(dias_padrao)])[0]))
        de = (date.today() - timedelta(days=dias - 1)).isoformat()
    return de, ate or date.today().isoformat()


_CACHE = {}
_TRAVAS = {}


def _cache(chave, segundos, fn):
    """A tela nunca espera (21/10: /api/canais levava 58 s e /api/producao 12 s): valor vencido volta na hora e é
    recalculado em segundo plano, uma consulta por vez por chave; só a 1ª consulta depois de ligar o painel espera."""
    v = _CACHE.get(chave)
    if v and time.time() - v[0] <= segundos:
        return v[1]
    trava = _TRAVAS.setdefault(chave, threading.Lock())
    if v:
        if trava.acquire(blocking=False):
            threading.Thread(target=_recalcular, args=(chave, fn, trava), daemon=True).start()
        return v[1]
    with trava:
        v = _CACHE.get(chave)
        if not v:
            v = (time.time(), fn())
            _CACHE[chave] = v
        return v[1]


def _recalcular(chave, fn, trava):
    try:
        _CACHE[chave] = (time.time(), fn())
    except Exception as e:  # noqa: BLE001
        # 27/10: o erro era engolido e a tela ficava com o valor velho sem ninguém saber — agora fica anotado
        try:
            with open(BASE / "logs" / "painel_erros.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%d/%m %H:%M:%S}] recalcular {chave}: {type(e).__name__}: {str(e)[:300]}\n")
        except OSError:
            pass
    finally:
        trava.release()


def _pronto(chave):
    """O último valor calculado (sem disparar cálculo): pros problemas não esperarem as consultas lentas."""
    v = _CACHE.get(chave)
    return v[1] if v else None


_ULTIMO_ACESSO = [0.0]


def _aquecer():
    """Mantém as consultas lentas prontas enquanto alguém usa o painel (até 15 min depois do último acesso; parado
    não gasta CPU do PC1, que é o render)."""
    primeira = True
    while True:
        _gravar_disco()  # o histórico do disco vale mesmo sem ninguém olhando (ele mesmo grava só a cada 10 min)
        if primeira or time.time() - _ULTIMO_ACESSO[0] < 15 * 60:
            for chave, seg, fn in AQUECER:
                try:
                    _cache(chave, seg, fn)
                except Exception:  # noqa: BLE001
                    pass
            primeira = False
        time.sleep(15)


def _lista_processos():
    """{pid: (minutos, linha de comando)} do PC1, sem escrever no log do controlador; {} se a consulta falhar."""
    import subprocess
    ps = ("Get-CimInstance Win32_Process -Filter \"Name like 'python%' or Name='wscript.exe' or Name='cmd.exe'\" | "
          "ForEach-Object { $m = try { [int]((Get-Date) - $_.CreationDate).TotalMinutes } catch { 0 }; "
          "\"$($_.ProcessId)|$m|$($_.CommandLine)\" }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=60,
                           encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for linha in (r.stdout or "").splitlines():
        p = linha.split("|", 2)
        if len(p) == 3 and p[0].strip().isdigit():
            out[int(p[0])] = (int(p[1]) if p[1].strip().lstrip("-").isdigit() else 0, p[2])
    return out


def _procs():
    return _cache("procs", 20, _lista_processos)


def _rodando(marcas):
    """Processos com a marca, sem repetir lançador + filho (mesma linha de comando): o mais antigo fica."""
    vistos = {}
    for pid, (m, cmd) in _procs().items():
        if any(x in cmd for x in marcas) and "painel_controlador" not in cmd:
            chave = re.sub(r"^\S*python\w*\.exe\"?\s*", "", cmd.strip(), flags=re.I)[:160]
            if chave not in vistos or vistos[chave]["min"] < m:
                vistos[chave] = {"pid": pid, "min": m, "cmd": chave}
    return sorted(vistos.values(), key=lambda x: -x["min"])


# ─── rotas antigas ────────────────────────────────────────────────────────────
def api_geral(_params):
    import controlador
    import controle
    import fila_render
    c = fila_render._cfg()
    item = lambda d: {"projeto": d["projeto"], "rotulo": d.get("rotulo", ""),  # noqa: E731
                      "min": round((time.time() - d.get("desde", time.time())) / 60)}
    return {"controlador": controlador._ler_estado(),
            "fila_pc1": {"rodando": [item(d) for _p, d in fila_render._ler("rodando", c.get("max_h", 6))],
                         "esperando": [item(d) for _p, d in fila_render._ler("esperando", 24)]},
            "controle": _controle_estado(controle)}


def _controle_estado(controle):
    return [{"projeto": p, "nome": controle.NOMES.get(p, p),
             **{e: dict(zip(("ligado", "motivo"), controle.ligado(p, e))) for e in controle.ETAPAS}}
            for p in controle.PROJETOS]


def api_medir(_params):
    import maquinas
    m = {h: maquinas.medir(h) for h in ("pc1", "pc2")}
    try:
        m["desktop"] = maquinas.medir("desktop")
    except Exception:  # noqa: BLE001
        m["desktop"] = {"host": "desktop", "ocioso": False, "motivo": "offline"}
    m["x200ma"] = maquinas.medir("x200ma")
    m["acer"] = maquinas.medir("acer")
    m["kaggle"] = maquinas.medir("kaggle")
    m["colab"] = maquinas.medir("colab")
    for cel in ("s20ultra", "s20"):  # 04/11: Galaxy S20 (celulares.py)
        m[cel] = maquinas.medir(cel)
    return m


def api_canais(_params):
    return _cache("canais", 60, _canais)  # o politica leva ~15 s


def _canais():
    import politica
    cad = politica.cadastro()
    creds = {c["id"]: c for c in politica.carregar_creds()}
    regs = politica._ler_ledger()
    agora = politica.agora()
    out = []
    for k, x in cad.items():
        c = next((creds[i] for i in x.get("creds") or [] if i in creds), None)
        if not c:
            continue
        meus = [r for r in regs if politica._do_canal(r, c)]
        hoje = [r for r in meus if politica._dt(r["ts"]).date() == agora.date()]
        futuros = sorted(t for t in (politica._dt(r.get("publish_at")) for r in meus) if t and t > agora)
        # publicações por dia (hora local) a partir de hoje: a agenda usa isto quando o catálogo grava outro nome
        publica_dia, no_ar_hoje = {}, 0
        for t in (politica._dt(r.get("publish_at")) for r in meus):
            if t and t.astimezone().date() >= agora.astimezone().date():
                dia = t.astimezone().date().isoformat()
                publica_dia[dia] = publica_dia.get(dia, 0) + 1
                no_ar_hoje += t.astimezone().date() == agora.astimezone().date() and t <= agora
        quem = {}
        for r in hoje:
            quem[r.get("projeto") or "?"] = quem.get(r.get("projeto") or "?", 0) + 1
        out.append({"slug": k, "nome": x.get("nome", k), "handle": x.get("handle"), "publica_dia": publica_dia,
                    "no_ar_hoje": no_ar_hoje, "dono": x.get("dono", "?"), "idioma": x.get("idioma", "pt"),
                    "teto": politica.teto_canal(c), "subidos_hoje": len(hoje), "agendados": len(futuros),
                    "prox_publicacao": futuros[0].astimezone().strftime("%Y-%m-%d %H:%M") if futuros else None,
                    "vazio_hoje": politica.canal_vazio_hoje(c), "bloqueado": politica.motivo_bloqueio(c) or None,
                    "quem_subiu": quem, "total_subidos": len(meus), "creds": list(x.get("creds") or [])})
    return out


def _fila_parceiro():
    """{id da credencial: Shorts prontos no PC esperando a vez} (fila do Cortes, chaveada pela credencial do canal)."""
    try:
        if str(RECAPD / "bin") not in sys.path:
            sys.path.insert(0, str(RECAPD / "bin"))
        import parceiro_diario as pdi
        return dict(pdi._fila(pdi.itens(pdi.cfg())))
    except Exception:  # noqa: BLE001
        return {}


def _cobertura():
    """Até que dia cada canal ativo tem postagem: último dia agendado + os vídeos prontos no PC (ainda sem agenda)
    divididos pelo teto/dia do canal. Dono 24/10: 'até que dia temos postagem em todos os canais (o que tem menos),
    contando o que tem no PC e agendado, e outro até que dia vai o canal que tem mais'."""
    hoje = date.today()
    fila = _fila_parceiro()
    try:
        hiper_dias = int((_ler(BASE / "estado" / "controlador.json", {}).get("estoques") or {}).get("hipercool_pt") or 0)
    except (TypeError, ValueError):
        hiper_dias = 0
    out = []
    for c in _cache("canais", 60, _canais) or []:
        if c.get("bloqueado"):
            continue
        agendados = sorted(d for d, n in (c.get("publica_dia") or {}).items() if n and d >= hoje.isoformat())
        ultimo = date.fromisoformat(agendados[-1]) if agendados else hoje - timedelta(days=1)
        no_pc = sum(fila.get(i, 0) for i in c.get("creds") or [])
        teto = max(1, c.get("teto") or 3)
        dias_pc = -(-no_pc // teto)
        if c.get("slug") == "manhwanoturno":
            dias_pc += hiper_dias  # capítulos prontos do hipercool: o painel já conta em dias
        ate = ultimo + timedelta(days=dias_pc)
        out.append({"slug": c["slug"], "nome": c.get("nome"), "dono": c.get("dono"), "agendados_ate": agendados[-1] if agendados else None,
                    "no_pc": no_pc, "teto": teto, "ate": ate.isoformat(), "dias": (ate - hoje).days + 1})
    out.sort(key=lambda x: x["ate"])
    return {"hoje": hoje.isoformat(), "canais": out, "menor": out[0] if out else None, "maior": out[-1] if out else None}


def api_cobertura(_params):
    return _cache("cobertura", 120, _cobertura)


def _janela(params, dias_padrao=7):
    """(início, fim) em hora local: ?horas=N (últimas N h), ?de=&ate= (dias inteiros) ou ?dias=N (N dias até agora)."""
    agora = datetime.now().astimezone()
    if params.get("horas", [""])[0]:
        return agora - timedelta(hours=max(1, int(params["horas"][0]))), agora
    de, ate = _periodo(params, dias_padrao)
    ini = datetime.combine(date.fromisoformat(de), datetime.min.time()).astimezone()
    fim = datetime.combine(date.fromisoformat(ate), datetime.max.time()).astimezone()
    return ini, min(fim, agora)


def _abre_em(r):
    """Hora (local) em que o vídeo do ledger ficou público: publish_at do agendamento, ou o upload se subiu sem agenda."""
    try:
        return datetime.fromisoformat((r.get("publish_at") or r.get("ts") or "").replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


_YT = {"token": None, "cred": None, "ate": 0, "ruins": {}, "stats": {}}
_YT_TRAVA = threading.Lock()


def _yt_tokens():
    """(cred_id, access_token) de canais que leem a API. 22/10: a 1ª conta do youtube_canais.json está suspensa
    (403 authenticatedUserAccountSuspended) e outras sem cota; a que falha fica 6 h fora e a que funciona vai na frente."""
    if _YT["token"] and time.time() < _YT["ate"]:
        yield _YT["cred"], _YT["token"]
    import politica
    creds = [c for c in politica.carregar_creds() if c.get("clientId") and c.get("clientSecret") and c.get("refresh_token")]
    creds.sort(key=lambda c: c["id"] != _YT["cred"])
    for c in creds:
        if _YT["ruins"].get(c["id"], 0) > time.time():
            continue
        dados = urlencode({"client_id": c["clientId"], "client_secret": c["clientSecret"],
                           "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=dados),
                                        timeout=15) as r:
                tok = json.loads(r.read())["access_token"]
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            _YT["ruins"][c["id"]] = time.time() + 6 * 3600
            continue
        _YT.update(token=tok, cred=c["id"], ate=time.time() + 45 * 60)
        yield c["id"], tok


def _yt_videos(ids):
    """{video_id: item da videos.list (snippet, statistics, status) ou None se sumiu/privado}; 50 por chamada (1
    unidade de cota cada) e cada vídeo fica 10 min guardado: trocar de período não consulta tudo de novo."""
    with _YT_TRAVA:
        agora = time.time()
        falta = [v for v in ids if v not in _YT["stats"] or agora - _YT["stats"][v][0] > 600]
        for i in range(0, len(falta), 50):
            lote = falta[i:i + 50]
            url = "https://www.googleapis.com/youtube/v3/videos?" + urlencode(
                {"part": "snippet,statistics,status", "id": ",".join(lote), "maxResults": 50})
            itens = None
            for cred, tok in _yt_tokens():
                try:
                    with urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": "Bearer " + tok}),
                                                timeout=30) as r:
                        itens = json.loads(r.read()).get("items", [])
                    break
                except urllib.error.HTTPError as e:
                    if e.code not in (401, 403):
                        raise
                    _YT["ruins"][cred] = time.time() + 6 * 3600
                    _YT["token"] = None
            if itens is None:
                raise RuntimeError("nenhum canal do youtube_canais.json conseguiu ler a API (suspenso, sem cota ou token morto)")
            achados = {it["id"]: it for it in itens}
            for v in lote:
                _YT["stats"][v] = (agora, achados.get(v))
        return {v: _YT["stats"][v][1] for v in ids if v in _YT["stats"]}


_SITUACAO = {"public": "público", "unlisted": "não listado", "private": "privado"}


def api_ranking(params):
    """Views AO VIVO (API do YouTube) dos vídeos que ABRIRAM no período (publish_at do ledger, hora local).
    Dono 22/10: lia o metricas_studio.json e contava vídeo LIDO no período; Hoje ficava vazio, 24 h não existia e
    7/14/30/90 davam a mesma lista (as leituras eram todas de 19-21/10). Retenção/duração seguem vindo do Studio."""
    ini, fim = _janela(params, 7)
    regs, desde = {}, None
    for r in _ler_jsonl(LEDGER):
        q = _abre_em(r) if r.get("video_id") else None
        if q:
            desde = min(desde or q, q)
        if q and ini <= q <= fim:
            regs[r["video_id"]] = (r, q)
    met = _ler(METRICAS)
    fonte, aviso = f"YouTube ao vivo ({datetime.now():%d/%m %H:%M})", None
    try:
        api = _yt_videos(list(regs))
    except Exception as e:  # noqa: BLE001
        api = None
        fonte, aviso = "Studio", f"API do YouTube falhou ({type(e).__name__}: {str(e)[:120]}); views da última leitura do Studio, onde houver."
    videos = []
    for vid, (r, q) in regs.items():
        m = met.get(vid) if isinstance(met.get(vid), dict) else {}
        if api is not None:
            it = api.get(vid) or {}
            st, sn = it.get("statistics") or {}, it.get("snippet") or {}
            sit = _SITUACAO.get((it.get("status") or {}).get("privacyStatus"), "removido ou privado")
            views = int(st["viewCount"]) if sit in ("público", "não listado") and "viewCount" in st else None
            likes = int(st["likeCount"]) if views is not None and "likeCount" in st else None
            coment = int(st["commentCount"]) if views is not None and "commentCount" in st else None
            titulo, canal = sn.get("title") or m.get("titulo") or r.get("arquivo"), sn.get("channelTitle") or r.get("canal")
        else:
            sit, likes, coment = "?", None, None
            views = int(m["views"]) if m.get("views") is not None else None
            titulo, canal = m.get("titulo") or r.get("arquivo"), m.get("canal_slug") or r.get("canal")
        videos.append({"id": vid, "titulo": titulo, "canal": canal, "projeto": r.get("projeto"), "tipo": r.get("tipo"),
                       "situacao": sit, "views": views, "likes": likes, "comentarios": coment,
                       "abriu": q.strftime("%Y-%m-%d %H:%M"), "dia": q.date().isoformat(),
                       "continuaram": m.get("continuaram"), "dur_media": m.get("dur_media"), "fonte": m.get("fonte"),
                       "lido_em": (m.get("lido_em") or "")[:16] or None})
    # 30/10 dona ("não estamos contabilizando direito no painel e no telão"): o ranking só via o ledger do postador
    # (481 de 2.681 vídeos dos canais). Entram também os vídeos dos canais postados por outro caminho (rede, à mão,
    # antes de 04/10) que abriram no período — do cache do videos_canais (lista de uploads do YouTube, 1 h).
    try:
        import videos_canais
        no_ledger = {v["id"] for v in videos}
        for v in videos_canais.dados(max_idade_s=10 ** 9).get("videos", []):
            q = videos_canais.pub_local(v)
            if v["id"] in no_ledger or not q or not (ini <= q <= fim):
                continue
            videos.append({"id": v["id"], "titulo": v.get("titulo"), "canal": v.get("canal"),
                           "projeto": "fora do postador", "tipo": None, "situacao": "público", "views": v.get("views"),
                           "likes": v.get("likes"), "comentarios": v.get("comentarios"),
                           "abriu": q.strftime("%Y-%m-%d %H:%M"), "dia": q.date().isoformat(), "continuaram": None,
                           "dur_media": None, "fonte": "lista de uploads do canal", "lido_em": None})
    except Exception:  # noqa: BLE001 — sem o cache, fica só o ledger como antes
        pass
    videos.sort(key=lambda v: (v["views"] is None, -(v["views"] or 0)))
    por_canal = {}
    for v in videos:
        if v["views"] is None:
            continue
        a = por_canal.setdefault(v["canal"] or "?", {"canal": v["canal"] or "?", "videos": 0, "views": 0, "melhor": 0})
        a["videos"] += 1
        a["views"] += v["views"]
        a["melhor"] = max(a["melhor"], v["views"])
    for a in por_canal.values():
        a["media"] = round(a["views"] / a["videos"])
    com = [v["views"] for v in videos if v["views"] is not None]
    return {"de": ini.strftime("%Y-%m-%d %H:%M"), "ate": fim.strftime("%Y-%m-%d %H:%M"), "total": len(videos),
            "com_views": len(com), "views_total": sum(com), "mediana": round(statistics.median(com)) if com else None,
            "nao_publicos": len(videos) - len(com), "fonte": fonte, "aviso": aviso, "videos": videos,
            "registro_desde": desde.strftime("%Y-%m-%d %H:%M") if desde else None,  # ledger começa em 04/10: 30 e 90 dias iguais
            "por_canal": sorted(por_canal.values(), key=lambda a: -a["views"])}


HIST_VIDEOS = HISTORICO.with_name("historico_videos.jsonl")


def _ajustar_por_videos(por):
    """10/11 (dona: "o painel parou em 52 mil desde a tarde"): o total do canal (statistics.viewCount) o YouTube só
    atualiza 1-2x/dia — a barra do dia ficava congelada horas. As views de CADA vídeo atualizam em minutos
    (historico_videos.jsonl). Aqui: depois da última vez que o total do canal mudou, soma o que cada vídeo ganhou desde
    então (vídeo novo conta do zero; ganho negativo = 0). Desligar: PAINEL_VIEWS_POR_VIDEO=0."""
    if os.environ.get("PAINEL_VIEWS_POR_VIDEO", "1") == "0":
        return
    pv = {}
    for r in _ler_jsonl(HIST_VIDEOS):
        if r.get("slug"):
            pv.setdefault(r["slug"], []).append(r)
    for slug, regs in por.items():
        vids = sorted(pv.get(slug, []), key=lambda r: r.get("ts", ""))
        if not vids:
            continue
        regs.sort(key=lambda r: r.get("ts", ""))
        base_i = 0  # última leitura em que o total do canal MUDOU
        for i in range(1, len(regs)):
            if regs[i].get("views") != regs[i - 1].get("views"):
                base_i = i
        base = regs[base_i]
        ref = next((v for v in reversed(vids) if v["ts"] <= base["ts"]), None)
        if not ref:
            continue
        for r in regs[base_i + 1:]:
            atual = next((v for v in reversed(vids) if v["ts"] <= r["ts"]), None)
            if not atual or atual is ref:
                continue
            ganho = sum(max(0, n - ref["v"].get(vid, 0)) for vid, n in atual["v"].items())
            r["views"] = base.get("views", 0) + ganho
            r["views_estimado"] = True


def api_canais_views(params):
    """Inscritos/views de cada canal e quanto ganharam no período (historico.jsonl do painel_canais)."""
    de, ate = _periodo(params, 7)
    por = {}
    for r in _ler_jsonl(HISTORICO):
        if r.get("slug") and (r.get("ts") or "")[:10] <= ate:
            por.setdefault(r["slug"], []).append(r)
    _ajustar_por_videos(por)
    # 01/11 (dona: painel com dados errados): o historico.jsonl do painel_canais só tem 12 canais; os outros (Noturnos,
    # inovare_*) vêm do histórico do videos_canais.py (mesma fonte: total do canal na API do YouTube)
    norm = {s.replace("-", "").replace("_", ""): s for s in por}
    extra = {}
    for r in _ler_jsonl(BASE / "estado" / "canais_views_hist.jsonl"):
        if r.get("slug") and (r.get("ts") or "")[:10] <= ate:
            extra.setdefault(r["slug"], []).append(r)
    parado = (datetime.now() - timedelta(days=3)).isoformat()
    for slug, regs in extra.items():
        velho = norm.get(slug)
        if velho is None:
            por[slug] = regs
        elif max(r.get("ts", "") for r in por[velho]) < parado:  # inovare_*: painel_canais parou em 12–13/10
            por[velho] = regs
    out = []
    for slug, regs in por.items():
        regs.sort(key=lambda r: r.get("ts", ""))
        # 11/11 (dona: "ontem 13 mil não faz sentido"): o total de views do YouTube só muda 1x/dia, de MADRUGADA
        # (00h–06h), quando ele fecha o dia ANTERIOR — o 10/11 ficou parado o dia todo em 841.135 e +53 mil apareceram
        # entre 00:10 e 06:37 do dia 11 → o gráfico e os cards punham no 11 as views assistidas no 10. Coleta antes das
        # 06:00 conta como fechamento do dia anterior (vale para a série E para o ganho dos cards).
        # PAINEL_VIEWS_MADRUGADA=0 volta ao antigo.
        corte_h = 6 if os.environ.get("PAINEL_VIEWS_MADRUGADA", "1") != "0" else 0

        def _dia(r, h=corte_h):
            try:
                return (datetime.fromisoformat(r["ts"][:16]) - timedelta(hours=h)).date().isoformat()
            except ValueError:
                return r["ts"][:10]
        # 12/11: os INSCRITOS mudam o dia todo (em tempo real: 1.472 às 05h → 1.580 às 23h de 11/11) — o corte das 06h
        # é só das VIEWS; com ele, os inscritos de 00h–06h iam pro dia anterior. Views: dia com corte; inscritos: dia real.
        fim = regs[-1]
        antes_v = [r for r in regs if _dia(r) < de]
        antes_i = [r for r in regs if _dia(r, 0) < de]
        ini_v = antes_v[-1] if antes_v else regs[0]
        ini_i = antes_i[-1] if antes_i else regs[0]
        dia_v, dia_i = {}, {}  # última coleta de cada dia: com várias por dia o corte em 60 só cobria ~8 dias (24/10)
        for r in regs:
            if _dia(r) >= de:
                dia_v[_dia(r)] = r
            if _dia(r, 0) >= de:
                dia_i[_dia(r, 0)] = r
        dias = sorted(set(dia_v) | set(dia_i))
        serie, ult_i, ult_v = [], ini_i.get("inscritos", 0), ini_v.get("views", 0)
        for d in dias:
            ult_i = dia_i[d].get("inscritos", ult_i) if d in dia_i else ult_i
            ult_v = dia_v[d].get("views", ult_v) if d in dia_v else ult_v
            serie.append([d, ult_i, ult_v])
        out.append({"slug": slug, "inscritos": fim.get("inscritos", 0), "views": fim.get("views", 0),
                    "videos": fim.get("videos", 0), "ganho_inscritos": fim.get("inscritos", 0) - ini_i.get("inscritos", 0),
                    "ganho_views": fim.get("views", 0) - ini_v.get("views", 0), "desde": ini_v.get("ts", "")[:16],
                    "ate": fim.get("ts", "")[:16], "serie": serie[-120:]})
    out.sort(key=lambda x: -x["ganho_views"])
    return {"de": de, "ate": ate, "canais": out}


def api_views_mesma_hora(_params):
    """12/11 (dona: "por que aqui diminuiu pra 2 mil views?"): o "Views hoje" começa às 06h e o YouTube solta as views
    em lotes (madrugada e saltos à tarde) — de manhã o número é sempre pequeno. Comparação justa: o ganho de ONTEM do
    início do dia dele (06h) até a MESMA hora de agora. Mesma fonte dos cartões (canais_views_hist), por canal."""
    agora = datetime.now()
    ini_hoje = agora.replace(hour=6, minute=0, second=0, microsecond=0)
    if agora < ini_hoje:
        ini_hoje -= timedelta(days=1)
    ini_ont, fim_ont = ini_hoje - timedelta(days=1), agora - timedelta(days=1)
    por = {}
    for r in _ler_jsonl(BASE / "estado" / "canais_views_hist.jsonl"):
        try:
            t = datetime.fromisoformat(r["ts"][:16])
        except (KeyError, ValueError):
            continue
        if r.get("slug") and ini_ont - timedelta(days=1) <= t <= agora:
            por.setdefault(r["slug"], []).append((t, r.get("views", 0)))

    def ganho(ini, fim):
        tot = 0
        for regs in por.values():
            antes = [v for t, v in regs if t <= ini]
            ate = [v for t, v in regs if t <= fim]
            if antes and ate:
                tot += max(0, ate[-1] - antes[-1])
        return tot
    return {"hoje": ganho(ini_hoje, agora), "ontem_mesma_hora": ganho(ini_ont, fim_ont),
            "hora": agora.strftime("%H:%M")}


def api_ranking_canais(params):
    """10/11 (dona: "ranking dos canais por inscritos, views, crescimento do dia ou da semana, que eu possa classificar
    e filtrar; metas dinâmicas pra ver quais canais podem"): cada canal com o ganho de hoje, 7 e 30 dias e o ritmo
    de hoje contra a média diária DELE (7 dias). "acima do normal" = hoje >= 2x a média do próprio canal."""
    # 12/11 (auditoria): com dias=30 a série começa em hoje-29 e o ganho(30) procura um dia <= hoje-30 — a coluna de
    # 30 dias saía "—" nos 31 canais. 31 dias de série dão o ponto de partida.
    base = {c["slug"]: c for c in api_canais_views({"dias": ["31"]})["canais"]}
    hoje = date.today().isoformat()
    out = []
    for slug, c in base.items():
        serie = {d: (i, v) for d, i, v in c.get("serie") or []}
        dias = sorted(serie)
        if not dias:
            continue
        fim_i, fim_v = c["inscritos"], c["views"]

        def ganho(n):
            corte = (date.today() - timedelta(days=n)).isoformat()
            ant = [d for d in dias if d <= corte]
            if not ant:
                return None, None
            i, v = serie[ant[-1]]
            return fim_i - i, fim_v - v
        gi1, gv1 = ganho(1)
        gi7, gv7 = ganho(7)
        gi30, gv30 = ganho(30)
        # média diária dos 7 dias ANTES de hoje (hoje ainda está acontecendo)
        ant = [d for d in dias if d < hoje]
        med_i = med_v = None
        if len(ant) >= 3:
            j = [d for d in ant if d >= (date.today() - timedelta(days=8)).isoformat()] or ant[-8:]
            n = max(1, (date.fromisoformat(j[-1]) - date.fromisoformat(j[0])).days)
            med_i = (serie[j[-1]][0] - serie[j[0]][0]) / n
            med_v = (serie[j[-1]][1] - serie[j[0]][1]) / n
        # 12/11 (auditoria): o ganho de HOJE (dia pela metade) era comparado com a média do dia INTEIRO — de manhã 17 dos
        # 31 canais saíam "abaixo do normal" sem nada errado. Agora a média é proporcional ao pedaço do dia que já
        # passou (views: o dia delas começa às 06h, o corte do painel; inscritos: à meia-noite) e "abaixo" só depois
        # das 14h, quando já tem dia suficiente pra julgar.
        agora_dt = datetime.now()
        frac_i = max(0.1, (agora_dt.hour * 60 + agora_dt.minute) / 1440)
        frac_v = max(0.1, (((agora_dt.hour - 6) % 24) * 60 + agora_dt.minute) / 1440)
        ritmo = lambda g, m, f: None if g is None or m is None else round(g / max(m * f, 1), 1)  # noqa: E731
        ri, rv = ritmo(gi1, med_i, frac_i), ritmo(gv1, med_v, frac_v)
        top = max(x for x in (ri or 0, rv or 0))
        cedo = agora_dt.hour < 14
        out.append({"canal": slug, "inscritos": fim_i, "views": fim_v, "videos": c.get("videos"),
                    "insc_hoje": gi1, "insc_7d": gi7, "insc_30d": gi30, "views_hoje": gv1, "views_7d": gv7,
                    "views_30d": gv30, "media_insc_dia": None if med_i is None else round(med_i, 1),
                    "media_views_dia": None if med_v is None else round(med_v),
                    "ritmo_insc": ri, "ritmo_views": rv,
                    "situacao": "sem média" if med_v is None else "acima do normal" if top >= 2
                    else "abaixo do normal" if not cedo and (rv or 0) < 0.5 and (med_v or 0) >= 20 else "normal",
                    "ate": c.get("ate")})
    out.sort(key=lambda x: -(x["views_hoje"] or 0))
    return {"canais": out, "em": datetime.now().isoformat(timespec="minutes")}


def _solares():
    """10/11 (dona: "mostrar no principal como estão os Instagram das solares, que têm prioridade"): último post e
    posts de hoje de cada conta (carrossel: cache\\historico_carrosseis*.json; Reel: logs\\reel_*_cron.log; MS:
    videos\\postagem_log.json)."""
    ms = Path(r"D:\ms-energy")
    hoje = date.today()
    contas = {"MS Energy": ("historico_carrosseis.json", None), "Advance": ("historico_carrosseis_advance.json", "reel_advance_cron.log"),
              "Globo": ("historico_carrosseis_globo.json", "reel_globo_cron.log")}
    out = []
    for nome, (hist, log_reel) in contas.items():
        posts = []
        try:
            for p in json.loads((ms / "cache" / hist).read_text(encoding="utf-8")):
                if p.get("data") and p.get("permalink"):
                    posts.append(("carrossel", p["data"][:16].replace("T", " ")))
        except (OSError, ValueError):
            pass
        if log_reel:
            dia = None
            for l in _cauda(ms / "logs" / log_reel, 400):
                m = re.match(r"\[(\d\d)/(\d\d)/(\d{4}) ", l)
                if m:
                    dia = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                m2 = re.match(r"\[(\d\d:\d\d):\d\d\] PUBLICADO", l)
                if m2 and dia:
                    posts.append(("reel", f"{dia} {m2.group(1)}"))
        else:
            try:
                for k, v in json.loads((ms / "videos" / "postagem_log.json").read_text(encoding="utf-8")).items():
                    if isinstance(v, dict) and v.get("insta"):
                        posts.append(("reel", v["insta"][:16].replace("T", " ")))
            except (OSError, ValueError):
                pass
        posts.sort(key=lambda x: x[1])
        ult = posts[-1][1] if posts else None
        h = [p for p in posts if p[1][:10] == hoje.isoformat()]
        horas = round((datetime.now() - datetime.fromisoformat(ult)).total_seconds() / 3600, 1) if ult else None
        # 12/11 (auditoria): "ok = até 6 h sem post" deixava as 3 VERMELHAS toda noite e manhã sem falha nenhuma — os
        # horários são 08:00–23:20 (tarefas AdvanceSolar_*/GloboSolar_*/MSEnergy_*), então 23:20→08:00 sem post é o
        # normal. Agora: vermelho só se um horário da agenda passou há mais de 1 h e nada saiu depois dele.
        atraso = _solar_horario_perdido(nome, ult)
        out.append({"conta": nome, "ultimo": ult, "horas_sem_post": horas, "hoje": len(h),
                    "hoje_reels": sum(1 for p in h if p[0] == "reel"), "hoje_carrosseis": sum(1 for p in h if p[0] == "carrossel"),
                    "horario_perdido": atraso, "ok": ult is not None and atraso is None})
    return out


SOLAR_HORARIOS = {  # tarefas do agendador (Reel + carrossel) — 12/11
    "MS Energy": ("08:40", "10:40", "12:40", "14:40", "16:40", "18:40", "20:40", "22:40"),
    "Advance": ("08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00", "22:00"),
    "Globo": ("09:20", "11:20", "13:20", "15:20", "17:20", "19:20", "21:20", "23:20"),
}


def _solar_horario_perdido(conta, ultimo):
    """'HH:MM' do horário da agenda que passou há mais de 1 h sem nenhum post depois dele (None = em dia)."""
    agora = datetime.now()
    passados = []
    for d in (agora.date() - timedelta(days=1), agora.date()):
        for hm in SOLAR_HORARIOS.get(conta, ()):
            t = datetime.combine(d, datetime.strptime(hm, "%H:%M").time())
            if t <= agora - timedelta(hours=1):
                passados.append(t)
    if not passados:
        return None
    ult_slot = max(passados)
    try:
        ult = datetime.fromisoformat(ultimo) if ultimo else None
    except ValueError:
        ult = None
    return None if ult and ult >= ult_slot - timedelta(minutes=15) else ult_slot.strftime("%d/%m %H:%M")


def api_resumo(_params):
    """10/11 (dona: "reunir as coisas principais na primeira, jamais vou abrir uma por uma"): saúde dos serviços,
    navegador sem navegador, proxy do celular e Instagram das solares numa resposta só."""
    out = {}
    try:
        sv = _pronto("saude")  # a checagem completa leva ~1 min: a tela usa a última e nunca espera
        if sv is None:
            threading.Thread(target=lambda: _cache("saude", 180, _saude), daemon=True).start()
            raise RuntimeError("checando os serviços pela 1ª vez (~1 min)")
        out["servicos"] = {"ok": sum(1 for s in sv if s.get("ok")), "total": len(sv),
                           "falhas": [{"nome": s["nome"], "detalhe": (s.get("detalhe") or "")[:160]} for s in sv if not s.get("ok")]}
    except Exception as e:  # noqa: BLE001
        out["servicos"] = {"erro": f"{type(e).__name__}: {e}"}
    try:
        n = api_nsn({})
        out["nsn"] = {"em": n.get("em"), "resumo": n.get("resumo")}
    except Exception as e:  # noqa: BLE001
        out["nsn"] = {"erro": f"{type(e).__name__}: {e}"}
    try:
        c = api_celular({})
        est = c.get("estado") or {}
        out["celular"] = {"alcancavel": est.get("celular_alcancavel"), "tunel": est.get("tunel"), "vivo": c.get("vivo_agora"),
                          "hoje": c.get("hoje_pelo_celular"), "atualizado": est.get("atualizado"), "erro": c.get("erro")}
    except Exception as e:  # noqa: BLE001
        out["celular"] = {"erro": f"{type(e).__name__}: {e}"}
    try:
        out["solares"] = _solares()
    except Exception as e:  # noqa: BLE001
        out["solares"] = {"erro": f"{type(e).__name__}: {e}"}
    try:  # 12/11: rotas do Flow (HTTP "sem navegador" x tela) — decisão do veo\beta\vigia_flow.py
        out["flow"] = _ler(Path(r"D:\veo\beta\logs\vigia_flow.json")) or {}
    except Exception as e:  # noqa: BLE001
        out["flow"] = {"erro": f"{type(e).__name__}: {e}"}
    return out


def api_placar(_params):
    return _ler(APRENDIZADO)


def api_hipercool(_params):
    import controlador
    import controle
    est = _ler(HIPER_ESTADO)
    caps = []
    for o in _ler(HIPER_CFG, {"obras": []}).get("obras", []):
        for n in range(o.get("de", 1), o.get("ate", 0) + 1):
            pasta = next((p for p in (PANELS / f"{o['slug']}-cap{n:02d}", PANELS / f"{o['slug']}-cap{n}") if p.is_dir()), None)
            if not pasta:
                continue
            e = est.get(pasta.name, {})
            idi = {lang: "postado" if v.get("postado") else ("pronto" if v.get("video") else
                   ("pc2" if v.get("pc2") else ("falhou" if v.get("pc2_falhas") else "-")))
                   for lang, v in (e.get("idiomas") or {}).items()}
            caps.append({"chave": pasta.name, "obra": o.get("titulo", o["slug"]), "num": n,
                         "render": e.get("render", "-"), "situacao": e.get("situacao", "-"),
                         "pt_completo": bool(e.get("pt_completo_em")), "pt_shorts": bool(e.get("pt_shorts_ok")),
                         "linguas_postadas": sum(s == "postado" for s in idi.values()),
                         "linguas_prontas": sum(s == "pronto" for s in idi.values()),
                         "linguas_pc2": sum(s == "pc2" for s in idi.values()), "idiomas": idi})
    estoque, no_pc2, velhas = controlador._hipercool()
    return {"capitulos": caps, "estoque_pt": estoque, "no_pc2": no_pc2, "marcas_velhas": velhas,
            "producao": controle.ligado("hipercool", "producao"), "postagem": controle.ligado("hipercool", "postagem"),
            "log_pc2": _cauda(HIPER_LOGS / "fila_pc2.log", 20), "log_trazer": _cauda(HIPER_LOGS / "fila_pc2-trazer.log", 12),
            "log_postagem": _cauda(HIPER_LOGS / "fila_postagem.log", 12)}


# ─── postagens de todas as redes ─────────────────────────────────────────────
def _titulo_de(caminho, nome, cache_titulos, metricas, vid):
    if vid and isinstance(metricas.get(vid), dict) and metricas[vid].get("titulo"):
        return metricas[vid]["titulo"]
    p = Path(caminho)
    for cand in (p.parent / "postar.json", p.with_suffix(".postar.json"), p.with_suffix(".json"), p.parent / "metadata.json"):
        if cand in cache_titulos:
            t = cache_titulos[cand]
        else:
            d = _ler(cand) if cand.exists() else {}
            t = d.get("titulo") or d.get("title") or d.get("caption") or (d.get("video") or {}).get("titulo") \
                if isinstance(d, dict) else None
            cache_titulos[cand] = t
        if t:
            return t
    return None


def _postagens():
    cat = _ler(CATALOGO, {"videos": []})
    metricas = _ler(METRICAS)
    led = {}
    for r in _ler_jsonl(LEDGER):
        if r.get("video_id"):
            led[r["video_id"]] = r
    agora = datetime.now().astimezone()
    titulos, out, vistos = {}, [], set()
    for v in cat.get("videos", []):
        for p in v.get("postagens", []):
            plat, vid = p.get("plataforma"), p.get("id")
            conta = p.get("conta") or "?"
            quando = p.get("quando") or ""
            # 27/10 (dono: "o painel mostra só 3 postagens de ontem"): post do Instagram pelo navegador grava
            # id "navegador" — com ele na chave, todos viravam 1 só (36 de 26/10 apareciam como 3)
            chave = (plat, vid) if vid and vid != "navegador" else \
                (plat, re.sub(r"\W", "", conta.lower()), quando[:13], v["caminho"])
            if chave in vistos:
                continue
            vistos.add(chave)
            r = led.get(vid) or {}
            m = metricas.get(vid) if vid and isinstance(metricas.get(vid), dict) else {}
            try:
                dt = datetime.fromisoformat(quando.replace("Z", "+00:00"))
                dt = dt if dt.tzinfo else dt.astimezone()
                quando_local = dt.astimezone().strftime("%Y-%m-%d %H:%M")
                no_ar = dt <= agora
            except ValueError:
                quando_local, no_ar = quando[:16], True
            link = (f"https://youtu.be/{vid}" if plat == "youtube" and vid else
                    f"https://www.tiktok.com/@{conta}/video/{vid}" if plat == "tiktok" and vid else
                    f"https://www.instagram.com/reel/{vid}/" if plat == "instagram" and vid and vid != "navegador" else
                    f"https://www.tiktok.com/@{conta}" if plat == "tiktok" else
                    f"https://www.instagram.com/{conta}/" if plat == "instagram" else None)
            out.append({"quando": quando_local, "plataforma": plat, "conta": r.get("canal") or conta,
                        "situacao": "no ar" if no_ar else "agendado", "projeto": v.get("projeto"),
                        "tipo": r.get("tipo") or v.get("tipo"), "origem": v.get("origem"),
                        "titulo": _titulo_de(v["caminho"], v["nome"], titulos, metricas, vid) or Path(v["caminho"]).parent.name,
                        "pasta": Path(v["caminho"]).parent.name, "arquivo": v["nome"], "caminho": v["caminho"],
                        "link": link, "video_id": vid, "views": m.get("views"), "continuaram": m.get("continuaram"),
                        "views_lidas_em": (m.get("lido_em") or "")[:16] or None,
                        "subido_em": (r.get("ts") or "")[:16].replace("T", " ") or None,
                        "mb": round(v.get("bytes", 0) / 1048576, 1)})
    _completar_postagens(out, led, agora)
    _nomear_canais_youtube(out, led)
    out.sort(key=lambda x: x["quando"], reverse=True)
    return out


def _nomear_canais_youtube(out, led):
    """12/11 (auditoria): a coluna "conta" do YouTube vinha do ledger (nome da CONTA Google, não do canal) — "Inovare"
    eram 2 canais (Mistérios Noturnos + Tech Noturno, 99 posts juntos) e o mesmo canal aparecia com 2-3 grafias
    ("AssistIA Investimentos"/"Assist-IA...", "YouTube inovaremanhwaverseind"). Agora o nome sai da credencial do
    upload (canal_id do ledger -> config\\canais.json); sem ela, fica o nome antigo sem o prefixo "YouTube "."""
    try:
        cfg = _ler(Path(r"D:\postador-de-videos\config\canais.json")).get("canais") or {}
        nome_cred = {cr: c.get("nome", slug) for slug, c in cfg.items() for cr in c.get("creds") or []}
    except Exception:  # noqa: BLE001
        nome_cred = {}
    for x in out:
        if x.get("plataforma") != "youtube":
            continue
        r = led.get(x.get("video_id")) or {}
        nome = nome_cred.get(r.get("canal_id"))
        if nome:
            x["conta"] = nome
        elif str(x.get("conta") or "").startswith("YouTube "):
            x["conta"] = x["conta"][8:]


SHORTS_DIR = Path(r"D:\hipercool-materiais\animes recap\shorts")


def _shorts_de_hoje(dia=None):
    """Shorts produzidos no dia em QUALQUER máquina: pastas <obra>_capN_AAAAMMDD[...] com postar.json (a data está no
    nome; mtime/ctime não servem — o postar.json é regravado ao postar)."""
    d = (dia or date.today()).strftime("%Y%m%d")
    try:
        return sum(1 for p in SHORTS_DIR.glob(f"*_{d}*/postar.json"))
    except OSError:
        return None


POSTED_TT = Path(r"D:\postador-de-videos\logs\tiktok_auto_posted.json")
POSTED_IG = Path(r"D:\postador-de-videos\logs\instagram_auto_posted.json")


def _completar_postagens(out, led, agora):
    """12/11 (dona: "parece que ontem só 81 no painel — menos da metade do pico"): o painel só lia o CATÁLOGO de vídeos,
    e a maioria dos posts não passa por ele — 11/11 o painel mostrou YouTube 37, Insta 28, TikTok 16 (=81) contra os
    registros reais YouTube 104 publicados (133 subidos), Insta 58, TikTok 66. Completa com os registros que gravam
    TODO post: uploads_ledger (YouTube), tiktok_auto_posted e instagram_auto_posted. Sem duplicar (id do YouTube;
    TikTok/Insta por conta + arquivo + minuto). PAINEL_SO_CATALOGO=1 volta ao antigo."""
    if os.environ.get("PAINEL_SO_CATALOGO") == "1":
        return
    vistos_yt = {x["video_id"] for x in out if x["plataforma"] == "youtube" and x.get("video_id")}
    vistos_rede = {(x["plataforma"], str(x.get("conta", "")).lower(), (x.get("quando") or "")[:16]) for x in out
                   if x["plataforma"] in ("tiktok", "instagram")}

    def _linha(plat, quando_dt, conta, caminho, vid=None, projeto=None, situacao=None, subido=None):
        p = Path(str(caminho or ""))
        return {"quando": quando_dt.astimezone().strftime("%Y-%m-%d %H:%M"), "plataforma": plat, "conta": conta,
                "situacao": situacao or ("no ar" if quando_dt <= agora else "agendado"), "projeto": projeto,
                "tipo": None, "origem": None, "titulo": p.parent.name or p.name, "pasta": p.parent.name, "arquivo": p.name,
                "caminho": str(caminho or ""), "video_id": vid, "views": None, "continuaram": None, "views_lidas_em": None,
                "subido_em": subido, "mb": None,
                "link": (f"https://youtu.be/{vid}" if plat == "youtube" and vid else
                         f"https://www.tiktok.com/@{conta}" if plat == "tiktok" else
                         f"https://www.instagram.com/{conta}/" if plat == "instagram" else None)}

    def _dt(s):
        try:
            d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
            return d if d.tzinfo else d.astimezone()
        except ValueError:
            return None
    met = _ler(METRICAS)  # 12/11 (auditoria): as linhas novas vinham sem views — "Views lidas" cobria só o catálogo
    for vid, r in led.items():  # YouTube: todo upload (o horário que conta é o da publicação agendada)
        if vid in vistos_yt:
            continue
        q = _dt(r.get("publish_at") or "") or _dt(r.get("ts") or "")
        if q:
            ln = _linha("youtube", q, r.get("canal") or "?", r.get("arquivo"), vid, r.get("projeto"),
                        subido=(r.get("ts") or "")[:16].replace("T", " ") or None)
            m = met.get(vid) if isinstance(met.get(vid), dict) else {}
            if m:
                ln.update(views=m.get("views"), continuaram=m.get("continuaram"),
                          views_lidas_em=(m.get("lido_em") or "")[:16] or None)
            out.append(ln)
    for plat, arq in (("tiktok", POSTED_TT), ("instagram", POSTED_IG)):
        for r in _ler(arq, []) or []:
            if not isinstance(r, dict):
                continue
            q = _dt(r.get("timestamp") or "")
            conta = str(r.get("account") or "?")
            if not q or (plat, conta.lower(), q.astimezone().strftime("%Y-%m-%d %H:%M")) in vistos_rede:
                continue
            out.append(_linha(plat, q, conta, r.get("path") or r.get("file"), projeto=r.get("tipo"), situacao="no ar"))
    # 12/11 (auditoria): os Instagram das SOLARES (MS Energy, Advance, Globo — Reel e carrossel) não passam por nenhum
    # dos registros acima: 11/11 foram 12 Reels + 12 carrosséis fora do "Vídeos postados". Mesmos arquivos do _solares.
    ms = Path(r"D:\ms-energy")
    contas_sol = {"MS Energy": "msenergysolar.pa", "Advance": "advance_novoestrela", "Globo": "globosolarenergiag"}
    for nome, (hist, log_reel) in {"MS Energy": ("historico_carrosseis.json", None),
                                   "Advance": ("historico_carrosseis_advance.json", "reel_advance_cron.log"),
                                   "Globo": ("historico_carrosseis_globo.json", "reel_globo_cron.log")}.items():
        conta = contas_sol[nome]
        achados = []
        try:
            for x in json.loads((ms / "cache" / hist).read_text(encoding="utf-8")):
                if x.get("data") and x.get("permalink"):
                    achados.append((x["data"], x.get("pasta") or x["permalink"], "carrossel"))
        except (OSError, ValueError):
            pass
        if log_reel:
            dia = None
            for l in _cauda(ms / "logs" / log_reel, 3000):
                m = re.match(r"\[(\d\d)/(\d\d)/(\d{4}) ", l)
                if m:
                    dia = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                m2 = re.match(r"\[(\d\d:\d\d):\d\d\] PUBLICADO", l)
                if m2 and dia:
                    achados.append((f"{dia}T{m2.group(1)}", f"reel {dia} {m2.group(1)}", "reel"))
        else:
            try:
                for k, v in json.loads((ms / "videos" / "postagem_log.json").read_text(encoding="utf-8")).items():
                    if isinstance(v, dict) and v.get("insta"):
                        achados.append((v["insta"], k + ".mp4", "reel"))
            except (OSError, ValueError):
                pass
        for quando, caminho, tipo in achados:
            q = _dt(quando)
            if not q:
                continue
            chave = ("instagram", conta, q.astimezone().strftime("%Y-%m-%d %H:%M"))
            if chave in vistos_rede:
                continue
            vistos_rede.add(chave)
            out.append(_linha("instagram", q, conta, caminho, projeto=f"solar ({tipo})", situacao="no ar"))


def api_postagens(params):
    de, ate = _periodo(params, 7)
    todas = _cache("postagens", 60, _postagens)
    linhas = [x for x in todas if de <= x["quando"][:10] <= ate or (x["situacao"] == "agendado" and x["quando"][:10] > ate)]
    return {"de": de, "ate": ate, "linhas": linhas, "total_catalogo": len(todas)}


# ─── produção ────────────────────────────────────────────────────────────────
_RX_TS = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")
_RX_VIDEO = re.compile(r"- INFO - ===== (.+) \(([\d.,]+) views\) =====")
ETAPAS_CORTES = [  # (regex, %, o que está fazendo) — na ordem em que aparecem num Short
    (r"\[fetch\] legenda|sem legenda YT", 5, "pegando a legenda do vídeo do parceiro"),
    (r"baixando vídeo-fonte|vídeo-fonte já existe", 8, "baixando o vídeo do parceiro"),
    (r"canal novo coberto|\[parceiro\] marcas fixas", 16, "cobrindo marca e legenda do parceiro"),
    (r"roteiro curto: \d+ frases", 22, "roteiro pronto"),
    (r"Disparando formato", 25, "começando a montar"),
    (r"\[concat|concatenando", 78, "juntando os clipes"),
    (r"queimando música", 82, "pondo a trilha"),
    (r"\[vertical\] gancho", 85, "gancho na tela"),
    (r"queimando legendas", 88, "queimando as legendas"),
    (r"master: ", 95, "mixagem final"),
    (r"\[publish\] alvo", 97, "mandando pra fila de postagem"),
    (r"\[auto\|short\] PRONTO", 100, "pronto"),
]


def _ts(linha):
    m = _RX_TS.match(linha)
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S") if m else None
    except ValueError:
        return None


def _destinos_cortes(dia):
    """[(hora, nome do canal, nicho)] das produções do dia (parceiro_producao.log)."""
    out = []
    for l in _cauda(RECAPD / "logs" / "parceiro_producao.log", 400, filtro=r"produção: "):
        m = re.match(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\] produção: (.+?) \((@[^)]*)\)(?: \[(\w+)\])?", l)
        if m and m.group(1).startswith(dia):
            out.append((datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"), m.group(2), m.group(4) or ""))
    return out


def _cortes_hoje(dia=None):
    """Cada Short tentado no dia (padrão hoje) no PC1 (log _parceiro_<dia>): início/fim, destino, voz, narração (master
    LUFS), resultado."""
    dia = dia or date.today().isoformat()
    try:
        texto = (WS_ANIME / f"_parceiro_{dia.replace('-', '')}.log").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [], None
    destinos = _destinos_cortes(dia)
    blocos, atual = [], None
    for linha in texto.splitlines():
        m = _RX_VIDEO.search(linha)
        if m:
            atual = {"titulo_original": m.group(1)[:120], "views_original": m.group(2), "inicio": _ts(linha), "linhas": []}
            blocos.append(atual)
            continue
        if atual is not None:
            atual["linhas"].append(linha)
    feitos = []
    for b in blocos:
        ls = b["linhas"]
        junto = "\n".join(ls)
        frases = re.search(r"roteiro curto: (\d+) frases", junto)
        # "(base, config N)" desde 20/10: o padrão antigo exigia ")" logo depois da base e todo clone virava "edge"
        voz = re.search(r"voz clonada: (\w+) \((\w+)", junto)
        nicho_v = re.search(r"narrador escolhido pelo nicho: \w+ — \{'nicho': '([^']*)'", junto)
        lufs = re.findall(r"\[vertical\] master: (-?[\d.]+) LUFS", junto)
        alvo = re.search(r"\[publish\] alvo: (.+)", junto)
        pronto = next((l for l in ls if "[auto|short] PRONTO" in l), None)
        falha = next((l for l in ls if re.search(r"pipeline falhou|subprocesso falhou|RuntimeError:", l)), None)
        ultimo_ts = next((_ts(l) for l in reversed(ls) if _ts(l)), None)
        dest = next((d for d in reversed(destinos) if b["inicio"] and d[0] <= b["inicio"]), None)
        pasta = Path(alvo.group(1).strip()) if alvo else None
        pj = _ler(pasta / "postar.json") if pasta else {}
        r = {"inicio": b["inicio"].strftime("%H:%M") if b["inicio"] else "?", "titulo_original": b["titulo_original"],
             "views_original": b["views_original"], "canal": (pj.get("canal_postado") or (dest[1] if dest else None)),
             "nicho": (nicho_v.group(1) if nicho_v else None) or (dest[2] if dest else None),
             "voz": f"{voz.group(1)} ({voz.group(2)})" if voz else "edge (sem clone)",
             "frases": int(frases.group(1)) if frases else None,
             "narracao_lufs": float(lufs[0]) if lufs else None, "titulo": pj.get("titulo"),
             "pasta": pasta.name if pasta else None, "link": pj.get("posted_url"),
             "caminho": str(pasta / "video.mp4") if pasta and (pasta / "video.mp4").exists() else None,
             "agendado_para": (pj.get("agendado_para") or "")[:16].replace("T", " ") or None,
             "postagem": ("postado" if pj.get("posted_url") else "reprovado" if "reprovado" in str(pj.get("revisao") or "")
                          else "na fila" if pj else None)}
        if pronto:
            r["resultado"], r["fim"] = "pronto", (_ts(pronto) or ultimo_ts)
        elif falha:
            r["resultado"], r["fim"] = "falhou: " + re.sub(r".*(RuntimeError: |ERROR - )", "", falha)[:140], ultimo_ts
        else:
            r["resultado"], r["fim"] = "em andamento", None
        r["dur_min"] = round((r["fim"] - b["inicio"]).total_seconds() / 60) if r["fim"] and b["inicio"] else None
        r["fim"] = r["fim"].strftime("%H:%M") if r["fim"] else None
        if r["narracao_lufs"] is not None:
            r["narracao"] = "MUDA" if r["narracao_lufs"] < -23 else "ok"
        r["_linhas"], r["_inicio"] = ls, b["inicio"]
        feitos.append(r)
    return feitos, destinos


def _progresso_cortes(b):
    """(%, etapa) de um Short em andamento a partir das linhas do log dele."""
    pct, etapa = 2, "escolhendo o vídeo do parceiro"
    n = b.get("frases") or 0
    for l in b["_linhas"]:
        for rx, p, nome in ETAPAS_CORTES:
            if re.search(rx, l) and p >= pct:
                pct, etapa = p, nome
        if n:
            m = re.search(r"\[clone v2?\] frase (\d+)|wrote audio_(\d+)\.wav", l)
            if m and pct <= 50:
                i = int(m.group(1) or m.group(2))
                pct, etapa = max(pct, 25 + round(23 * (i + 1) / n)), f"narrando frase {i + 1} de {n}"
            m = re.search(r"\[humanizar\] frase (\d+)", l)
            if m and pct <= 56:
                i = int(m.group(1))
                pct, etapa = max(pct, 50 + round(6 * (i + 1) / n)), f"humanizando a voz ({i + 1}/{n})"
            m = re.search(r"\[segments/\w+\] clipe (\d+):", l)
            if m and pct < 78:
                i = int(m.group(1))
                pct, etapa = max(pct, 56 + round(21 * (i + 1) / n)), f"cortando clipe {i + 1} de {n}"
        if "[clone] " in l and "frases com a voz" in l and pct < 56:
            pct, etapa = 56, "voz clonada pronta"
    return min(pct, 100), etapa


def _prod_cortes():
    feitos, _dest = _cortes_hoje()
    durs = [f["dur_min"] for f in feitos if f["resultado"] == "pronto" and f["dur_min"]]
    media = round(statistics.median(durs)) if durs else None
    rod = _rodando(PROJETOS["cortes"]["marcas"])
    trabalhos = []
    if rod and feitos and feitos[-1]["resultado"] == "em andamento":
        b = feitos[-1]
        pct, etapa = _progresso_cortes(b)
        passou = round((datetime.now() - b["_inicio"]).total_seconds() / 60) if b["_inicio"] else None
        trabalhos.append({"o_que": f"Short pra {b['canal'] or '?'}", "detalhe": b["titulo_original"], "voz": b["voz"],
                          "pct": pct, "etapa": etapa, "desde_min": passou,
                          "eta_min": (round(passou * (100 - pct) / pct) if passou is not None and pct >= 10
                                      else max(0, media - passou) if media and passou is not None else None),
                          "ultima": next((l for l in reversed(b["_linhas"]) if l.strip()), "")[:220]})
    import controlador
    est = controlador._ler_estado()
    pc2 = [{"o_que": x.get("o_que"), "desde_min": x.get("min")} for x in (est.get("agora") or {}).get("pc2", [])
           if "Cortes" in str(x.get("o_que")) or "anime" in str(x.get("o_que")).lower()]
    for f in sorted((BASE / "estado" / "pc2_parceiro").glob("*.json")):  # 27/10: vários Shorts juntos no PC2
        est_pc2 = _ler(f)
        if est_pc2:
            pc2.append({"o_que": f"Short no PC2 pra {est_pc2.get('destino')}", "detalhe": est_pc2.get("titulo"),
                        "desde": est_pc2.get("inicio")})
    try:
        sys.path.insert(0, str(RECAPD / "bin"))
        import parceiro_diario as pdi
        c = pdi.cfg()
        its = pdi.itens(c)
        fila = pdi._fila(its)
        filas = [{"canal": x.get("nome", x["canal"]), "nicho": x.get("nicho"), "fila": fila[x["canal"]],
                  "alvo": x.get("fila_alvo", c.get("fila_alvo", 2)), "handle": x.get("handle")}
                 for x in c.get("pt", []) if x.get("ativo", True)]
        prontos = sum(1 for x in its if x["estado"] == "pronto")
    except Exception as e:  # noqa: BLE001
        filas, prontos = [{"erro": f"{type(e).__name__}: {e}"}], None
    feitos_pub = [{k: v for k, v in f.items() if not k.startswith("_")} for f in feitos]
    ok = sum(1 for f in feitos if f["resultado"] == "pronto")
    return {"trabalhos": trabalhos, "pc2": pc2, "feitos_hoje": feitos_pub, "media_min": media,
            # 12/11: "prontos hoje" contava só o log do PC1 (5) — os Shorts do PC2/desktop/notebooks/Kaggle ficavam de
            # fora (61 pastas com a data de hoje). Agora: pastas de Short com a data de HOJE no nome (qualquer máquina);
            # "prontos_pc1" mantém o número antigo
            "numeros": {"prontos_hoje": _shorts_de_hoje(), "prontos_pc1": ok,
                        "falhas_hoje": sum(1 for f in feitos if f["resultado"].startswith("falhou")),
                        "mudos_hoje": sum(1 for f in feitos if f.get("narracao") == "MUDA"),
                        "na_fila_de_postagem": prontos, "minutos_por_short": media},
            "filas": filas, "rodando": rod,
            "log": _cauda(WS_ANIME / f"_parceiro_{date.today():%Y%m%d}.log", 30)}


def _prod_hipercool():
    import controlador
    est = controlador._ler_estado()
    estoque, no_pc2, velhas = controlador._hipercool()
    pc2 = [{"o_que": x.get("o_que"), "desde_min": x.get("min")} for x in (est.get("agora") or {}).get("pc2", [])
           if "hipercool" in str(x.get("o_que"))]
    return {"trabalhos": [{"o_que": r["cmd"][:90], "desde_min": r["min"]} for r in _rodando(PROJETOS["hipercool"]["marcas"])],
            "pc2": pc2, "numeros": {"estoque_pt_dias": estoque, "linguas_no_pc2": len(no_pc2), "marcas_velhas_pc2": velhas},
            "log": _cauda(HIPER_LOGS / "fila_pc2.log", 15) + _cauda(HIPER_LOGS / "fila_faltantes.log", 10)
            + _cauda(HIPER_LOGS / "fila_ciclo.log", 10)}


def _prod_msenergy():
    import controlador
    hoje = f"{date.today():%Y%m%d}"
    log_post = _ler(MSE / "videos" / "postagem_log.json")
    videos = []
    for f in sorted((MSE / "videos" / "shorts_veo").glob("ms_energy_solar_*.mp4"), reverse=True)[:30]:
        side = _ler(f.with_suffix(".json"))
        pst = log_post.get(f.stem) or log_post.get(f.name) or {}
        videos.append({"arquivo": f.name, "dia": f"{f.stem[16:20]}-{f.stem[20:22]}-{f.stem[22:24]} {f.stem[25:27]}:{f.stem[27:29]}",
                       "hoje": hoje in f.name, "legenda": side.get("caption") or side.get("legenda") or side.get("titulo"),
                       "mb": round(f.stat().st_size / 1048576, 1),
                       "insta": bool(pst.get("insta")) if isinstance(pst, dict) else None,
                       "tiktok": bool(pst.get("tiktok")) if isinstance(pst, dict) else None})
    gerados = controlador._msenergy_gerados_hoje()
    rod = _rodando(PROJETOS["msenergy"]["marcas"])
    # 12/11 (auditoria): a meta mostrada era sempre a base (2) — o controlador DOBRA quando a reserva está abaixo de
    # 7 dias (controlador.py, mesma conta abaixo); e o % travava em 100 mesmo com 4/2
    estoque_ms = controlador._estoque_msenergy()
    meta = controlador.MSENERGY_POR_DIA * (2 if estoque_ms < controlador.RESERVA_DIAS * controlador.MSENERGY_POR_DIA else 1)
    return {"trabalhos": [{"o_que": "gerando no Flow (Veo 3.1)", "detalhe": r["cmd"][:90], "desde_min": r["min"],
                           "pct": min(95, round(r["min"] / 30 * 100)), "eta_min": max(0, 30 - r["min"])} for r in rod],
            "numeros": {"gerados_hoje": gerados, "meta_dia": meta, "sem_post_insta": estoque_ms},
            "pct_dia": round(gerados / max(1, meta) * 100), "videos": videos,
            "log": _cauda(MSE / "logs" / "gerar_diario.log", 20)}


def _veo_funil():
    """24/10 (funil + foto na hora do Veo): fotos de hoje (aprovadas/tentadas, nota media do rosto), melhor e pior tema
    no placar de 48 h e fotos antigas fora do sorteio. Erro = {} (nunca derruba a aba)."""
    out = {}
    try:
        hoje = datetime.now().strftime("%Y-%m-%d")
        regs = []
        for ln in Path(r"D:\veo\beta\logs\foto_na_hora.jsonl").read_text(encoding="utf-8").splitlines():
            if hoje in ln:
                regs.append(json.loads(ln))
        tent = [r for r in regs if "aprovada" in r]
        notas = [r["nota"] for r in tent if r.get("aprovada")]
        out["fotos_na_hora_hoje"] = f"{sum(1 for r in tent if r['aprovada'])}/{len(tent)} aprovadas"
        if notas:
            out["nota_rosto_media"] = round(sum(notas) / len(notas), 2)
    except Exception:  # noqa: BLE001
        pass
    try:
        g = json.loads(Path(r"D:\postador-de-videos\_analise\placar_veo_temas.json").read_text(encoding="utf-8"))
        vt = {k: v for k, v in g.get("grupos", {}).get("veo", {}).items() if v.get("testes", 0) >= 2}
        if vt:
            taxa = lambda k: vt[k]["vitorias"] / vt[k]["testes"]  # noqa: E731
            top, pior = max(vt, key=taxa), min(vt, key=taxa)
            # sem "_": no celular o nome quebra linha em vez de cortar
            out["tema_que_rende"] = f"{top.replace('_', ' ')} ({vt[top]['vitorias']:g}/{vt[top]['testes']})"
            out["tema_que_perde"] = f"{pior.replace('_', ' ')} ({vt[pior]['vitorias']:g}/{vt[pior]['testes']})"
    except Exception:  # noqa: BLE001
        pass
    try:
        d = json.loads(Path(r"D:\veo\beta\logs\fotos_rosto_reprovado.json").read_text(encoding="utf-8"))
        out["fotos_antigas_fora"] = f"{len(d.get('reprovadas', {}))}/{d.get('total', 0)} (rosto)"
    except Exception:  # noqa: BLE001
        pass
    return out


def _prod_veo():
    import controlador
    est = controlador._ler_estado()
    d = est.get("disparos_hoje", {})
    reserva = controlador._reserva_veo()
    teto_dia, res_min = controlador._veo_tetos()  # 29/10 (D33): em vigor pela rampa do tetos.json
    return {"trabalhos": [{"o_que": r["cmd"][:90], "desde_min": r["min"]} for r in _rodando(PROJETOS["veo"]["marcas"])],
            "numeros": {"reserva_limpos": reserva, "reserva_max": controlador.VEO_RESERVA_MAX,
                        "reserva_min": res_min, "brutos_no_drive": (est.get("drive_brutos") or {}).get("n"),
                        "limpos_hoje": d.get("veo_limpar", 0) * controlador.VEO_LIMPAR_LOTE,
                        "limpar_dia": controlador.VEO_LIMPAR_DIA, "gerados_hoje": d.get("veo_gerar", 0),
                        "teto_dia": teto_dia, **_veo_funil()},
            "pct_reserva": round(min(1, reserva / controlador.VEO_RESERVA_MAX) * 100) if reserva else 0,
            "log": _cauda(VEO_LOG, 15)}


def _prod_simples(pid, logs):
    return {"trabalhos": [{"o_que": r["cmd"][:90], "desde_min": r["min"]} for r in _rodando(PROJETOS[pid]["marcas"])],
            "log": [l for p in logs for l in _cauda(p, 12)]}


def _prod_claude_video():
    """10/11: Reels do Claude Video — feitos hoje, nota da última versão e o que ele está fazendo."""
    ccv = Path(r"D:\claude-code-video")
    hoje = f"{date.today():%Y%m%d}"
    prontos = [f for f in (ccv / "saida").glob("*/*.mp4")]
    feitos_hoje = sum(1 for f in prontos if hoje in f.name)
    nota = None
    for l in reversed(_cauda(ccv / "estado" / "gerar.log", 80)):
        m = re.search(r"\[lapidar\] rodada \d+: nota ([\d.]+)", l)
        if m:
            nota = float(m.group(1))
            break
    d = _prod_simples("historias", [ccv / "estado" / "gerar.log"])
    d["numeros"] = {"gerados_hoje": feitos_hoje, "reels_prontos": len(prontos), "nota_ultima": nota, "meta_nota": 8}
    return d


def api_producao(_params):
    import controle
    import controlador
    estado_ctrl = controlador._ler_estado()
    disparos = estado_ctrl.get("disparos_hoje", {})
    necessidades = {n["nome"].split("_")[0] for n in estado_ctrl.get("necessidades", [])}
    _map_proj = {"cortes": ("cortes",), "hipercool": ("hipercool",), "msenergy": ("msenergy",),
                 "veo": ("veo",), "manhwa-react": ("manhwa-react",), "historias": ("historias",), "postador": ("postador",)}
    out = {}
    fns = {"cortes": _prod_cortes, "hipercool": _prod_hipercool, "msenergy": _prod_msenergy, "veo": _prod_veo,
           "manhwa-react": lambda: _prod_simples("manhwa-react", [MR_LOGS / "lote_noturno.log",
                                                                  MR_LOGS / f"rede_{date.today():%Y%m%d}.log"]),
           "historias": _prod_claude_video,
           "postador": lambda: _prod_simples("postador", [POST_LOGS / "postar_auto.log",
                                                         RECAPD / "logs" / "parceiro_postar_auto.log"])}
    for pid, info in PROJETOS.items():
        try:
            d = fns[pid]()
        except Exception as e:  # noqa: BLE001
            d = {"erro": f"{type(e).__name__}: {e}", "trabalhos": []}
        ctrl = {e: {p: dict(zip(("ligado", "motivo"), controle.ligado(p, e))) for p in info["controle"]}
                for e in controle.ETAPAS}
        n_disparos = sum(v for k, v in disparos.items() if k.startswith(pid) or
                         any(k.startswith(a) for a in _map_proj.get(pid, ())))
        # manhwa-react/postador rodam pelas tarefas deles (não pelo controlador): processo vivo também conta como ativo
        em_execucao = bool(d.get("trabalhos") or d.get("pc2") or (isinstance(d.get("rodando"), list) and d["rodando"]))
        ativo = em_execucao or pid in necessidades or any(k.startswith(pid) for k in disparos)
        out[pid] = {"id": pid, "nome": info["nome"], "sub": info["sub"], "catalogo": info["catalogo"],
                    "controle": ctrl, "disparos_hoje": n_disparos, "ativo": ativo, "em_execucao": em_execucao, **d}
    return out


# ─── registro das ações feitas pelo painel ───────────────────────────────────
ACOES = BASE / "estado" / "painel_acoes.jsonl"


def _registrar(acao, **dados):
    try:
        with open(ACOES, "a", encoding="utf-8") as f:
            f.write(json.dumps({"em": datetime.now().isoformat(timespec="seconds"), "acao": acao, **dados},
                               ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


# ─── tarefas agendadas ───────────────────────────────────────────────────────
PADRAO_TAREFAS = ("Controlador|Painel|Vigia|Parceiro|Hipercool|Postador|TikTok|MSEnergy|ManhwaReact|Anime|VozClonada|"
                  "Veo|Backup|Limpa|Opus|Kiro|Comentario|Catalogo|Rede|Aprendizado|Atualizar|Historias|Engaj|Canais")
CODIGOS = {0: "ok", 1: "falhou (código 1)", 2: "falhou (código 2)", 0x41300: "pronta", 0x41301: "rodando agora",
           0x41303: "ainda não rodou", 0x41306: "encerrada à força", 0x800710E0: "pulou: a anterior ainda rodava",
           0x8004131F: "já estava rodando", 0xC000013A: "interrompida (janela fechada)", 0xFFFFFFFF: "falhou (código -1)",
           0x80070002: "o arquivo do comando não existe", 0x8007010B: "a pasta do comando não existe"}
CODIGOS_OK = {0, 0x41300, 0x41301, 0x41303, 0x800710E0, 0x8004131F}
ESTADOS = {"Ready": "pronta", "Running": "rodando", "Disabled": "desligada", "Queued": "na fila"}


def _ps_json(script, timeout=90):
    import subprocess
    r = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, timeout=timeout,
                       encoding="utf-8", errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    t = (r.stdout or "").strip()
    d = json.loads(t) if t else []
    return d if isinstance(d, list) else [d]


# 12/11 (auditoria): a lista de nomes acima deixava ~100 tarefas NOSSAS de fora (SentinelaContinue, MotorPesquisador,
# VigilanciaSistema, FecharAvisosFlow, LimpezaChrome, Kaggle*, NSN_*, Solares...) — falha nelas nunca aparecia no painel.
# Agora entram TODAS as tarefas da pasta raiz do agendador (as do Windows ficam em subpastas), menos as de fabricante.
FABRICANTES_TAREFAS = ("OneDrive|MicrosoftEdge|Google|Adobe|NVIDIA|Intel|CCleaner|Opera|Brave|npcap|User_Feed|HP |"
                       "IObit|USER_ESRV|Wise Memory|Trader Binance|Atlas - |Laboratorio - ")


_PS_TAREFAS = r"""[Console]::OutputEncoding=[Text.Encoding]::UTF8
$s = New-Object -ComObject Schedule.Service; $s.Connect()
$out = foreach ($t in $s.GetFolder('\').GetTasks(1)) {
  if ($t.Name -match '^(FABRICANTES)') { continue }
  $acao = ''
  try { $x = [xml]$t.Xml; $acao = (($x.Task.Actions.Exec | ForEach-Object { ([string]$_.Command + ' ' + [string]$_.Arguments).Trim() }) -join ' && ') } catch {}
  $ult = ''; if ($t.LastRunTime.Year -gt 2000) { $ult = $t.LastRunTime.ToString('yyyy-MM-dd HH:mm') }
  $prox = ''; if ($t.NextRunTime.Year -gt 2000) { $prox = $t.NextRunTime.ToString('yyyy-MM-dd HH:mm') }
  $st = @{0='Unknown';1='Disabled';2='Queued';3='Ready';4='Running'}[[int]$t.State]
  [pscustomobject]@{nome=$t.Name; estado=$st; ultima=$ult; resultado=[int64]$t.LastTaskResult; proxima=$prox; acao=$acao}
}
$out | ConvertTo-Json -Depth 3 -Compress"""


def _tarefas():
    # 12/11: Get-ScheduledTask + Get-ScheduledTaskInfo por tarefa passava de 90 s com as ~155 tarefas (o painel dava
    # "TimeoutExpired"). Uma consulta só ao agendador (Schedule.Service) traz tudo em ~8 s.
    if os.environ.get("PAINEL_TAREFAS_SO_NOMES") == "1":
        ps = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-ScheduledTask | Where-Object { $_.TaskName -match '"
              + PADRAO_TAREFAS + "' } | ForEach-Object { $i = $_ | Get-ScheduledTaskInfo; [pscustomobject]@{nome=$_.TaskName; "
              "estado=[string]$_.State; ultima=$(if ($i.LastRunTime -and $i.LastRunTime.Year -gt 2000) "
              "{ $i.LastRunTime.ToString('yyyy-MM-dd HH:mm') } else { '' }); resultado=[int64]$i.LastTaskResult; "
              "proxima=$(if ($i.NextRunTime) { $i.NextRunTime.ToString('yyyy-MM-dd HH:mm') } else { '' }); "
              "acao=(($_.Actions | ForEach-Object { ([string]$_.Execute + ' ' + [string]$_.Arguments).Trim() }) -join ' && ')} } "
              "| ConvertTo-Json -Depth 3 -Compress")
    else:
        ps = _PS_TAREFAS.replace("FABRICANTES", FABRICANTES_TAREFAS)
    out = []
    for t in _ps_json(ps, timeout=150):
        cod = int(t.get("resultado") or 0) & 0xFFFFFFFF
        estado = ESTADOS.get(t.get("estado"), t.get("estado"))
        ok = cod in CODIGOS_OK or estado == "desligada" or not t.get("ultima")
        # 29/10 (dona: "por que esses avisos não desaparecem?"): 0x40010004 = a instância ANTERIOR foi encerrada pelo
        # agendador (limite de tempo/parada), não é falha atual. Com a próxima execução agendada ou a tarefa rodando
        # agora, não é problema. O mesmo vale para qualquer código quando a tarefa já está rodando de novo.
        if cod == 0x40010004 and (t.get("proxima") or estado == "rodando"):
            ok = True
        if estado == "rodando":
            ok = True
        out.append({"nome": t.get("nome"), "estado": estado, "ultima": t.get("ultima") or None,
                    "resultado": CODIGOS.get(cod, f"falhou (código 0x{cod:X})"), "codigo": f"0x{cod:X}",
                    "ok": ok, "proxima": t.get("proxima") or None, "acao": (t.get("acao") or "")[:300]})
    out.sort(key=lambda x: (x["ok"], x["estado"] == "desligada", x["nome"].lower()))
    return out


def api_tarefas(_params):
    return {"tarefas": _cache("tarefas", 90, _tarefas)}


def api_medicoes(_params):
    """Aba Medições: views do TikTok por conta (medir_tiktok.py, diário) e Reels/carrosséis do Instagram do MS Energy
    (metricas_insta.py, semanal) — última medição de cada um + estado das tarefas que o botão "medir agora" dispara."""
    def _ultimos(pasta):
        return sorted(Path(pasta).glob("*.json")) if Path(pasta).exists() else []
    tk = _ultimos(r"D:\postador-de-videos\logs\tiktok_views")
    tiktok = None
    if tk:
        atual, antes = _ler(tk[-1]), (_ler(tk[-2]) if len(tk) > 1 else {})
        tiktok = {"data": tk[-1].stem, "antes": tk[-2].stem if len(tk) > 1 else None,
                  "hora": datetime.fromtimestamp(tk[-1].stat().st_mtime).strftime("%d/%m %H:%M"),
                  "contas": [{"conta": k, **v, "ganho": (v.get("views", 0) - antes[k].get("views", 0)) if k in antes else None}
                             for k, v in atual.items()]}
    ig = _ultimos(r"D:\ms-energy\cache\metricas")
    insta = None
    if ig:
        d = _ler(ig[-1])
        insta = {"data": ig[-1].stem, "hora": datetime.fromtimestamp(ig[-1].stat().st_mtime).strftime("%d/%m %H:%M"),
                 "seguidores": (d.get("perfil") or {}).get("followers_count"),
                 "novo": d.get("novo"), "antigo": d.get("antigo"), "reels": d.get("reels") or []}
    tarefas = {t["nome"]: t for t in _cache("tarefas", 90, _tarefas) if t["nome"] in ("TikTok_MedirViews", "MSEnergy_Metricas")}
    return {"tiktok": tiktok, "insta": insta, "tarefas": tarefas}


def api_kanban(_params):
    """Kanban das Máquinas (24/10): o que cada tarefa pode fazer, onde está fixada e as últimas trocas."""
    import transferencias as tr
    d = tr.ler()
    return {"tarefas": {k: {"rotulo": t["rotulo"], "pcs": t["pcs"], "nao": t.get("nao") or {},
                            "proxima_vez": bool(t.get("proxima_vez"))} for k, t in tr.TAREFAS.items()},
            "fixos": d["fixos"], "padrao": tr.PADRAO, "nomes": tr.NOMES, "pedidos": d["pedidos"][-12:][::-1]}


def api_mover(corpo):
    """Solta um cartão em outra coluna: registra o pedido e dispara a troca em segundo plano (para na origem,
    recomeça no destino; transferencias.py). Recusa na hora o que não tem como (ex.: Cortes no PC2)."""
    import subprocess
    import transferencias as tr
    tarefa, de, para = (str(corpo.get(k) or "") for k in ("tarefa", "de", "para"))
    if not re.fullmatch(r"\w+", tarefa) or not re.fullmatch(r"\w+", para) or not re.fullmatch(r"\w*", de):
        raise ValueError("pedido inválido")
    p = tr.pedir(tarefa, de, para)
    if p["situacao"] == "pendente":
        subprocess.Popen([r"D:\veo\venv\Scripts\pythonw.exe", str(BASE / "transferencias.py"), "executar", p["id"]],
                         cwd=str(BASE), creationflags=0x08000000 | 0x00000008)  # sem janela + fora deste processo
    _registrar("mover tarefa", tarefa=tarefa, de=de, para=para, situacao=p["situacao"])
    return p


def api_soltar(corpo):
    import transferencias as tr
    tarefa = str(corpo.get("tarefa") or "")
    if tarefa not in tr.TAREFAS:
        raise ValueError("tarefa inválida")
    tr.soltar(tarefa)
    _registrar("soltar tarefa", tarefa=tarefa)
    return {"ok": True}


def api_tarefa_rodar(corpo):
    import subprocess
    nome = str(corpo.get("nome") or "")
    if not re.fullmatch(r"[\w .\-]+", nome) or not re.search(PADRAO_TAREFAS, nome):
        raise ValueError("tarefa inválida")
    atual = next((t for t in _tarefas() if t["nome"] == nome), None)
    if not atual:
        raise ValueError("tarefa não encontrada")
    if atual["estado"] == "desligada":
        raise ValueError("tarefa desligada: o painel não religa o que foi desligado de propósito")
    if atual["estado"] == "rodando":
        raise ValueError("já está rodando")
    subprocess.run(["powershell", "-NoProfile", "-Command", f"Start-ScheduledTask -TaskName '{nome}'"],
                   capture_output=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    _registrar("rodar tarefa", nome=nome, motivo=corpo.get("motivo"))
    _CACHE.pop("tarefas", None)
    return {"ok": True, "nome": nome}


# ─── bots do Telegram ────────────────────────────────────────────────────────
def _bots():
    import urllib.request
    import urllib.parse
    lista = []
    principal = _ler(Path(r"D:\postador-de-videos\config\telegram.json"))
    if principal.get("bot_token") or principal.get("token"):
        lista.append(("principal", "Principal (o que não tem bot próprio)",
                      principal.get("bot_token") or principal.get("token"), principal.get("chat_id")))
    for k, b in _ler(Path(r"D:\postador-de-videos\config\telegram_bots.json")).items():
        if isinstance(b, dict) and b.get("bot_token"):
            lista.append((k, b.get("nome") or k, b["bot_token"], b.get("chat_id") or principal.get("chat_id")))
    def um(item):
        chave, nome, tok, chat = item
        r = {"chave": chave, "nome": nome, "usuario": None, "link": None, "iniciado": None}
        try:
            me = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getMe", timeout=15).read())
            r["usuario"] = (me.get("result") or {}).get("username")
            r["link"] = f"https://t.me/{r['usuario']}?start=1" if r["usuario"] else None
            q = urllib.parse.urlencode({"chat_id": chat})
            ok = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getChat?{q}", timeout=15).read())
            r["iniciado"] = bool(ok.get("ok"))
        except Exception as e:  # noqa: BLE001
            r["iniciado"] = False if "400" in str(e) else None
            r["erro"] = type(e).__name__
        return r
    # cada chamada do Python ao Telegram leva ~15 s neste PC (190 s em série medido 21/10): em paralelo
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(um, lista))


def api_bots(_params):
    return {"bots": _cache("bots", 600, _bots)}


# ─── avisos (tudo o que foi ou seria mandado pro Telegram) ───────────────────
def api_avisos(params):
    de, ate = _periodo(params, 7)
    try:
        import avisos as av
        rota = av.ROTA
    except Exception:  # noqa: BLE001
        rota = {}
    linhas = []
    for r in _ler_jsonl(BASE / "estado" / "avisos.jsonl"):
        dia = (r.get("em") or "")[:10]
        if de <= dia <= ate:
            o = r.get("origem") or "?"
            linhas.append({"em": (r.get("em") or "")[:16].replace("T", " "), "origem": o,
                           "bot": rota.get(o, "principal"), "situacao": r.get("situacao"),
                           "importante": "sim" if r.get("importante") else "não", "texto": (r.get("texto") or "")[:1500]})
    linhas.sort(key=lambda x: x["em"], reverse=True)
    return {"de": de, "ate": ate, "linhas": linhas}


# ─── vídeos de referência (dona 28/10: "vi um vídeo bom" -> fica guardado, avisa e entra na fila de análise) ───
REFS = BASE / "estado" / "videos_referencia.jsonl"


def api_referencias(_params):
    linhas = _ler_jsonl(REFS)
    linhas.sort(key=lambda r: r.get("em", ""), reverse=True)
    return {"linhas": linhas}


def api_referencia_nova(corpo):
    url = str(corpo.get("url") or "").strip()
    if not re.match(r"https?://\S+$", url) or len(url) > 500:
        raise ValueError("cole o link do vídeo (começa com http)")
    if any(r.get("url") == url for r in _ler_jsonl(REFS)):
        raise ValueError("esse vídeo já está na lista")
    obs = str(corpo.get("obs") or "").strip()[:1000]
    item = {"em": datetime.now().isoformat(timespec="seconds"), "url": url, "obs": obs, "situacao": "na fila"}
    REFS.parent.mkdir(parents=True, exist_ok=True)
    with open(REFS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    import html
    import avisos as av
    av.enviar(f"🎬 <b>Vídeo de referência</b> mandado pelo painel (entra na fila de análise):\n{html.escape(url)}"
              + (f"\n<i>{html.escape(obs)}</i>" if obs else ""), "referencia", importante=True)
    return {"ok": True, "item": item}


# ─── aprendizado (achados dos vídeos dos parceiros) ─────────────────────────
APR = BASE / "aprendizado"


def api_aprendizado(_params):
    out = []
    for r in _ler_jsonl(APR / "acervo.jsonl"):
        t = r.get("trecho")
        out.append({"id": r.get("id"), "em": (r.get("em") or "")[:16].replace("T", " "), "status": r.get("status"),
                    "tipo": r.get("tipo"), "descricao": r.get("descricao"), "por_que_novo": r.get("por_que_novo"),
                    "como_aplicar": r.get("como_aplicar"), "modelo": r.get("modelo"), "nota": r.get("nota"),
                    "video": r.get("video"), "url": r.get("url"), "inicio": r.get("inicio"), "fim": r.get("fim"),
                    "trecho": str(t) if t and Path(str(t)).exists() else None})
    out.sort(key=lambda x: x["em"] or "", reverse=True)
    return {"itens": out}


def api_aprendizado_marcar(corpo):
    import aprendizado
    aid, status = str(corpo.get("id") or ""), corpo.get("status")
    if status not in ("aprovado", "reprovado", "pendente"):
        raise ValueError("status inválido")
    i = aprendizado.marcar(aid, status)
    if not i:
        raise ValueError("achado não encontrado")
    if status != "pendente":
        aprendizado._lembrar(i, f"{status} pelo dono (painel)")
    _registrar("aprendizado", id=aid, status=status)
    return {"ok": True, "id": aid, "status": status}


# ─── IA do painel (painel_ia.py) ─────────────────────────────────────────────
def _ia_resumo(j):
    return {k: j.get(k) for k in ("id", "tipo", "pedido", "projeto", "status", "status_ia", "detalhe", "criado",
                                  "inicio", "fim", "voltas", "pai", "aplicado_em", "desfeito_em", "origem",
                                  "auto_aplicar")} | \
        {"mudou": len(j.get("manifesto") or {}), "passo": (j.get("passos") or [{}])[-1].get("o")}


def api_ia(_params):
    import painel_ia
    jobs = painel_ia.todos()
    return {"pedidos": [_ia_resumo(j) for j in jobs], "projetos": {k: v[0] for k, v in painel_ia.PROJETOS.items()},
            "rodando": next((j["id"] for j in jobs if j.get("status") == "rodando"), None),
            "na_fila": sum(1 for j in jobs if j.get("status") == "fila"),
            "vigias": _cache("ia_vigias", 120, painel_ia.historico_vigias)}


def api_ia_pedido(params):
    import painel_ia
    j = painel_ia.ler(params.get("id", [""])[0])
    if not j:
        raise ValueError("pedido não existe")
    j["mudancas"] = painel_ia.mudancas(j["id"]) if j.get("manifesto") else []
    return j


def api_ia_pedir(corpo):
    import painel_ia
    j = painel_ia.pedir(corpo.get("tipo"), corpo.get("pedido"), corpo.get("projeto") or "geral", corpo.get("contexto"))
    _registrar("ia pedir", id=j["id"], tipo=j["tipo"], pedido=j["pedido"][:300])
    return _ia_resumo(j)


def api_ia_conversa(params):
    import painel_ia
    jid = params.get("id", [""])[0]
    if not painel_ia.ler(jid):
        raise ValueError("pedido não existe")
    return {"id": jid, "mensagens": painel_ia.conversa(jid), "doc": painel_ia.documento(jid) is not None}


def api_ia_doc(params):
    import painel_ia
    jid = params.get("id", [""])[0]
    texto = painel_ia.documento(jid)
    if texto is None:
        raise ValueError("documento ainda não existe (sai quando o pedido termina)")
    return {"id": jid, "arquivo": str(painel_ia.DOCS / f"{jid}.md"), "texto": texto}


def api_vigia_conversa(params):
    import painel_ia
    return painel_ia.conversa_vigia(params.get("vigia", [""])[0], params.get("hora", [""])[0])


def _pedido_conserto(titulo):
    return f"Conserte: {titulo}"


def _ia_por_problema(probs):
    """Junta em cada problema o último pedido de conserto da IA pra ele (o painel mostra "ver conversa")."""
    try:
        import painel_ia
        jobs = painel_ia.todos()
    except Exception:  # noqa: BLE001
        return probs
    ultimo = {}
    for j in sorted(jobs, key=lambda j: j.get("criado") or ""):
        if j.get("tipo") == "propor":
            ultimo[j.get("pedido")] = j
    out = []
    for x in probs:
        j = ultimo.get(_pedido_conserto(x.get("titulo")))
        if j and j.get("aplicado_em"):  # a aplicação é o que importa depois que existe
            j = next((a for a in jobs if a.get("id") == j["aplicado_em"]), j)
        out.append({**x, "ia": {k: j.get(k) for k in ("id", "tipo", "status", "status_ia", "criado", "desfeito_em")}}
                   if j else x)
    return out


def api_ia_corrigir_todos(corpo):
    """Botão "corrigir todos" (dono 21/10): 1 proposta por problema, que vira aplicação sozinha se a IA achar o
    conserto (backup + Desfazer como sempre). Pula problema que já tem pedido na fila/rodando ou de menos de 6 h.
    {"ensaio": true} só diz o que faria."""
    import painel_ia
    probs = _ia_por_problema(_cache("problemas", 30, _problemas))
    criar, pulados = [], []
    agora = datetime.now()
    for x in probs:
        ia = x.get("ia") or {}
        recente = ia.get("criado") and (agora - datetime.fromisoformat(ia["criado"])).total_seconds() < 6 * 3600
        if x.get("so_dono") or re.search(r"deslogad|desconectad|verifica", (x.get("titulo") or "") + (x.get("detalhe") or ""), re.I):
            pulados.append({"titulo": x["titulo"], "motivo": "só o dono resolve (login/verificação)"})
        elif ia.get("status") in ("fila", "rodando") or recente:
            pulados.append({"titulo": x["titulo"], "motivo": f"já tem pedido ({ia.get('status')}, {ia.get('id')})"})
        else:
            criar.append(x)
    if corpo.get("ensaio"):
        return {"criar": [x["titulo"] for x in criar], "pulados": pulados}
    criados = []
    for x in criar:
        j = painel_ia.pedir("consertar", _pedido_conserto(x["titulo"]), x.get("projeto") or "geral",
                            x.get("contexto") or x.get("detalhe") or "", origem="corrigir todos", auto_aplicar=True)
        criados.append({"id": j["id"], "titulo": x["titulo"]})
    _registrar("ia corrigir todos", criados=[c["id"] for c in criados], pulados=len(pulados))
    return {"criados": criados, "pulados": pulados}


def api_ia_acao(corpo):
    import painel_ia
    jid, acao = corpo.get("id"), corpo.get("acao")
    if acao == "aplicar":
        j = painel_ia.aplicar(jid)
    elif acao == "parar":
        j = painel_ia.parar(jid)
    elif acao == "desfazer":
        j = painel_ia.desfazer(jid, forcar=bool(corpo.get("forcar")))
    else:
        raise ValueError("ação inválida")
    _registrar("ia " + acao, id=jid)
    return _ia_resumo(j)


# ─── Cortes: um dia qualquer e os segurados ──────────────────────────────────
def api_cortes_dia(params):
    dia = params.get("dia", [date.today().isoformat()])[0]
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", dia):
        raise ValueError("dia inválido")
    feitos, _d = _cortes_hoje(dia)
    dias = sorted({p.stem[10:14] + "-" + p.stem[14:16] + "-" + p.stem[16:18] for p in WS_ANIME.glob("_parceiro_2*.log")
                   if re.fullmatch(r"_parceiro_\d{8}", p.stem)}, reverse=True)
    return {"dia": dia, "dias": dias[:60], "feitos": [{k: v for k, v in f.items() if not k.startswith("_")} for f in feitos]}


def api_segurados(_params):
    """Shorts do parceiro que não vão sair sozinhos: reprovados pela análise do vídeo pronto (nudez) e os 'verificar'
    (o upload estourou o tempo: pode ter subido — conferir no Studio antes de repetir)."""
    sys.path.insert(0, str(RECAPD / "bin"))
    import parceiro_diario as pdi
    out = []
    for x in pdi.itens(pdi.cfg()):
        if x["estado"] not in ("reprovado", "verificar"):
            continue
        d, pasta = x["d"], x["pj"].parent
        out.append({"estado": x["estado"], "pasta": pasta.name, "canal": d.get("canal_postado") or x.get("canal"),
                    "titulo": d.get("titulo"), "motivo": str(d.get("revisao") or d.get("timeout_em") or "")[:300],
                    "quando": datetime.fromtimestamp(x["pj"].stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "caminho": str(pasta / "video.mp4") if (pasta / "video.mp4").exists() else None})
    out.sort(key=lambda r: r["quando"], reverse=True)
    return {"segurados": out}


# ─── agenda (o que sai em cada canal/conta nos próximos dias) ────────────────
def api_agenda(_params):
    linhas = _cache("postagens", 60, _postagens)
    hoje = date.today()
    dias = [(hoje + timedelta(days=i)).isoformat() for i in range(3)]
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    por = {}
    for x in linhas:
        d = x["quando"][:10]
        if d < dias[0]:
            continue
        a = por.setdefault((x["plataforma"], x["conta"]), {"plataforma": x["plataforma"], "conta": x["conta"], "hoje_no_ar": 0,
                                                            "hoje_falta": 0, "amanha": 0, "depois": 0, "mais_tarde": 0,
                                                            "proximo": None, "horarios": []})
        if d == dias[0]:
            a["hoje_no_ar" if x["situacao"] == "no ar" else "hoje_falta"] += 1
        elif d == dias[1]:
            a["amanha"] += 1
        elif d == dias[2]:
            a["depois"] += 1
        else:
            a["mais_tarde"] += 1
        if x["quando"] > agora:
            a["horarios"].append(x["quando"][5:16])
            a["proximo"] = min(a["proximo"] or "9", x["quando"])
    def _norm(s):  # o catálogo grava "MundoQueNaoExiste", "YouTube inovaremanhwaverseind", "ManhwaReact-ia"...
        s = re.sub(r"[^a-z0-9]", "", (s or "").lower())
        return s[7:] if s.startswith("youtube") else s
    contas_yt = {_norm(kk[1]) for kk in por if kk[0] == "youtube"}
    for c in _pronto("canais") or []:  # canal do YouTube sem nada no catálogo nos próximos dias também aparece
        nomes = {_norm(c.get("nome")), _norm(c.get("handle")), _norm(c.get("slug"))} - {""}
        if c.get("bloqueado") or nomes & contas_yt:
            continue
        pd = c.get("publica_dia") or {}  # datas reais do ledger (politica casa o registro com o canal pela credencial)
        no_ar = c.get("no_ar_hoje", 0)
        por[("youtube", c.get("nome"))] = {
            "plataforma": "youtube", "conta": c.get("nome"), "hoje_no_ar": no_ar, "hoje_falta": max(0, pd.get(dias[0], 0) - no_ar),
            "amanha": pd.get(dias[1], 0), "depois": pd.get(dias[2], 0), "mais_tarde": sum(n for d, n in pd.items() if d > dias[2]),
            "proximo": c.get("prox_publicacao"), "horarios": []}
    out = sorted(por.values(), key=lambda a: (a["plataforma"], a["hoje_no_ar"] + a["hoje_falta"], a["amanha"]))
    for a in out:
        a["horarios"] = " ".join(sorted(a["horarios"])[:8])
        # 12/11 (auditoria): TikTok e Instagram postam NA HORA (nunca têm agendamento) — todas as contas deles saíam
        # "nada amanhã" (12 alarmes falsos). Essa regra é só do YouTube, que agenda com dias de antecedência.
        a["situacao"] = ("SEM POST HOJE" if a["hoje_no_ar"] + a["hoje_falta"] == 0 else
                         "nada amanhã" if a["amanha"] == 0 and a["plataforma"] == "youtube" else "ok")
    campos = ("hoje_no_ar", "hoje_falta", "amanha", "depois", "mais_tarde")
    # totais prontos: a IA do painel errava somando as linhas na mão (21/10: disse 21 quando eram 28)
    totais = {c: sum(a[c] for a in out) for c in campos}
    totais["por_rede"] = {p: {c: sum(a[c] for a in out if a["plataforma"] == p) for c in campos}
                          for p in sorted({a["plataforma"] for a in out})}
    totais["sem_post_hoje"] = sum(a["situacao"] == "SEM POST HOJE" for a in out)
    return {"dias": dias, "totais": totais, "linhas": out}


# ─── o que dá mais view ──────────────────────────────────────────────────────
def api_desempenho(params):
    r = api_ranking({"dias": [params.get("dias", ["30"])[0]]})
    led = {x["video_id"]: x for x in _ler_jsonl(LEDGER) if x.get("video_id")}
    semana = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
    # narrador e Config 1 x 2: o rodízio da voz clonada guarda a pasta da postagem; o postar.json dela tem o link
    voz_de = {}
    for chave, f in ((_ler(VOZ / "_rodizio.json").get("feitos")) or {}).items():
        pj = _ler(Path(f["postagem"]) / "postar.json") if f.get("postagem") else {}
        m = re.search(r"(?:youtu\.be/|shorts/|v=)([\w-]{11})", str(pj.get("posted_url") or ""))
        if m:
            cfg = f.get("config")
            voz_de[m.group(1)] = (chave.split(":")[0], f"Config {cfg}" if cfg in ("1", "2") else "antes da Config 1/2")
    grupos = {"canal": {}, "projeto": {}, "hora": {}, "dia_semana": {}, "fonte": {}, "narrador": {}, "config_voz": {}}
    met = _ler(METRICAS)
    proj_cat = {x["video_id"]: x.get("projeto") for x in (_pronto("postagens") or []) if x.get("video_id")}
    for v in r["videos"]:
        if v["views"] is None:  # privado/removido: o ranking lista, mas não tem view para comparar
            continue
        pa = (led.get(v["id"]) or {}).get("publish_at") or ""
        try:
            dt = datetime.fromisoformat(pa.replace("Z", "+00:00")).astimezone() if pa else None
        except ValueError:
            dt = None
        if dt is None:  # fora do ledger: hora de publicação = leitura do Studio - idade do vídeo (aprox.)
            m = met.get(v["id"]) if isinstance(met.get(v["id"]), dict) else {}
            try:
                dt = datetime.fromisoformat(m["lido_em"]) - timedelta(hours=float(m.get("idade_h") or 0))
            except (KeyError, TypeError, ValueError):
                dt = None
        chaves = {"canal": v["canal"] or "?", "projeto": v["projeto"] or proj_cat.get(v["id"]) or "?", "fonte": v["fonte"] or "?",
                  "hora": f"{dt.hour:02d}h" if dt else "?", "dia_semana": semana[dt.weekday()] if dt else "?"}
        if v["id"] in voz_de:
            chaves["narrador"], chaves["config_voz"] = voz_de[v["id"]]
        for g, k in chaves.items():
            grupos[g].setdefault(k, []).append(v["views"])
    out = {}
    for g, d in grupos.items():
        out[g] = sorted(({"nome": k, "videos": len(vs), "mediana": round(statistics.median(vs)), "media": round(sum(vs) / len(vs)),
                          "melhor": max(vs), "total": sum(vs), "pct_1000": round(100 * sum(x >= 1000 for x in vs) / len(vs)),
                          "pct_5000": round(100 * sum(x >= 5000 for x in vs) / len(vs))}  # 23/10: marca de 5 mil
                         for k, vs in d.items()), key=lambda x: -x["mediana"])
    return {"de": r["de"], "ate": r["ate"], "total": r["total"], "grupos": out,
            "obs": f"Só YouTube: vídeos que abriram no período, views de {r['fonte']}. Narrador e Config 1 x 2: só os vídeos do rodízio da voz clonada já postados.", "com_voz": len(voz_de)}


# ─── contas TikTok/Instagram e situação dos canais YouTube ───────────────────
CONTAS_TIKTOK = Path(r"D:\projeto-navegador-sem-navegador\relatorios\saida\contas_tiktok.json")


def _contas_tiktok():
    """Entrega real de cada conta do TikTok (views, vídeos zerados, morta), lida do TikTok Studio por HTTP pela central
    de inteligência (relatorios\\inteligencia.py --tiktok). Dono 28/10: as mortas ficam em destaque no painel."""
    d = _ler(CONTAS_TIKTOK) or {}
    return {"quando": d.get("quando"), "contas": d.get("contas") or {}}


def api_contas(_params):
    reuso = _ler(Path(r"D:\postador-de-videos\config\reuso_plataformas.json"))
    linhas, hoje, semana = _cache("postagens", 60, _postagens), date.today().isoformat(), (date.today() - timedelta(days=6)).isoformat()
    contas = {}
    for x in linhas:
        if x["plataforma"] not in ("tiktok", "instagram") or x["situacao"] != "no ar":
            continue
        a = contas.setdefault((x["plataforma"], x["conta"]), {"plataforma": x["plataforma"], "conta": x["conta"], "hoje": 0,
                                                              "semana": 0, "total": 0, "ultimo": ""})
        a["total"] += 1
        a["hoje"] += x["quando"][:10] == hoje
        a["semana"] += x["quando"][:10] >= semana
        a["ultimo"] = max(a["ultimo"], x["quando"])
    for plat in ("tiktok", "instagram"):
        cfg = reuso.get(plat) or {}
        lista = cfg.get("contas") or []
        for c in (lista if isinstance(lista, list) else list(lista)):
            nome = c.get("conta") or c.get("nome") or c.get("usuario") if isinstance(c, dict) else str(c)
            if nome and (plat, nome) not in contas:
                contas[(plat, nome)] = {"plataforma": plat, "conta": nome, "hoje": 0, "semana": 0, "total": 0, "ultimo": ""}
        for a in contas.values():
            if a["plataforma"] == plat:
                a["limite_dia"] = cfg.get("max_por_conta_dia")
    entrega = _contas_tiktok()
    for a in contas.values():
        a["situacao"] = ("parada há 7 dias" if not a["semana"] else "no limite hoje" if a.get("limite_dia") and a["hoje"] >= a["limite_dia"]
                         else "postou hoje" if a["hoje"] else "sem post hoje")
        e = entrega["contas"].get(a["conta"]) if a["plataforma"] == "tiktok" else None
        if e:
            a.update({"arroba": e["arroba"], "views_7d": e["views_7d"], "seguidores": e["seguidores"],
                      "zerados": f"{e['zerados_48h']}/{e['velhos_48h']}", "sem_legenda": e["sem_legenda"],
                      "morta": e["morta"], "entrega": "MORTA" if e["morta"] else "entrega"})
            if e["morta"]:
                a["situacao"] = "MORTA: 0 views"
    st = _ler(Path(r"D:\postador-de-videos\config\canais_status.json"))
    canais = [{"lista": k, "nome": c.get("nome"), "motivo": c.get("motivo"), "em": c.get("em"), "liberado_em": c.get("liberado_em")}
              for k, v in st.items() if not k.startswith("_") and isinstance(v, list) for c in v if isinstance(c, dict)]
    return {"contas": sorted(contas.values(), key=lambda a: (not a.get("morta"), a["plataforma"], -a["semana"])),
            "canais_status": canais, "entrega_lida_em": entrega.get("quando"),
            "regras": {p: {k: v for k, v in (reuso.get(p) or {}).items() if not isinstance(v, (list, dict)) and not k.startswith("_")}
                       for p in ("tiktok", "instagram")}}


# ─── voz clonada ─────────────────────────────────────────────────────────────
VOZ = Path(r"D:\hipercool-materiais\videos_voz_clonada")


def _voz_extras():
    """Dono 21/10 (frente I): nicho, canal, link e views de cada Short com voz clonada. Nicho/canal vêm do
    _historico.jsonl (desde 21/10); link e canal postado do postar.json da pasta; views das métricas do Studio."""
    hist = {}
    for h in _ler_jsonl(VOZ / "_historico.jsonl"):
        if h.get("pasta"):
            hist[str(h["pasta"]).lower().rstrip("\\/")] = h
    met = _ler(METRICAS)
    nome_cred = {cr: c.get("nome", slug) for slug, c in (_ler(Path(r"D:\postador-de-videos\config\canais.json")).get("canais")
                                                          or {}).items() for cr in c.get("creds") or []}

    def de(pasta):
        if not pasta:
            return {}
        h = hist.get(str(pasta).lower().rstrip("\\/"), {})
        pj = _ler(Path(pasta) / "postar.json")
        m = re.search(r"(?:youtu\.be/|shorts/|v=)([\w-]{11})", str(pj.get("posted_url") or ""))
        vid = m.group(1) if m else None
        mt = met.get(vid) if vid and isinstance(met.get(vid), dict) else {}
        return {"nicho": h.get("nicho"), "canal": pj.get("canal_postado") or nome_cred.get(h.get("canal"), h.get("canal")),
                "encaixe": (h.get("escolha") or {}).get("encaixe"), "views": mt.get("views"),
                "link": f"https://youtu.be/{vid}" if vid else None,
                # 22/10: a view só é lida 48 h depois de publicar; a tela diz quando, em vez de "sem leitura"
                "publica_em": pj.get("agendado_para") or pj.get("publish_at") or None}
    return de


def api_voz(_params):
    rz = _ler(VOZ / "_rodizio.json")
    feitos, por = [], {}
    extras = _voz_extras()
    for chave, f in (rz.get("feitos") or {}).items():
        partes = chave.split(":")
        video = Path(f["video"]) if f.get("video") else None
        feitos.append({"narrador": partes[0], "base": partes[1] if len(partes) > 1 else "", "rodada": partes[-1],
                       "quando": f.get("quando"), "video": f.get("video"), "postagem": f.get("postagem"),
                       "existe": bool(video and video.exists()), **extras(f.get("postagem"))})
        # dono 21/10: a pasta do narrador não tem mais cópia do vídeo (só o .txt); a conta sai do rodízio
        n = por.setdefault(partes[0], {"narrador": partes[0], "videos": 0, "config1": 0, "config2": 0, "_t": -1, "_f": f,
                                       "_nichos": set(), "views": 0, "com_views": 0})
        n["videos"] += 1
        n["config1"] += f.get("config") == "1"
        n["config2"] += f.get("config") == "2"
        if feitos[-1].get("nicho"):
            n["_nichos"].add(feitos[-1]["nicho"])
        if isinstance(feitos[-1].get("views"), (int, float)):
            n["views"] += feitos[-1]["views"]
            n["com_views"] += 1
        txt = Path(f["txt"]) if f.get("txt") else None
        t = max((p.stat().st_mtime for p in (txt, video) if p and p.exists()), default=0)
        if t >= n["_t"]:
            n["_t"], n["_f"] = t, f
    narradores = []
    for n in sorted(por.values(), key=lambda x: x["narrador"]):
        f, t = n.pop("_f"), n.pop("_t")
        n["nichos"] = ", ".join(sorted(n.pop("_nichos")))
        txt = Path(f["txt"]) if f.get("txt") else None
        n.update(ultimo=datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") if t > 0 else f.get("quando"),
                 ultimo_caminho=f.get("video"),
                 descricao=txt.read_text(encoding="utf-8", errors="replace")[:600] if txt and txt.exists() else None)
        narradores.append(n)
    falhas = [{"chave": k, **(v if isinstance(v, dict) else {"detalhe": v})} for k, v in (rz.get("falhas") or {}).items()]
    return {"indice": rz.get("indice"), "rodada": rz.get("rodada"), "feitos": sorted(feitos, key=lambda x: x["quando"] or "", reverse=True),
            "narradores": narradores, "falhas": falhas}


# ─── tendências e histórico do disco ─────────────────────────────────────────
DISCO_HIST = BASE / "estado" / "painel_disco.jsonl"


def _gravar_disco():
    """Uma amostra a cada 10 min (D:, C: e o C: do PC2 pela última medida do controlador)."""
    import shutil
    try:
        ult = DISCO_HIST.stat().st_mtime if DISCO_HIST.exists() else 0
        if time.time() - ult < 600:
            return
        import controlador
        med = (controlador._ler_estado().get("medidas") or {}).get("pc2") or {}
        with open(DISCO_HIST, "a", encoding="utf-8") as f:
            f.write(json.dumps({"em": datetime.now().isoformat(timespec="minutes"),
                                "D": round(shutil.disk_usage("D:\\").free / 1e9, 1), "C": round(shutil.disk_usage("C:\\").free / 1e9, 1),
                                "pc2": med.get("disco_gb")}) + "\n")
    except Exception:  # noqa: BLE001
        pass


def _tendencias():
    hoje = date.today()
    dias = [(hoje - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
    prod = {}
    for d in dias:
        arq = WS_ANIME / f"_parceiro_{d.replace('-', '')}.log"
        try:
            with open(arq, "rb") as f:
                b = f.read()
            prod[d] = {"prontos": b.count(b"[auto|short] PRONTO"), "falhas": len(re.findall(rb"pipeline falhou|subprocesso falhou", b))}
        except OSError:
            prod[d] = {"prontos": 0, "falhas": 0}
        # 12/11 (auditoria): "prontos" contava só o log do PC1 (5/dia) — as pastas com a data do dia são de TODAS as
        # máquinas (202 em 11/11). "falhas" segue do PC1 (só ele grava); "prontos_pc1" guarda o número antigo.
        prod[d]["prontos_pc1"] = prod[d]["prontos"]
        n = _shorts_de_hoje(date.fromisoformat(d))
        if n is not None:
            prod[d]["prontos"] = n
    post = {}
    for x in _cache("postagens", 60, _postagens):
        d = x["quando"][:10]
        if d in prod and x["situacao"] == "no ar":
            post.setdefault(x["plataforma"], {})[d] = post.setdefault(x["plataforma"], {}).get(d, 0) + 1
    ultimo = {}
    for r in _ler_jsonl(HISTORICO):
        d = (r.get("ts") or "")[:10]
        if r.get("slug") and d:
            ultimo[(r["slug"], d)] = r
    # 09/11: ganho do dia = soma por canal (último do dia - último do dia anterior) só dos canais medidos nos DOIS dias.
    # Antes era total - total: canal que entrava/saía da medição virava salto falso de views.
    por_dia = {}
    for (slug, d), r in ultimo.items():
        por_dia.setdefault(d, {})[slug] = r
    ganho, ant = {}, None
    for d in sorted(por_dia):
        if ant and d in dias:
            comuns = set(por_dia[d]) & set(por_dia[ant])
            ganho[d] = {k: sum(max(0, por_dia[d][s].get(k, 0) - por_dia[ant][s].get(k, 0)) for s in comuns)
                        for k in ("views", "inscritos")}
            ganho[d]["canais"] = len(comuns)
        ant = d
    # 12/11 (auditoria): o historico.jsonl tem só 22 canais e o dia civil — o gráfico não batia com os cartões da Geral
    # (31 canais, views com o corte das 06h). Agora a MESMA série dos cartões (api_canais_views): por canal, valor do
    # dia - valor do dia anterior, somado; o historico.jsonl fica só pros dias que a série nova não cobre.
    try:
        series = api_canais_views({"dias": ["31"]})["canais"]
        novo = {}
        for c in series:
            s = c.get("serie") or []
            for (d0, i0, v0), (d1, i1, v1) in zip(s, s[1:]):
                if d1 in dias:
                    g = novo.setdefault(d1, {"views": 0, "inscritos": 0, "canais": 0})
                    g["views"] += max(0, v1 - v0)
                    g["inscritos"] += i1 - i0
                    g["canais"] += 1
        ganho.update(novo)
    except Exception:  # noqa: BLE001
        pass
    disco = [r for r in _ler_jsonl(DISCO_HIST)][-1000:]
    return {"dias": dias, "producao": prod, "postagens": post, "ganho": ganho, "disco": disco}


def api_tendencias(_params):
    return _cache("tendencias", 900, _tendencias)


# ─── saúde dos serviços ──────────────────────────────────────────────────────
def _saude():
    import urllib.request
    out = []

    def item(nome, ok, detalhe, quando=None, alerta=None):
        # alerta (com ok=True): acabando ou volta sozinho; aparece em amarelo e NÃO vira problema
        out.append({"nome": nome, "ok": ok, "detalhe": detalhe, "quando": quando, "alerta": alerta})
    # a rodada é de hora em hora (tarefa BackupDriveVideos); o .jsonl só registra quando algum arquivo foi pro Drive
    bk = _ler_jsonl(Path(r"D:\manhwa-react\logs\backup_drive.jsonl"))
    hoje_bk = [r for r in bk if (r.get("em") or "")[:10] == date.today().isoformat()]
    blog = Path(r"D:\manhwa-react\logs\backup_drive.log")
    ult = _cauda(blog, 1)
    idade_h = (time.time() - blog.stat().st_mtime) / 3600 if blog.exists() else None
    item("Backup no Drive", idade_h is not None and idade_h < 2.5 and not any(re.search(r"erro|falh", l, re.I) for l in ult),
         (ult[-1][:160] if ult else "sem log") + f" · hoje {len(hoje_bk)} arquivo(s) levados, "
         f"{sum(r.get('bytes', 0) for r in hoje_bk) / 1e9:.1f} GB liberados",
         datetime.fromtimestamp(blog.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if blog.exists() else None)
    procs = _procs()
    item("Vigia de segurança do trader", any("vigia_externo" in c or "VIGIA_SEGURANCA" in c for _m, c in procs.values()),
         "rodando" if any("vigia_externo" in c or "VIGIA_SEGURANCA" in c for _m, c in procs.values()) else "não está rodando (VIGIA_SEGURANCA.bat)")
    item("Vigia geral (VigiaVideos)", (time.time() - (BASE / "vigia_geral.log").stat().st_mtime) < 45 * 60 if (BASE / "vigia_geral.log").exists() else False,
         "última rodada " + datetime.fromtimestamp((BASE / "vigia_geral.log").stat().st_mtime).strftime("%H:%M") if (BASE / "vigia_geral.log").exists() else "sem log")
    try:
        cfg = _ler(Path(r"D:\hipercool-videos\secrets\claude_proxy.json"))
        req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/v1/models", headers={"Authorization": "Bearer " + cfg["auth_token"]})
        n = len(json.loads(urllib.request.urlopen(req, timeout=15).read()).get("data") or [])
        item("Gateway de IA (OmniRoute, VPS 157)", n > 0, f"{n} modelos no catálogo")
    except Exception as e:  # noqa: BLE001
        item("Gateway de IA (OmniRoute, VPS 157)", False, f"não respondeu ({type(e).__name__})")
    try:
        sys.path.insert(0, str(RECAPD / "bin"))
        import anime_worker_client
        on = anime_worker_client.is_online("100.125.7.77", 8772, timeout=8)
        import controlador as _ct
        ocupado = not on and _ct._porta_8772_pc2()  # atende 1 por vez: rodando anime não responde o /health
        item("Worker do anime no PC2 (8772)", on or ocupado, "no ar" if on else "ocupado rodando um anime longo" if ocupado
             else "fora do ar: o controlador tenta religar a cada rodada")
    except Exception as e:  # noqa: BLE001
        item("Worker do anime no PC2 (8772)", False, f"não deu pra conferir ({type(e).__name__})")
    import controlador
    m2 = (controlador._ler_estado().get("medidas") or {}).get("pc2") or {}
    item("PC2 (ssh)", m2.get("cpu") is not None, m2.get("motivo") or "sem medida na última rodada")
    md = (controlador._ler_estado().get("medidas") or {}).get("desktop") or {}
    item("Desktop / PC3 (ssh)", md.get("cpu") is not None,
         (f"{'LIVRE' if md.get('ocioso') else 'ocupado'}: {md.get('motivo', 'sem medida')}"
          + (f" · CPU {md['cpu']}% RAM {md['ram_gb']} GB" if md.get("cpu") is not None else "")))
    yt = BASE / "ytdlp_vez.json"
    pausa_yt = (_ler(BASE / "ytdlp_pausa.json").get("ate") or 0) - time.time()  # 22/10: o vigia não chama mais o agente por isso
    item("yt-dlp (vez única)", True, ("último uso " + datetime.fromtimestamp(yt.stat().st_mtime).strftime("%d/%m %H:%M")
                                      if yt.exists() else "sem registro")
         + (f" · EM PAUSA por mais {pausa_yt / 60:.0f} min: o YouTube está barrando o IP de casa e os Shorts esperam "
            "(a pausa dobra sozinha se o bloqueio voltar)" if pausa_yt > 0 else ""),
         alerta="IP barrado" if pausa_yt > 0 else None)

    # ── 22/10: o que pode ACABAR ou travar. Só medida real: item com ok=false vira "problema" no painel ──
    import shutil
    import subprocess as _sp
    import urllib.request as _ur
    _sj = getattr(_sp, "CREATE_NO_WINDOW", 0)
    sec = Path(r"D:\hipercool-videos\secrets")
    for drive, nome in (("D:\\", "Disco D:"), ("C:\\", "Disco C:")):
        try:
            t, _u, f = shutil.disk_usage(drive)
            item(nome, f / 1e9 > 5, f"{f / 1e9:.1f} GB livres ({f / t * 100:.0f}%)" + (": limpar já" if f / 1e9 < 3 else ""))
        except OSError:
            item(nome, False, "não leu o disco")
    try:  # gemini_estado.json: cada chave tem "ate" = em pausa (limite/erro) até essa hora
        ge = _ler(sec / "gemini_estado.json")
        gk = _ler(sec / "gemini_keys.json", [])
        n_g = len(gk if isinstance(gk, list) else gk.get("keys") or [])
        pausa = sum(1 for v in ge.values() if isinstance(v, dict) and (v.get("ate") or 0) > time.time())
        item("Gemini: chaves livres agora", n_g - pausa > 0, f"{max(0, n_g - pausa)} de {n_g} livres; {pausa} em pausa (limite ou erro)")
    except Exception as e:  # noqa: BLE001
        item("Gemini: chaves livres agora", False, f"não leu o estado ({type(e).__name__})")
    try:  # Webshare (Groq e geradores sempre pelo proxy): 2 proxies sorteados tentam uma página de 204 bytes
        import random
        prx = [l.strip() for l in (sec / "proxies.txt").read_text(encoding="utf-8").splitlines()
               if l.strip().startswith("http")]
        ok_p = 0
        for u in random.sample(prx, min(2, len(prx))):
            try:
                op = _ur.build_opener(_ur.ProxyHandler({"http": u, "https": u}))
                ok_p += op.open("https://www.google.com/generate_204", timeout=10).status == 204
            except Exception:  # noqa: BLE001
                pass
        item("Proxies Webshare", ok_p > 0, f"{ok_p} de 2 proxies sorteados responderam ({len(prx)} na lista)")
    except Exception as e:  # noqa: BLE001
        item("Proxies Webshare", False, f"não testou ({type(e).__name__})")
    try:  # parceiro_diario grava a conta que bateu "limite diário de envios" do Studio (pausa até a meia-noite de lá)
        lim = _ler(RECAPD / "workspace" / "anime" / ".limite_diario.json")
        agora_tz = datetime.now().astimezone()
        presas = sorted(k for k, v in lim.items() if isinstance(v, dict) and v.get("ate")
                        and datetime.fromisoformat(v["ate"]) > agora_tz)
        item("YouTube: contas no limite diário de envio", not presas,
             f"{len(presas)} bateram o limite diário do YouTube e esperam até a meia-noite de lá: {', '.join(presas)}. "
             "As contas são verificadas; o teto diário sobe com a idade/confiança do canal. Nada a fazer: o envio volta "
             "sozinho amanhã (a rampa de uploads/dia já acompanha)." if presas else "nenhuma")
    except Exception as e:  # noqa: BLE001
        item("YouTube: contas no limite diário de envio", False, f"não leu ({type(e).__name__})")
    try:  # capa por IA (Cloudflare/Pollinations): o filtro recusa e o Short sai sem capa
        arq = WS_ANIME / f"_parceiro_{date.today():%Y%m%d}.log"
        b = arq.read_bytes() if arq.exists() else b""
        sem = b.count("capa IA: todas as tentativas reprovadas".encode())
        com = b.count(b"capa IA: capa.jpg") + b.count(b"capa IA: imagem pela reserva")
        item("Capas por IA hoje", sem <= max(2, com), f"{com} com capa, {sem} sem capa (gerador recusou tudo)"
             if com or sem else "nenhuma tentativa hoje ainda")
    except Exception as e:  # noqa: BLE001
        item("Capas por IA hoje", False, f"não leu o log ({type(e).__name__})")

    def _drive():
        import controlador
        r = _sp.run([str(controlador.RCLONE), "about", "manhwa-drive:", "--json"], capture_output=True, text=True,
                    timeout=60, creationflags=_sj)
        return json.loads(r.stdout)
    try:  # espaço do Drive do backup (1 consulta por hora)
        d = _cache("saude_drive", 3600, _drive)
        livre, total = d.get("free"), d.get("total")
        item("Google Drive do backup", livre is None or livre > 50e9,
             (f"{livre / 1e9:.0f} GB livres de {total / 1e9:.0f} GB" if livre is not None and total else "sem limite informado")
             + (f"; lixeira {d['trashed'] / 1e9:.1f} GB" if d.get("trashed") else ""))
    except Exception as e:  # noqa: BLE001
        item("Google Drive do backup", False, f"rclone about falhou ({type(e).__name__}): reautorizar o manhwa-drive:?")
    try:  # tarefas que fazem a produção/postagem: faltando, desabilitada ou sem rodar há mais de 26 h
        esperadas = ("ControladorVideos", "PainelVideos", "VigiaVideos", "PostadorDeVideos", "BackupDriveVideos",
                     "ParceiroKaijinre-Postagem", "HipercoolPostagem", "HipercoolPC2", "MSEnergy_PostarInsta",
                     "MSEnergy_PostarTikTok", "TikTokRodadaExtra", "ManhwaReact-Rede", "ManhwaReact-Lote", "VozClonadaVigia")
        ps = ("foreach($x in @(" + ",".join(f"'{t}'" for t in esperadas) + ")){ $t=Get-ScheduledTask -TaskName $x "
              "-ErrorAction SilentlyContinue; if(-not $t){\"$x|FALTA||\"; continue}; $i=Get-ScheduledTaskInfo -TaskName $x; "
              "\"$x|$($t.State)|$($i.LastTaskResult)|$($i.LastRunTime.ToString('yyyy-MM-dd HH:mm'))\" }")
        r = _sp.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=150,
                    creationflags=_sj, encoding="utf-8", errors="replace")
        ruins, resultado = [], []
        for linha in (r.stdout or "").splitlines():
            p = linha.strip().split("|")
            if len(p) != 4:
                continue
            nome, estado, res, quando = p
            if estado == "FALTA":
                ruins.append(f"{nome} não existe")
            elif estado == "Disabled":
                ruins.append(f"{nome} desabilitada")
            elif quando and quando[:4] > "2000" and datetime.now() - datetime.strptime(quando, "%Y-%m-%d %H:%M") > timedelta(hours=26):
                ruins.append(f"{nome} sem rodar desde {quando[5:]}")
            elif res not in ("0", "267009", "267011", "267014", "2147750687"):  # ok, rodando, nunca rodou, parada, já rodando
                resultado.append(f"{nome}={res}")
        lidas = sum(1 for l in (r.stdout or "").splitlines() if l.count("|") == 3)
        item("Tarefas agendadas", lidas == len(esperadas) and not ruins,
             ("; ".join(ruins) if ruins else f"as {lidas} da produção/postagem existem e rodaram nas últimas 26 h")
             + (f" | último código diferente de 0: {', '.join(resultado)}" if resultado else ""))
    except _sp.TimeoutExpired:  # PC ocupado: é a medida que falhou, não as tarefas (22/10 10:20 virou problema falso)
        item("Tarefas agendadas", True, "não conferiu agora: o PowerShell passou de 150 s (PC ocupado); tenta de novo "
             "na próxima rodada", alerta="sem medida")
    except Exception as e:  # noqa: BLE001
        item("Tarefas agendadas", False, f"não conferiu ({type(e).__name__})")

    try:  # Opus 4.6 dos agentes: o MonitorOpus (D:\monitor_opus.py, 10 em 10 min) lê a cota no OmniRoute e prevê a volta
        mo = Path(r"D:\opus_monitor.json")
        est_o = _ler(mo)
        idade_m = (time.time() - mo.stat().st_mtime) / 60 if mo.exists() else None
        if idade_m is None or idade_m > 40:
            item("IA dos agentes: Opus 4.6 (Antigravity)", False,
                 f"monitor parado há {round(idade_m) if idade_m else '?'} min (tarefa MonitorOpus): sem previsão da cota")
        elif est_o.get("funcionando"):
            item("IA dos agentes: Opus 4.6 (Antigravity)", True, "com crédito (testado com texto real pelo monitor)")
        else:
            prev = est_o.get("previsao_avisada")
            item("IA dos agentes: Opus 4.6 (Antigravity)", True,
                 "sem crédito; volta " + (datetime.fromisoformat(prev).strftime("%d/%m %H:%M") if prev else "sem previsão")
                 + " (previsão do MonitorOpus, que avisa no Telegram)", alerta="sem crédito")
    except Exception as e:  # noqa: BLE001
        item("IA dos agentes: Opus 4.6 (Antigravity)", False, f"não leu o monitor ({type(e).__name__})")

    def _kiro():  # só leitura: o --simular conta as contas sem crédito no mês sem gravar nada
        import maquinas
        r = _sp.run([maquinas.SSH, "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "hermes-bloqueio",
                     "python3 /opt/omniroute/kiro_renovacao.py --simular; tail -60 /opt/omniroute/kiro_renovacao.log"],
                    capture_output=True, text=True, timeout=60, creationflags=_sj, encoding="utf-8", errors="replace")
        linhas = re.findall(r"(\d{4}-\d\d-\d\dT\d\d:\d\d) sem credito no mes=(\d+) ligadas com credito=(\d+)", r.stdout or "")
        if not linhas:
            raise RuntimeError((r.stderr or r.stdout or "sem saída").strip()[-120:])
        agora_k, sem_k, com_k = linhas[0][0], int(linhas[0][1]), int(linhas[0][2])  # 1ª linha = o --simular (agora)
        # ritmo: contas que esgotaram por dia nas últimas 72 h (o log só grava quando muda), mesmo mês
        t_ag = datetime.fromisoformat(agora_k)
        velhas = [(datetime.fromisoformat(t), int(s)) for t, s, _c in linhas[1:]
                  if t[:7] == agora_k[:7] and timedelta(hours=12) < t_ag - datetime.fromisoformat(t) < timedelta(hours=72)]
        ritmo = (sem_k - velhas[0][1]) / ((t_ag - velhas[0][0]).total_seconds() / 86400) if velhas else None
        return sem_k, com_k, ritmo
    try:  # Kiro (kr/claude-sonnet-4.5): IA do vigia geral e do aprendizado; crédito mensal, renova dia 1 00:00 UTC
        sem_k, com_k, ritmo = _cache("saude_kiro", 3600, _kiro)
        hoje_d = date.today()
        dias_virada = ((hoje_d.replace(day=28) + timedelta(days=4)).replace(day=1) - hoje_d).days
        dura = com_k / ritmo if ritmo and ritmo > 0 else None
        item("Kiro (IA do vigia e do aprendizado)", com_k > 0,
             f"{com_k} conta(s) com crédito, {sem_k} sem crédito no mês; renova dia 1 (daqui a {dias_virada} dia(s))"
             + (f"; gastando ~{ritmo:.0f} conta(s)/dia, acaba em ~{dura:.1f} dia(s)" if dura is not None else "")
             + ("" if com_k else ": até lá o vigia e o aprendizado ficam sem a IA"),
             alerta="acaba antes do dia 1" if com_k and dura is not None and dura < dias_virada else None)
    except Exception as e:  # noqa: BLE001
        item("Kiro (IA do vigia e do aprendizado)", False, f"não leu a cota na VPS 157 ({type(e).__name__}: {str(e)[:80]})")
    try:  # Veo (Google Flow): o gerador marca a conta EXHAUSTED até 00:05 quando o crédito do dia acaba
        nomes = re.findall(r'"session":\s*"([^"]+)"', Path(r"D:\veo\beta\contas.py").read_text(encoding="utf-8"))
        st = _ler(Path(r"D:\veo\beta\logs\sessoes_status.json"))
        agora_s = datetime.now().isoformat(timespec="seconds")
        sem_v = [n for n in nomes if (st.get(n) or {}).get("status") == "EXHAUSTED"
                 and ((st.get(n) or {}).get("cooldown_until") or "") > agora_s]
        pausa_v = [n for n in nomes if n not in sem_v and ((st.get(n) or {}).get("cooldown_until") or "") > agora_s]
        livres = len(nomes) - len(sem_v) - len(pausa_v)
        item("Veo (Google Flow): contas com crédito hoje", livres > 0,
             f"{livres} de {len(nomes)} com crédito; {len(sem_v)} sem crédito até a meia-noite"
             + (f", {len(pausa_v)} em pausa por falha" if pausa_v else "")
             + ("" if livres else ": nenhum Veo novo hoje (MS Energy e reserva do TikTok usam o estoque)"),
             alerta="acabando" if livres and len(sem_v) * 2 >= len(nomes) else None)
    except Exception as e:  # noqa: BLE001
        item("Veo (Google Flow): contas com crédito hoje", False, f"não leu o estado do gerador ({type(e).__name__})")
    try:  # TikTok: o postador não sabe de ban; conta deslogada ou sem postar há 48 h enquanto as outras postam = suspeita
        post = Path(r"D:\postador-de-videos")
        cts = [c for c in (_ler(post / "config" / "reuso_plataformas.json").get("tiktok") or {}).get("contas", {})
               if not c.startswith("_")]
        ult_t = {}
        for r in _ler(post / "logs" / "tiktok_auto_posted.json", []):
            a, t = r.get("account"), r.get("timestamp") or ""
            if a and t > ult_t.get(a, ""):
                ult_t[a] = t
        paradas = sorted(c for c in cts if ult_t.get(c, "") < (datetime.now() - timedelta(hours=48)).isoformat())
        postaram = sum(1 for c in cts if ult_t.get(c, "") >= (datetime.now() - timedelta(hours=26)).isoformat())
        deslog = set()
        for d in (date.today() - timedelta(days=1), date.today()):
            arq = post / "logs" / f"tiktok_{d:%Y%m%d}.log"
            if arq.exists():
                deslog |= set(re.findall(r"DESLOGADO: (\S+)", arq.read_text(encoding="utf-8", errors="replace")))
        partes = [f"{postaram} de {len(cts)} postaram nas últimas 26 h"]
        if deslog:
            partes.append("deslogada: " + ", ".join(sorted(deslog)) + " (cofre.py logar <conta> e entrar no tiktok.com)")
        so_paradas = [c for c in paradas if c not in deslog]  # a deslogada já explica por que parou
        if so_paradas:
            partes.append("sem postar há 48 h: " + ", ".join(so_paradas) + " (abrir o perfil: aviso de ban ou de login?)")
        item("TikTok: contas paradas ou deslogadas", not deslog and not paradas, "; ".join(partes))
    except Exception as e:  # noqa: BLE001
        item("TikTok: contas paradas ou deslogadas", False, f"não leu o registro do postador ({type(e).__name__})")
    try:  # P04 (22/10): checagem diária (04-08 h) do login de cada canal pelo navegador (checar_canais_diario.py)
        cc = _ler(Path(r"D:\postador-de-videos\logs\checar_canais.json"))
        canais_cc = cc.get("canais") or {}
        ruins_cc = {k: v for k, v in canais_cc.items() if v.get("status") != "ok"}
        fim_cc = cc.get("fim")
        velho = not fim_cc or datetime.now() - datetime.fromisoformat(fim_cc) > timedelta(hours=30) or not cc.get("completa")
        if ruins_cc:
            item("YouTube: login dos canais (checagem diária)", False,
                 "; ".join(f"{k}: {v.get('status')} ({str(v.get('detalhe'))[:70]})" for k, v in sorted(ruins_cc.items()))
                 + " — logar de novo: python D:\\logins-google\\cofre.py logar <conta>", fim_cc)
        else:
            item("YouTube: login dos canais (checagem diária)", True,
                 f"os {len(canais_cc)} canais abrem o Studio logados" if not velho else
                 "sem rodada completa nas últimas 30 h (a checagem roda 1x por dia entre 04 e 08 h)",
                 fim_cc, alerta="sem rodada recente" if velho else None)
    except Exception as e:  # noqa: BLE001
        item("YouTube: login dos canais (checagem diária)", False, f"não leu o resultado ({type(e).__name__})")

    return out


def api_saude(_params):
    return {"servicos": _cache("saude", 180, _saude)}


# ─── "o que está errado agora" ───────────────────────────────────────────────
def _rodada_ctrl():
    """Linhas da última rodada do controlador (do último cabeçalho 'pc1: ... | pc2: ...' até o fim)."""
    ls = _cauda(BASE / "logs" / f"controlador_{date.today():%Y%m%d}.log", 60)
    ini = max((i for i, l in enumerate(ls) if re.search(r"\] pc1: .*\| pc2: ", l)), default=None)
    return ls[ini:] if ini is not None else []


def _problema(lista, pid, nivel, titulo, detalhe, projeto="geral", desde=None, fonte=None, links=None, contexto=None,
              so_dono=False):
    """so_dono: só o dono resolve (login, verificação no Studio...): aparece direto e o vigia não gasta IA nele."""
    lista.append({"id": pid, "nivel": nivel, "titulo": titulo, "detalhe": detalhe, "projeto": projeto, "desde": desde,
                  "fonte": fonte, "links": links or [], "so_dono": so_dono, "contexto": contexto or f"{titulo}\n{detalhe}"
                  + (f"\nLog: {fonte}" if fonte else "")})


def _sessoes_google(p, agora):
    """Contas do cofre com o login do Google morto (dono 24/10: 'só quero saber quais estão desconectadas, em
    avisos'). Só LÊ o cadastro: quem testa de verdade é o `cofre.py checar` da tarefa CofreChecar (1x/dia)."""
    try:
        contas = json.loads(Path(r"D:\logins-google\cofre\contas.json").read_text(encoding="utf-8"))["contas"]
    except (OSError, ValueError, KeyError):
        return
    mortas, ultima = [], ""
    for email, e in contas.items():
        if e.get("tipo") == "instagram" or "@" not in email:
            continue
        ultima = max(ultima, e.get("checado") or "")
        if e.get("google") and e["google"] != "vivo":
            ch = e.get("checado") or ""
            mortas.append(f"{email.split('@')[0]} ({e['google']}, visto {ch[8:10]}/{ch[5:7]})")
    if mortas:
        _problema(p, "sessoes-google", "aviso", f"{len(mortas)} conta(s) Google desconectada(s) no cofre",
                  "; ".join(mortas) + " — pra entrar de novo: python D:\\logins-google\\cofre.py logar <conta>",
                  so_dono=True)
    if ultima and (agora - datetime.fromisoformat(ultima)).total_seconds() > 36 * 3600:
        _problema(p, "sessoes-checagem", "aviso", "Checagem dos logins do cofre atrasada",
                  f"última checagem {ultima.replace('T', ' ')} (a tarefa CofreChecar roda 1x/dia)")


def _problemas():
    import shutil
    import controlador
    p, agora = [], datetime.now()
    est = controlador._ler_estado()
    ult = max(filter(None, (est.get("ultima_rodada"), est.get("inicio_rodada"))), default=None)  # 06/11: início também
    idade = (agora - datetime.fromisoformat(ult)).total_seconds() / 60 if ult else None
    log_ctrl = str(BASE / "logs" / f"controlador_{date.today():%Y%m%d}.log")
    if idade is None or idade > 25:
        _problema(p, "controlador", "erro", "Controlador parado",
                  f"última rodada há {round(idade) if idade else '?'} min (roda a cada 10): nada novo é produzido",
                  desde=ult, fonte=log_ctrl)
    try:  # 12/11 (dona: "avisar de todas as formas" se a rota do Flow quebrar) — vigia_flow.py
        vf = json.loads(Path(r"D:\veo\beta\logs\vigia_flow.json").read_text(encoding="utf-8"))
        for tipo, r in (vf.get("rotas") or {}).items():
            if r.get("estado") in ("desligado", "teste"):
                _problema(p, f"flow-rota-{tipo}", "erro", f"Flow ({tipo}): rota SEM NAVEGADOR quebrou — indo pela tela",
                          f"desde {str(r.get('desde', '?'))[:16]}; a produção segue pela tela; teste automático a cada 60 min. "
                          f"Último erro: {(r.get('evidencia') or ['?'])[-1][:200]} — provável mudança na interface do Flow "
                          "(refazer o pedido: projeto-navegador-sem-navegador\\docs\\FLOW_AGENTE_NOVO_12NOV.md)",
                          desde=r.get("desde"), fonte=r"D:\veo\beta\logs\vigia_flow.log")
        u2 = vf.get("ultimas_2h") or {}
        if u2 and not u2.get("http_ok") and not u2.get("tela_ok"):
            _problema(p, "flow-parado", "erro", "Flow PAROU nas duas rotas (2 h sem imagem/vídeo)",
                      "nem a rota sem navegador nem a tela entregaram nada — conta/crédito/login ou mudança grande no Flow",
                      fonte=r"D:\veo\beta\logs\vigia_flow.log")
    except (OSError, ValueError):
        pass
    try:  # 29/10 (dona): conta do like/comentário deslogada no telão = problema vermelho no painel (vitrine._avisar_deslogado)
        # 12/11 (dona desligou o like do telão — medido: não muda as views) — sem like ligado não é mais problema
        if os.environ.get("TELAO_LIKE", "0") != "1":
            raise ValueError("like desligado")
        dl = json.loads((BASE / "estado" / "telao_deslogado.json").read_text(encoding="utf-8"))
        # 06/11 (dona: "nem estava deslogada"): o sinal de 01/11 ficou 5 dias porque os likes seguintes deram TIMEOUT
        # (não "ok") e nunca apagaram. Sem 401/403 novo há 6 h = vencido.
        if (datetime.now() - datetime.fromisoformat(dl.get("em") or "2000-01-01")).total_seconds() > 6 * 3600:
            raise ValueError("vencido")
        _problema(p, f"telao-deslogado-{dl.get('maquina')}", "erro", f"Telão {str(dl.get('maquina', '')).upper()}: conta do like DESLOGADA",
                  f"{dl.get('seguidos', 1)} vídeo(s) exibido(s) sem like ({dl.get('resultado')}). Resolver: {dl.get('como_resolver')}",
                  desde=dl.get("desde"), fonte=str(BASE / "logs" / "vitrine.log"))
    except (OSError, ValueError):
        pass
    rodada = _rodada_ctrl()
    ag, med = est.get("agora") or {}, est.get("medidas") or {}
    for pc in ("pc1", "pc2"):
        if not ag.get(pc) and idade is not None and idade <= 25:
            rx = r"PC2|pc2|parceiro: PC2" if pc == "pc2" else r"pc1:|PC1|cortes_pc1|hipercool_faltantes"
            motivos = [re.sub(r"^\[[^\]]+\]\s*", "", l) for l in rodada[1:] if re.search(rx, l)
                       and not re.search(r"bin já igual|DISPAROU", l)]
            _problema(p, f"parado-{pc}", "aviso", f"{pc.upper()} sem trabalho agora",
                      " · ".join(motivos[:4]) or (med.get(pc) or {}).get("motivo") or "controlador não achou o que mandar",
                      fonte=log_ctrl)
    # disparo que termina sem fazer nada (21/10: hipercool_pc2 16x em vão com o pc2-trazer travado)
    rapidos = {}
    for l in _cauda(BASE / "logs" / f"controlador_{date.today():%Y%m%d}.log", 400):
        m = re.match(r"\[\d\d/\d\d (\d\d:\d\d):\d\d\]\s+terminou: (.+) \((\d+) min\)", l)
        if m and int(m.group(3)) <= 2:
            h = datetime.combine(agora.date(), datetime.strptime(m.group(1), "%H:%M").time())
            if (agora - h).total_seconds() < 90 * 60:
                rapidos.setdefault(m.group(2), []).append(m.group(1))
    for nome, horas in rapidos.items():
        if len(horas) >= 3:
            _problema(p, f"rapido-{nome[:30]}", "erro", f"Trabalho que termina sem fazer nada: {nome}",
                      f"{len(horas)} vezes em 90 min terminou em até 2 min ({', '.join(horas[-4:])})", fonte=log_ctrl)
    fp = _cauda(HIPER_LOGS / "fila_pc2.log", 4)
    if len(fp) >= 3 and all("outro pc2 rodando" in l for l in fp[-3:]):
        pid = re.search(r"pid (\d+)", fp[-1])
        _problema(p, "pc2-trava-hipercool", "erro", "Línguas do hipercool no PC2 bloqueadas",
                  f"3 rodadas seguidas com 'outro pc2 rodando' (pid {pid.group(1) if pid else '?'}): o pc2-trazer pode "
                  "ter travado", projeto="hipercool", fonte=str(HIPER_LOGS / "fila_pc2.log"))
    for disco, minimo in (("D:\\", 10), ("C:\\", 5)):
        try:
            livre = shutil.disk_usage(disco).free / 1e9
            if livre < minimo:
                _problema(p, f"disco-{disco[0]}", "erro" if livre < minimo / 2 else "aviso", f"Disco {disco[:2]} quase cheio",
                          f"{livre:.1f} GB livres (mínimo {minimo}): a produção para quando encher")
        except OSError:
            pass
    d2 = (med.get("pc2") or {}).get("disco_gb")
    if isinstance(d2, (int, float)) and d2 < 5:
        _problema(p, "disco-pc2", "aviso", "Disco do PC2 quase cheio", f"{d2} GB livres no C: do PC2")
    for t in _pronto("tarefas") or []:
        if not t["ok"] and t["estado"] != "desligada":
            _problema(p, f"tarefa-{t['nome']}", "aviso", f"Tarefa {t['nome']}: {t['resultado']}",
                      f"última vez {t['ultima'] or '?'} · comando: {t['acao'][:160]}", desde=t["ultima"],
                      contexto=f"A tarefa agendada {t['nome']} terminou com {t['resultado']} ({t['codigo']}) em "
                               f"{t['ultima']}. Comando: {t['acao']}")
    if agora.hour >= 12:
        vazios = [c["nome"] for c in (_pronto("canais") or []) if c.get("vazio_hoje") and not c.get("bloqueado")]
        if vazios:
            _problema(p, "canais-vazios", "erro" if agora.hour >= 18 else "aviso",
                      f"{len(vazios)} canal(is) sem post hoje", ", ".join(vazios[:12]), projeto="cortes",
                      contexto="Canais sem nenhuma postagem hoje (regra do dono: nenhum canal fica 1 dia sem postar): "
                               + ", ".join(vazios))
    prod = _pronto("producao") or {}
    cn = (prod.get("cortes") or {}).get("numeros") or {}
    if cn.get("mudos_hoje"):
        _problema(p, "mudos", "erro", f"{cn['mudos_hoje']} Short(s) com narração muda hoje",
                  "nível da narração abaixo de -23 LUFS (a trava segura, mas a causa precisa ser vista)", projeto="cortes")
    falhas = [f for f in (prod.get("cortes") or {}).get("feitos_hoje") or [] if str(f.get("resultado", "")).startswith("falhou")]
    if len(falhas) >= 3:
        causas = {}
        for f in falhas:
            causas[f["resultado"][:90]] = causas.get(f["resultado"][:90], 0) + 1
        _problema(p, "falhas-cortes", "aviso", f"{len(falhas)} Shorts falharam hoje no PC1",
                  " · ".join(f"{n}x {c}" for c, n in sorted(causas.items(), key=lambda x: -x[1])[:3]), projeto="cortes",
                  fonte=str(WS_ANIME / f"_parceiro_{date.today():%Y%m%d}.log"))
    for arq in (BASE / "estado" / "esperando").glob("*.json"):
        d = _ler(arq)
        if d.get("desde") and time.time() - d["desde"] > 3 * 3600:
            _problema(p, f"fila-{arq.stem}", "aviso", "Render esperando a vez há muito tempo",
                      f"{d.get('projeto')} ({d.get('rotulo')}) esperando há {(time.time() - d['desde']) / 3600:.1f} h")
    for s in _pronto("saude") or []:
        if not s["ok"]:
            _problema(p, f"saude-{s['nome'][:30]}", "aviso", s["nome"], s["detalhe"],
                      projeto="cortes" if "anime" in s["nome"] else "geral")
    _sessoes_google(p, agora)
    tt = _contas_tiktok()
    mortas = {k: v for k, v in tt["contas"].items() if v.get("morta")}
    try:  # 12/11: as já pausadas no reuso_plataformas não gastam vídeo — só a morta AINDA ativa é erro
        _reuso = json.loads(Path(r"D:\postador-de-videos\config\reuso_plataformas.json").read_text(encoding="utf-8"))
        _pausadas = {k for k, v in (_reuso.get("tiktok", {}).get("contas") or {}).items()
                     if isinstance(v, dict) and v.get("pausada")}
    except (OSError, ValueError):
        _pausadas = set()
    if mortas and set(mortas) <= _pausadas:
        _problema(p, "tiktok-mortas", "aviso", f"{len(mortas)} conta(s) do TikTok mortas — já pausadas (não gastam vídeo)",
                  ", ".join(sorted(mortas)) + f". Lido em {(tt['quando'] or '?').replace('T', ' ')}", projeto="tiktok")
        mortas = {}
    mortas = {k: v for k, v in mortas.items() if k not in _pausadas}
    if mortas:
        _problema(p, "tiktok-mortas", "erro", f"{len(mortas)} conta(s) do TikTok MORTA(S): zero views em todos os vídeos",
                  "; ".join(f"{k} (@{v['arroba']}, {v['videos']} vídeos, {v['seguidores']} seguidores)"
                            for k, v in mortas.items())
                  + f" — o postador continua gastando vídeo nelas. Lido em {(tt['quando'] or '?').replace('T', ' ')}",
                  projeto="tiktok", so_dono=True,
                  links=[{"t": "@" + v["arroba"], "u": f"https://www.tiktok.com/@{v['arroba']}"} for v in mortas.values()])
    bots =[b for b in (_pronto("bots") or []) if b.get("iniciado") is False]
    if bots:
        _problema(p, "bots", "aviso", f"{len(bots)} bot(s) do Telegram sem 'Iniciar'",
                  "Abra cada link e aperte Iniciar; até lá os avisos deles caem no bot principal.",
                  links=[{"t": "@" + (b["usuario"] or b["chave"]), "u": b["link"]} for b in bots if b.get("link")])
    for l in reversed(_cauda(BASE / "vigia_geral.log", 120, filtro=r"agente terminou: REVISAR")):
        m = re.match(r"\[?(\d{4}-\d\d-\d\d[ T]\d\d:\d\d)", l)
        if m and (agora - datetime.fromisoformat(m.group(1).replace(" ", "T"))).total_seconds() < 6 * 3600:
            _problema(p, "vigia-revisar", "aviso", "O vigia pediu revisão", l[-260:], fonte=str(BASE / "VIGIA_DIARIO.md"))
        break
    p.sort(key=lambda x: x["nivel"] != "erro")
    return p


REGISTRO_ERROS = BASE / "estado" / "problemas_registro.json"
ESPERA_VIGIA_MIN = 45     # problema sem tentativa do vigia por mais que isso = aparece pro dono
CONFERINDO_H = 6          # depois do "CONSERTEI" o problema pode demorar a sumir (tarefa só roda de novo na hora dela)
_TRAVA_REG = threading.Lock()


def _situacao(x, reg, agora):
    """Dono 24/10: 'essas tarefas já devem se consertar só pelo vigia; só deve aparecer as que não consertar'."""
    if x.get("so_dono") or re.search(r"deslogad|desconectad|verifica", (x.get("titulo") or "") + (x.get("detalhe") or ""), re.I):
        return "precisa", "só você resolve (login/verificação): o vigia não mexe em conta"
    ia = x.get("ia") or {}
    fim = None
    try:
        j = __import__("painel_ia").ler(ia.get("id") or "") or {}
        fim = j.get("fim")
    except Exception:  # noqa: BLE001
        pass
    if ia.get("status") in ("fila", "rodando"):
        return "consertando", "o vigia está consertando"
    if ia.get("status_ia") == "CONSERTEI" and not ia.get("desfeito_em"):
        h = (agora - datetime.fromisoformat(fim)).total_seconds() / 3600 if fim else 0
        if h < CONFERINDO_H:
            return "conferindo", f"o vigia consertou às {str(fim or '')[11:16]} — esperando a próxima rodada confirmar"
        return "precisa", f"o vigia disse que consertou há {h:.0f} h, mas o problema continua"
    if ia:
        motivo = {"REVISAR": "o vigia não conseguiu sozinho", "OK": "o vigia achou que não é conserto de código",
                  "PROPOSTA": "o conserto proposto não foi aplicado"}.get(ia.get("status_ia"), f"tentativa do vigia: {ia.get('status')}")
        return "precisa", motivo
    primeiro = (reg.get(x["id"]) or {}).get("primeiro")
    if primeiro and (agora - datetime.fromisoformat(primeiro)).total_seconds() / 60 < ESPERA_VIGIA_MIN:
        return "fila_vigia", "na fila do vigia (ele tenta consertar a cada 20 min)"
    return "precisa", "o vigia ainda não tentou consertar"


def _registrar_problemas(probs, parcial):
    """Registro de TODOS os erros (dono 24/10: 'no final um log de erros, conta todos mesmo os consertados')."""
    agora = datetime.now()
    with _TRAVA_REG:
        reg = _ler(REGISTRO_ERROS, {}) or {}
        atuais = set()
        for x in probs:
            atuais.add(x["id"])
            r = reg.get(x["id"])
            if not r or not r.get("aberto"):
                r = {"titulo": x["titulo"], "projeto": x.get("projeto"), "nivel": x.get("nivel"),
                     "primeiro": agora.isoformat(timespec="seconds"), "aberto": True, "vezes": (r or {}).get("vezes", 0) + 1,
                     "ia": (r or {}).get("ia", [])}
                reg[x["id"]] = r
            r.update(titulo=x["titulo"], detalhe=(x.get("detalhe") or "")[:300], ultimo=agora.isoformat(timespec="seconds"))
            ia = x.get("ia") or {}
            if ia.get("id") and ia["id"] not in r["ia"]:
                r["ia"].append(ia["id"])
            if ia.get("status_ia"):
                r["ia_status"] = ia["status_ia"]
            x["situacao"], x["situacao_txt"] = _situacao(x, reg, agora)
        if not parcial:
            for pid, r in reg.items():
                if r.get("aberto") and pid not in atuais:
                    r.update(aberto=False, fechado_em=agora.isoformat(timespec="seconds"),
                             como="consertado pelo vigia" if r.get("ia_status") == "CONSERTEI" else
                             "resolvido depois da tentativa do vigia" if r.get("ia") else "sumiu sozinho")
        # guarda 30 dias
        corte = (agora - timedelta(days=30)).isoformat()
        reg = {k: v for k, v in reg.items() if v.get("aberto") or (v.get("fechado_em") or "") >= corte}
        REGISTRO_ERROS.parent.mkdir(exist_ok=True)
        tmp = REGISTRO_ERROS.with_suffix(".tmp")
        tmp.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(REGISTRO_ERROS)
    return probs


def api_problemas(_params):
    # logo depois de ligar o painel as checagens lentas (tarefas, bots, saúde) ainda não terminaram: a tela avisa
    parcial = any(_pronto(k) is None for k in ("tarefas", "bots", "saude", "canais", "producao"))
    if parcial:
        _CACHE.pop("problemas", None)
    probs = _registrar_problemas([dict(x) for x in _ia_por_problema(_cache("problemas", 30, _problemas))], parcial)
    return {"problemas": probs, "em": datetime.now().strftime("%H:%M:%S"), "parcial": parcial}


def api_erros(_params):
    """Registro de erros dos últimos 30 dias (abertos e consertados) + contagem."""
    reg = _ler(REGISTRO_ERROS, {}) or {}
    linhas = [{"id": k, **v, "ia": ", ".join(v.get("ia") or [])} for k, v in reg.items()]
    linhas.sort(key=lambda r: r.get("primeiro") or "", reverse=True)
    conta = {"total": len(linhas), "abertos": sum(r.get("aberto", False) for r in linhas),
             "vigia": sum(r.get("como") == "consertado pelo vigia" for r in linhas),
             "sozinho": sum(r.get("como") in ("sumiu sozinho", "resolvido depois da tentativa do vigia") for r in linhas)}
    return {"conta": conta, "linhas": linhas}


# ─── liga/desliga ─────────────────────────────────────────────────────────────
PODE_ABRIR = [Path(r"D:\hipercool-materiais\animes recap\shorts"), Path(r"D:\hipercool-materiais\videos_voz_clonada"),
              Path(r"D:\hipercool-materiais\_postados"), Path(r"D:\ms-energy\videos"), Path(r"D:\hipercool-videos\workspace\videos")]


def _tela():
    """Frente K (dono 21/10): PCs fracos/tablets como TELA que toca sozinha cada vídeo que fica pronto. Lista os vídeos
    das últimas 48 h nas pastas de produção; arquivo mexido há menos de 90 s fica de fora (render ainda escrevendo)."""
    agora, out = time.time(), []
    fontes = [("Cortes", Path(r"D:\hipercool-materiais\animes recap\shorts"), ["*/video.mp4"]),
              ("Hipercool", Path(r"D:\hipercool-videos\workspace\videos"), ["*/cap*/*/censurado/*.mp4", "longo/*/*.mp4",
                                                                            "longo/*/*/*.mp4"]),
              ("MS Energy", Path(r"D:\ms-energy\videos"), ["*.mp4", "*/*.mp4"])]
    for origem, raiz, padroes in fontes:
        for pad in padroes:
            for p in raiz.glob(pad):
                try:
                    st = p.stat()
                except OSError:
                    continue
                if not 90 < agora - st.st_mtime < 48 * 3600 or st.st_size < 100_000:
                    continue
                pj = _ler(p.parent / "postar.json") if origem == "Cortes" else {}
                out.append({"caminho": str(p), "origem": origem, "quando": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                            "titulo": pj.get("titulo") or p.parent.name if origem == "Cortes" else p.stem,
                            "canal": pj.get("canal_postado") or pj.get("canal") or "", "mb": round(st.st_size / 1e6, 1)})
    out.sort(key=lambda x: x["quando"], reverse=True)
    return out[:40]


def api_tela(_params):
    return {"videos": _cache("tela", 60, _tela)}


def api_abrir(corpo):
    """Abre no PC o vídeo pronto (dono 21/10: "tem que ter a opção de abrir os vídeos já prontos"). Só arquivo de vídeo
    dentro das pastas de produção."""
    import os
    p = Path(str(corpo.get("caminho") or "")).resolve()
    if corpo.get("pasta"):  # "abrir pasta" no Explorer (a pasta do vídeo)
        p = p.parent if p.suffix else p
    if not any(p.is_relative_to(b.resolve()) for b in VIDEO_OK) or not (p.is_dir() or p.suffix.lower() in TIPOS):
        raise ValueError("só vídeo/pasta das pastas de produção")
    if not p.exists():
        raise ValueError("arquivo não existe mais (pode ter ido pro Drive)")
    os.startfile(str(p))
    return {"aberto": str(p)}


def _refletir_controle(controle):
    """O _cache devolve o valor velho na hora: sem isto, depois do clique a tela redesenhava a chave na posição antiga
    (por até 30 s) e o dono podia clicar de novo e desfazer."""
    g = _CACHE.get("geral")
    if g and isinstance(g[1], dict):
        g[1]["controle"] = _controle_estado(controle)
    pr = _CACHE.get("producao")
    if pr and isinstance(pr[1], dict):
        for p in pr[1].values():
            for e, por in ((p.get("controle") or {}) if isinstance(p, dict) else {}).items():
                for proj in por:
                    por[proj] = dict(zip(("ligado", "motivo"), controle.ligado(proj, e)))


def api_controle_mudar(corpo):
    import controle
    projeto, etapa, ligar = corpo.get("projeto"), corpo.get("etapa"), corpo.get("ligado")
    if projeto not in controle.PROJETOS or etapa not in controle.ETAPAS or not isinstance(ligar, bool):
        raise ValueError("pedido inválido")
    controle.mudar(projeto, etapa, ligar, (corpo.get("motivo") or "pelo painel")[:200])
    ok, motivo = controle.ligado(projeto, etapa)
    _refletir_controle(controle)
    return {"projeto": projeto, "etapa": etapa, "ligado": ok, "motivo": motivo,
            "aviso": None if ok == ligar else f"continua {'ligado' if ok else 'desligado'}: {motivo}"}


def api_er(_params):
    """29/10 (Fable): aba 'Engenharia reversa' — prioridades da dona (canal/vídeo), resultados e contagens."""
    er = BASE / "engenharia_reversa"
    cfg = {}
    try:
        cfg = json.loads((BASE / "config" / "er_prioridades.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass

    def _n(p):
        try:
            return sum(1 for _ in (er / p).read_text(encoding="utf-8", errors="replace").splitlines())
        except OSError:
            return 0
    try:
        res = (er / "RESULTADOS_CONTINUO.md").read_text(encoding="utf-8", errors="replace")[-6000:]
    except OSError:
        res = ""
    try:
        prog = (er / "PROGRESSO.md").read_text(encoding="utf-8", errors="replace")[-3000:]
    except OSError:
        prog = ""
    try:
        logp = (er / "amostra.log").read_text(encoding="utf-8", errors="replace").splitlines()[-25:]
    except OSError:
        logp = []
    return {"itens": cfg.get("itens") or [], "medidas_parceiros": _n("medidas.jsonl"), "medidas_nossos": _n("medidas_nossos.jsonl"),
            "medidas_fontes": _n("medidas_fontes.jsonl"), "resultados": res, "progresso": prog, "log": logp}


def api_er_prioridade(corpo):
    sys.path.insert(0, str(BASE / "engenharia_reversa"))
    import continuo
    alvo = str(corpo.get("alvo") or "").strip()
    if not alvo or len(alvo) > 300:
        raise ValueError("informe a URL ou o @ do canal, ou a URL do vídeo")
    d = continuo.adicionar(alvo, corpo.get("tipo") or None)
    return {"ok": True, "itens": d["itens"]}


def api_nsn(params):
    """29/10 (Fable): aba 'Sem navegador' — saúde real dos serviços por HTTP (projeto-navegador-sem-navegador
    tools\\saude.py) + as últimas linhas do log, porque esse sistema não abre janela e ninguém veria cair."""
    raiz = Path(r"D:\projeto-navegador-sem-navegador")
    est = {}
    try:
        est = json.loads((raiz / "relatorios" / "saida" / "saude.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    n = int((params.get("linhas") or ["60"])[0])
    logs = {}
    for nome in ("saude.jsonl", "manter_cookies.jsonl"):
        try:
            linhas = (raiz / "logs" / nome).read_text(encoding="utf-8", errors="replace").splitlines()[-n:]
        except OSError:
            linhas = []
        logs[nome] = [json.loads(l) if l.startswith("{") else l for l in linhas if l.strip()][-n:] if linhas else []
    uso = []
    # uso em produção (29/10, D21–D23): Studio lido por HTTP (metricas_rede), Reel por HTTP no PC1 e nos notebooks
    # (instagram_auto.log), colheita de cookies nas máquinas (maquina_remota.log)
    # 29/10 (D30): Veo gerado por HTTP nas máquinas (maquina_remota.log "Flow por HTTP (perfil): ok chrome=N s")
    for nome, chave in (("metricas_rede.log", "por HTTP"), ("instagram_auto.log", "HTTP"), ("maquina_remota.log", "colher"),
                        ("maquina_remota.log", "Reel por HTTP"), ("maquina_remota.log", "Flow por HTTP")):
        try:
            linhas = (BASE.parent / "postador-de-videos" / "logs" / nome).read_text(encoding="utf-8", errors="replace").splitlines()[-600:]
            uso += [f"{nome.split('.')[0]}: {l}" for l in linhas if chave in l][-15:]
        except OSError:
            pass
    uso = uso[-40:]
    # 29/10 (D33): monitor de banimento + rampa dos tetos (tools\monitor_banimento.py, tarefa NSN_Banimento)
    try:
        ban = json.loads((raiz / "relatorios" / "saida" / "banimento.json").read_text(encoding="utf-8"))
        ban.pop("vistos", None)
        ban.pop("sinais_7d", None)
    except (OSError, ValueError):
        ban = {}
    return {"em": est.get("_em"), "resumo": est.get("_resumo") or {}, "servicos": {k: v for k, v in est.items() if not k.startswith("_")},
            "logs": logs, "uso_producao": uso, "banimento": ban}


def api_modelos_central(_params):
    """29/10 (Fable, D14): aba 'Modelos da IA' — botão Argon / Opus / os dois / auto do melhorador central, estado e a
    última bancada (qual Argon chega mais perto do Opus 5.5)."""
    import melhorador_central as mc
    pedido, vigor, motivo, conj = mc.modo_modelos()
    est = mc._ler(mc.ESTADO, {})
    banc = mc._ler(mc.PASTA / "bancada" / "ultima.json", {})
    cota, _ = mc.cota_opus()
    argon = {}  # 29/10 (D24): estado do Argon (zelador + manter) e do Claude web (monitor), para a dona ver sem abrir log
    for nome, arq in (("zelador", r"D:\gemini-argo\argon_zelador.json"), ("manter", r"D:\gemini-argo\argon_manter.json"),
                      ("sonnet_web", r"D:\sonnet web\estado.json")):
        try:
            argon[nome] = json.loads(Path(arq).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            argon[nome] = {}
    return {"modo": pedido, "em_vigor": vigor, "motivo": motivo, "conjuntos": mc.modelos_cfg()["conjuntos"],
            "conjunto_em_vigor": conj, "dona_no_chat": mc.dona_no_chat(mc.modelos_cfg().get("chat_min", 30)),
            "cota_cc": cota, "central_ligado": mc.ligado(), "central_modo": mc.cfg().get("modo"),
            "rodadas": est.get("rodadas") or {}, "bancada": banc,
            "bancada_rodando": (mc.PASTA / "bancada" / ".rodando").exists(), "argon": argon}


def api_modelos_central_mudar(corpo):
    import melhorador_central as mc
    modo = str(corpo.get("modo") or "")
    pedido, vigor, motivo, conj = mc.mudar_modelos(modo)
    return {"modo": pedido, "em_vigor": vigor, "motivo": motivo, "conjunto_em_vigor": conj}


def api_bancada_rodar(_corpo):
    """Dispara a bancada de modelos em segundo plano (1 por vez)."""
    import melhorador_central as mc
    marca = mc.PASTA / "bancada" / ".rodando"
    if marca.exists() and time.time() - marca.stat().st_mtime < 3600:
        return {"ok": False, "erro": "já há uma bancada rodando"}
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(datetime.now().isoformat(), encoding="utf-8")
    log_b = BASE / "logs" / f"bancada_modelos_{datetime.now():%Y%m%d_%H%M}.log"
    py_b = Path(r"D:\recapd-ambientes\producao\venv\Scripts\python.exe")  # tem psutil (cortes_juri)
    cmd = f'"{py_b if py_b.exists() else sys.executable}" -X utf8 "{BASE / "bancada_modelos.py"}" > "{log_b}" 2>&1 & del "{marca}"'
    subprocess.Popen(["cmd", "/c", cmd], cwd=str(BASE), creationflags=0x08000000 | 0x00000008)
    return {"ok": True, "log": str(log_b)}


def api_telao_like(params):
    """29/10 (Fable): aba 'Telão: like e comentário' — a conta pessoal da dona curtiu/comentou os vídeos que o telão
    exibiu? (vitrine\\checklist_like.py lê logs\\vitrine.log; tarefa TelaoChecklist a cada 30 min).
    10/11 (dona: "não diz se é do dia, 7 dias, 30"): ?dias=N recalcula pelo log nesse período."""
    try:
        dias = int(params.get("dias", ["0"])[0] or 0)
    except ValueError:
        dias = 0
    if dias:
        try:
            if str(BASE / "vitrine") not in sys.path:
                sys.path.append(str(BASE / "vitrine"))
            import checklist_like
            return _cache(f"telao_like_{dias}", 300, lambda: checklist_like.montar(dias))
        except Exception as e:  # noqa: BLE001
            return {"erro": f"{type(e).__name__}: {e}"}
    try:
        return json.loads((BASE / "estado" / "vitrine_checklist.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {"erro": f"checklist ainda não gerado ({type(e).__name__})"}


def api_celular(_params):
    """29/10 (Fable, D20): aba 'Celular (proxy TikTok)' — o túnel até o Redmi está vivo? quantos posts saíram pelo celular
    hoje? e o teste (6 contas mortas pelo celular × as outras) está dando certo? Tudo de postador-de-videos\\bin\\proxy_celular.py."""
    try:
        bin_ = r"D:\postador-de-videos\bin"
        if bin_ not in sys.path:
            sys.path.insert(0, bin_)
        import importlib
        import proxy_celular
        importlib.reload(proxy_celular)
        return proxy_celular.placar()
    except Exception as e:  # noqa: BLE001
        return {"erro": f"{type(e).__name__}: {e}"}


ROTAS = {"/api/geral": lambda p: _cache("geral", 10, lambda: api_geral(p)), "/api/medir": api_medir,
         "/api/modelos_central": api_modelos_central, "/api/nsn": api_nsn, "/api/er": api_er, "/api/celular": api_celular, "/api/telao_like": api_telao_like,
         "/api/canais": api_canais, "/api/postagens": api_postagens, "/api/cobertura": api_cobertura, "/api/kanban": api_kanban, "/api/erros": api_erros,
         "/api/ranking": api_ranking, "/api/canais_views": api_canais_views, "/api/placar": api_placar,
         "/api/views_mesma_hora": lambda p: _cache("views_mesma_hora", 120, lambda: api_views_mesma_hora(p)),
         "/api/ranking_canais": lambda p: _cache("ranking_canais", 120, lambda: api_ranking_canais(p)),
         "/api/resumo": lambda p: _cache("resumo", 60, lambda: api_resumo(p)),
         "/api/hipercool": api_hipercool, "/api/producao": lambda p: _cache("producao", 30, lambda: api_producao({})),
         "/api/problemas": api_problemas, "/api/tarefas": api_tarefas, "/api/bots": api_bots, "/api/avisos": api_avisos,
         "/api/aprendizado": api_aprendizado, "/api/ia": api_ia, "/api/ia_pedido": api_ia_pedido,
         "/api/ia_conversa": api_ia_conversa, "/api/ia_doc": api_ia_doc, "/api/vigia_conversa": api_vigia_conversa,
         "/api/agenda": api_agenda, "/api/desempenho": api_desempenho, "/api/contas": api_contas, "/api/voz": api_voz,
         "/api/tendencias": api_tendencias, "/api/referencias": api_referencias, "/api/saude": api_saude, "/api/cortes_dia": api_cortes_dia, "/api/tela": api_tela,
         "/api/segurados": lambda p: _cache("segurados", 120, lambda: api_segurados(p)), "/api/medicoes": api_medicoes,
         "/api/recap_longo": lambda p: _cache("recap_longo", 60, api_recap_longo)}


def api_recap_longo():
    """Recap longo (dona 25/10): a VPS hermes-prod (vps_central.py) grava status.json na página dela; aqui só lê."""
    try:
        pag = (BASE / "estado" / "recap_longo_pagina.txt").read_text(encoding="utf-8").strip()
        with urllib.request.urlopen(f"https://produtos.opus-sem-limites.com.br/{pag}/status.json", timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"erro": f"sem dados da VPS ({type(e).__name__}: {str(e)[:120]})"}
ROTAS_POST = {"/api/controle": api_controle_mudar, "/api/abrir": api_abrir, "/api/tarefa_rodar": api_tarefa_rodar,
              "/api/modelos_central": api_modelos_central_mudar, "/api/bancada_rodar": api_bancada_rodar,
              "/api/er_prioridade": api_er_prioridade,
              "/api/aprendizado_marcar": api_aprendizado_marcar, "/api/ia_pedir": api_ia_pedir, "/api/ia_acao": api_ia_acao,
              "/api/ia_corrigir_todos": api_ia_corrigir_todos, "/api/mover": api_mover, "/api/soltar": api_soltar,
              "/api/referencia_nova": api_referencia_nova}
AQUECER = [("geral", 10, lambda: api_geral({})), ("producao", 30, lambda: api_producao({})), ("canais", 120, _canais),
           ("postagens", 60, _postagens), ("tarefas", 90, _tarefas), ("bots", 600, _bots), ("problemas", 40, _problemas),
           ("saude", 180, _saude), ("tendencias", 900, _tendencias)]
VIDEO_OK = PODE_ABRIR + [APR / "trechos"]
TIPOS = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".mp3": "audio/mpeg", ".wav": "audio/wav",
         ".m4a": "audio/mp4", ".jpg": "image/jpeg", ".png": "image/png"}


CHAVE = BASE / "estado" / "painel_chave.txt"
ARQUIVOS_PUBLICOS = {"/manifest.webmanifest", "/sw.js", "/icone.svg", "/icone-192.png", "/icone-512.png"}


def _chave():
    """Chave de acesso de fora do PC (gerada 1x; apagar o arquivo troca a chave e derruba quem estava logado)."""
    import secrets as _s
    try:
        c = CHAVE.read_text(encoding="utf-8").strip()
        if len(c) >= 20:
            return c
    except OSError:
        pass
    c = _s.token_urlsafe(24)
    CHAVE.write_text(c, encoding="utf-8")
    return c


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(BASE / "painel_web"), **kw)

    def _json(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _midia(self, caminho):
        """Vídeo/áudio/imagem das pastas de produção, com 'Range' (o player do navegador pula pro meio)."""
        p = Path(caminho).resolve()
        if p.suffix.lower() not in TIPOS or not any(p.is_relative_to(b.resolve()) for b in VIDEO_OK) or not p.is_file():
            return self._json({"erro": "arquivo não permitido ou não existe"}, 404)
        tam = p.stat().st_size
        ini, fim = 0, tam - 1
        m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
        if m and (m.group(1) or m.group(2)):
            ini = int(m.group(1)) if m.group(1) else max(0, tam - int(m.group(2)))
            fim = min(int(m.group(2)), tam - 1) if m.group(1) and m.group(2) else tam - 1
        n = fim - ini + 1
        self.send_response(206 if m else 200)
        self.send_header("Content-Type", TIPOS[p.suffix.lower()])
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(n))
        if m:
            self.send_header("Content-Range", f"bytes {ini}-{fim}/{tam}")
        self.end_headers()
        try:
            with open(p, "rb") as f:
                f.seek(ini)
                while n > 0:
                    bloco = f.read(min(n, 1 << 20))
                    if not bloco:
                        break
                    self.wfile.write(bloco)
                    n -= len(bloco)
        except (ConnectionError, OSError):
            pass

    def _remoto(self):
        """Pedido que veio de fora deste PC (Tailscale serve repassa com estes cabeçalhos)."""
        return bool(self.headers.get("Tailscale-User-Login") or self.headers.get("X-Forwarded-For")) \
            or self.client_address[0] not in ("127.0.0.1", "::1")

    def _liberado(self):
        """Fora do PC só com a chave (a IA do painel mexe em arquivo: ninguém de fora sem chave, nem a VPS da tailnet).
        1ª vez: link com ?chave=...; vira cookie de 1 ano e a chave sai do endereço."""
        if not self._remoto():
            return True
        if urlparse(self.path).path in ARQUIVOS_PUBLICOS:  # ícone/manifesto do app do celular: sem dado nenhum
            return True
        import secrets as _s
        chave = _chave()
        q = parse_qs(urlparse(self.path).query).get("chave", [""])[0]
        cookie = re.search(r"painel_chave=([\w-]+)", self.headers.get("Cookie") or "")
        if q and _s.compare_digest(q, chave):
            self.send_response(302)
            seguro = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""  # 25/10: via videos.opus-sem-limites
            self.send_header("Set-Cookie", f"painel_chave={chave}; Max-Age=31536000; Path=/; HttpOnly; SameSite=Lax{seguro}")
            self.send_header("Location", urlparse(self.path).path or "/")
            self.end_headers()
            return False
        if cookie and _s.compare_digest(cookie.group(1), chave):
            return True
        corpo = ("<meta name=viewport content='width=device-width'><body style='background:#000;color:#eee;font-family:sans-serif;"
                 "padding:24px'><h3>Central de Vídeos</h3><p>Abra pelo link com a chave (está no Telegram / no PC em "
                 "D:\\video-fila\\estado\\painel_chave.txt).</p></body>").encode("utf-8")
        self.send_response(401)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)
        return False

    def do_GET(self):
        if not self._liberado():
            return
        u = urlparse(self.path)
        if u.path.startswith("/api/"):
            _ULTIMO_ACESSO[0] = time.time()
        if u.path == "/midia":
            return self._midia(parse_qs(u.query).get("caminho", [""])[0])
        if u.path == "/rede":  # painel da rede (postador\painel\index.html, gerado pela tarefa PainelCanais)
            try:
                corpo = Path(r"D:\postador-de-videos\painel\index.html").read_bytes()
            except OSError:
                corpo = "<p style='font-family:sans-serif'>Painel da rede ainda não gerado (tarefa PainelCanais).</p>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(corpo)
            return
        if u.path not in ROTAS:
            return super().do_GET()
        try:
            self._json(ROTAS[u.path](parse_qs(u.query)))
        except Exception as e:  # noqa: BLE001
            self._json({"erro": f"{type(e).__name__}: {e}"}, 500)

    def do_POST(self):
        # só o próprio painel: outro site não consegue mandar o cabeçalho X-Painel (o navegador barra sem CORS)
        if not self._liberado():
            return
        rota = ROTAS_POST.get(urlparse(self.path).path)
        if not rota or self.headers.get("X-Painel") != "1":
            return self._json({"erro": "não permitido"}, 403)
        try:
            n = int(self.headers.get("Content-Length") or 0)
            self._json(rota(json.loads(self.rfile.read(min(n, 60_000)) or b"{}")))
        except Exception as e:  # noqa: BLE001
            self._json({"erro": f"{type(e).__name__}: {e}"}, 400)

    def log_message(self, *_a):
        pass

    def end_headers(self):  # 06/11: a página nova (números no topo) não aparecia — o navegador guardava o index.html velho
        if not urlparse(self.path).path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


class Servidor(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    # 11/11: a fila padrão é 5; a Visão geral dispara ~10 pedidos juntos e, com o PC1 ocupado no render, os que
    # passavam de 5 eram recusados ("Failed to fetch" / ERR_CONNECTION_REFUSED nos gráficos)
    request_queue_size = 64


def main():
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else PORT
    srv = Servidor(("127.0.0.1", port), Handler)
    threading.Thread(target=_aquecer, daemon=True).start()
    if sys.stdout:
        print(f"Painel em http://localhost:{port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
