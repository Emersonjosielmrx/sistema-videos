#!/usr/bin/env python3
"""metricas_rede.py - le no Studio, PELO NAVEGADOR, as metricas dos videos da REDE e alimenta o aprendizado dela
(Onda 3.1 do plano geral; itens AT-03/DS-04 de D:\\veo\\docs\\PLANO_MELHORIAS_VEO.md, 16/10). Nada de API.

Ate aqui a rede so aprendia por VIEWS (painel_canais.py: views / mediana do canal). O que o Studio mostra e a API nao:
  - Short: "Continuaram assistindo" (% que NAO deslizou no feed), visualizacoes intencionais, duracao media;
  - completo (longo): impressoes e CTR.
Copiado do padrao do hipercool (bin/metricas.py): le videos de 48 h a 21 dias, rele a cada 72 h. Cada CANAL abre o
Chrome uma vez (youtube_studio_extras.sessao) e le varios videos; limite por canal e por rodada.

Decide (1 vez por video, com 3+ do mesmo canal medidos para ter mediana):
  - Short: nota = continuaram / mediana do canal -> braco do GANCHO usado (o que segura nos 1os segundos);
  - completo: nota = CTR / mediana dos completos do canal (com impressoes suficientes) -> braco do TITULO.
As notas entram em _analise/rede_aprendizado.json (canais[slug][dim][braco]), o mesmo que o mr/rede.py le.

Uso: python bin/metricas_rede.py [--max 12] [--por-canal 4] [--so-decidir]
Dados: _analise/metricas_studio.json.   Log: logs/metricas_rede.log
"""
import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BIN = Path(__file__).resolve().parent
ROOT = BIN.parent
sys.path.insert(0, str(BIN))
PUBLICADOS = Path(r"D:\hipercool-materiais\_postados\react\publicados.json")
DADOS = ROOT / "_analise" / "metricas_studio.json"
APREND = ROOT / "_analise" / "rede_aprendizado.json"
LOG = ROOT / "logs" / "metricas_rede.log"
IDADE_MIN_H, IDADE_MAX_D, RELER_H = 48, 21, 72
# 18/10 (unificação): vídeos que não são da rede (Noturnos, hipercool, parceiro...) vêm do ledger, só pra 1ª leitura
# (48-96 h). É a medição dos canais sem token de API (os Noturnos): notificar_telegram.medir_48h usa estas views.
LEDGER = ROOT / "logs" / "uploads_ledger.jsonl"
CADASTRO = ROOT / "config" / "canais.json"
PRIMEIRA_MAX_H = 96
MIN_AMOSTRA = 3
MIN_IMPRESSOES = 100


def log(msg):
    linha = f"[{datetime.now():%d/%m %H:%M:%S}] {msg}"
    print(linha, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        tmp.replace(p)
    except PermissionError:
        # Fallback: força com shutil.move (pode sobrescrever mesmo com lock de leitura em alguns casos)
        import shutil
        try:
            shutil.move(str(tmp), str(p))
        except Exception as e2:
            # Se ainda falhar, deixa o .tmp e avisa no stderr (não trava o script)
            print(f"[AVISO] Nao gravou {p.name}: {e2} (mantido em {tmp.name})", file=sys.stderr)


def _dt(s):
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.astimezone()
    except (TypeError, ValueError):
        return None


RETIRADOS = Path(r"D:\manhwa-react\work\rede_retirados.json")


def pendentes(reg, dados, agora):
    """{canal_id: [(vid, item, idade_h)]} na idade de medir e nao lidos nas ultimas RELER_H. Pula retirado (rede "tirar
    e repor") e removido do YouTube (16/10: a 1a rodada gastou 1 min de Chrome no wKiGkUQ6bBc, removido)."""
    retirados = _ler(RETIRADOS, {})
    out = {}
    for chave, v in reg.items():
        if not isinstance(v, dict) or not v.get("video_id") or not v.get("canal_id"):
            continue
        if v["video_id"] in retirados or (dados.get(v["video_id"]) or {}).get("removido"):
            continue
        quando = _dt(v.get("publish_at")) or _dt(v.get("postado_em"))
        if not quando:
            continue
        idade_h = (agora - quando).total_seconds() / 3600
        if idade_h < IDADE_MIN_H or idade_h > IDADE_MAX_D * 24:
            continue
        d = dados.get(v["video_id"], {})
        if v.get("so_primeira"):
            if idade_h > PRIMEIRA_MAX_H or d.get("lido_em"):
                continue
        elif d.get("lido_em") and (agora - _dt(d["lido_em"])).total_seconds() / 3600 < RELER_H:
            continue
        out.setdefault(v["canal_id"], []).append((v["video_id"], dict(v, _chave=chave), idade_h))
    return out


def do_ledger(reg):
    """{chave: item} dos uploads do ledger que não estão no registro da rede, no formato que pendentes() lê."""
    na_rede = {v.get("video_id") for v in reg.values() if isinstance(v, dict)}
    import politica
    creds = {c["id"]: c for c in politica.carregar_creds()}
    slugs, parados = {}, set()
    for k, x in (_ler(CADASTRO, {}).get("canais") or {}).items():
        parado = politica.estado_do_cadastro(x, creds) != "ativo"
        for cid in x.get("creds") or []:
            slugs[cid] = x.get("slug") or k
            if parado:
                parados.add(cid)
    out = {}
    for ln in LEDGER.read_text("utf-8").splitlines() if LEDGER.exists() else []:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        vid = r.get("video_id")
        if not vid or vid in na_rede or not r.get("canal_id") or r["canal_id"] in parados:
            continue
        out["ledger:" + vid] = {"video_id": vid, "canal_id": r["canal_id"], "publish_at": r.get("publish_at") or r.get("ts"),
                                "canal_slug": slugs.get(r["canal_id"], r.get("canal")), "so_primeira": True,
                                "fonte": " ".join(x for x in (r.get("projeto"), r.get("tipo")) if x) or None,
                                "titulo": _titulo_da_ficha(r) or r.get("arquivo") or ""}
    return out


def _titulo_da_ficha(r):
    """Título que subiu (postar.json ao lado do arquivo do ledger). 21/10: sem isso o painel mostrava "video.mp4"
    (todo Short do parceiro tem esse nome) nas listas de melhores/piores."""
    try:
        return json.loads((Path(r["caminho"]).parent / "postar.json").read_text("utf-8")).get("titulo") or ""
    except (KeyError, TypeError, OSError, ValueError):
        return ""


def _fora(vid):
    """True so se o oEmbed diz 404 (privado = 401/403 nao conta: pode voltar)."""
    import urllib.error
    import urllib.request
    try:
        urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json",
                               timeout=20)
        return False
    except urllib.error.HTTPError as e:
        return e.code == 404
    except Exception:  # noqa: BLE001
        return False


def coletar(max_total, por_canal):
    import youtube_studio_extras as yx
    import youtube_web_poster as yw
    reg, dados = _ler(PUBLICADOS, {}), _ler(DADOS, {})
    agora = datetime.now(timezone.utc)
    fila = pendentes(reg, dados, agora)
    fila_ledger = pendentes(do_ledger(reg), dados, agora)
    log(f"metricas da rede: {sum(len(x) for x in fila.values())} video(s) na idade de medir em {len(fila)} canal(is)"
        f" + {sum(len(x) for x in fila_ledger.values())} de fora da rede (1ª leitura)")
    lidos = 0
    ordem = sorted(fila.items(), key=lambda kv: -len(kv[1]))
    resto = sorted(fila_ledger.items(), key=lambda kv: -len(kv[1]))
    if fila_ledger and max_total > 1:  # 1 vaga garantida pro de fora mais velho: ele vence em 96 h, a rede relê por 21 dias
        cid, itens = max(fila_ledger.items(), key=lambda kv: max(h for _v, _i, h in kv[1]))
        velho = max(itens, key=lambda x: x[2])
        ordem = [(cid, [velho])] + ordem
        resto = [(c, its) for c, its in ((c, [x for x in its if x is not velho]) for c, its in resto) if its]
    ordem += resto
    for canal_id, itens in ordem:  # depois da vaga garantida: rede primeiro, os de fora pegam a sobra da rodada
        if lidos >= max_total:
            break
        try:
            _c, _slug, e = yw._canal_e_mapa(canal_id)
        except Exception as ex:  # noqa: BLE001  (canal fora do navegador: nao da para abrir o Studio dele)
            log(f"  {canal_id}: sem perfil de navegador ({str(ex)[:80]}) - pulado")
            continue
        itens = sorted(itens, key=lambda x: x[2])[:min(por_canal, max_total - lidos)]
        try:
            with yx.sessao(e) as pg:
                for vid, it, idade_h in itens:
                    try:
                        m = yx.metricas(pg, vid)
                    except Exception as ex:  # noqa: BLE001
                        m = {"aviso": f"{type(ex).__name__}: {str(ex)[:120]}"}
                    lidos += 1
                    base = {"lido_em": datetime.now().astimezone().isoformat(timespec="minutes"),
                            "idade_h": round(idade_h), "canal_slug": it.get("canal_slug"), "fonte": it.get("fonte"),
                            "estrategia": it.get("estrategia"), "titulo": it.get("titulo", "")[:90],
                            "chave": it.get("_chave")}
                    if it.get("so_primeira"):
                        base["so_primeira"] = True
                    if m.get("aviso"):
                        dados[vid] = {**dados.get(vid, {}), **base, "erro": m["aviso"]}
                        import extras_rede  # oEmbed: 404 = saiu do ar -> nunca mais tenta
                        if extras_rede.no_ar(vid) is False and _fora(vid):
                            dados[vid]["removido"] = True
                        log(f"  {vid} ({it.get('canal_slug')}): nao leu ({m['aviso'][:100]})"
                            + (" - REMOVIDO do YouTube, nao tenta mais" if dados[vid].get("removido") else ""))
                    else:
                        dados[vid] = {**dados.get(vid, {}), **m, **base}
                        dados[vid].pop("erro", None)
                        log(f"  {vid} ({it.get('canal_slug')}, {it.get('fonte')}): views {m.get('views')} | "
                            f"continuaram {m.get('continuaram')}% | intencionais {m.get('intencionais')} | "
                            f"dur {m.get('dur_media')}s | CTR {m.get('ctr')}")
                    _gravar(DADOS, dados)
        except Exception as ex:  # noqa: BLE001
            log(f"  {canal_id}: sessao falhou ({type(ex).__name__}: {str(ex)[:120]})")
    return lidos


def decidir():
    """Transforma o que foi lido em nota de braco (1 vez por video). Devolve quantas notas gravou."""
    dados, apr = _ler(DADOS, {}), _ler(APREND, {})
    canais = apr.setdefault("canais", {})
    por_canal = {}
    for vid, d in dados.items():
        if isinstance(d, dict) and not vid.startswith("_") and not d.get("erro") and not d.get("so_primeira"):
            por_canal.setdefault(d.get("canal_slug"), []).append((vid, d))  # de fora da rede não entra na mediana dela
    n = 0
    for slug, lst in por_canal.items():
        shorts = [(v, d) for v, d in lst if d.get("fonte") != "completo" and d.get("continuaram") is not None]
        if len(shorts) >= MIN_AMOSTRA:
            med = statistics.median(d["continuaram"] for _, d in shorts) or 1
            for vid, d in shorts:
                braco = (d.get("estrategia") or {}).get("gancho")
                if d.get("decidido_gancho") or not braco:
                    continue
                nota = round(d["continuaram"] / med, 3)
                canais.setdefault(slug, {}).setdefault("gancho", {}).setdefault(braco, []).append(nota)
                d["decidido_gancho"] = f"continuaram {d['continuaram']} x mediana {med} -> {nota}"
                n += 1
        # 22/10 (MR-03): o Studio quase nunca devolve "continuaram" (todas as rodadas desde 17/10 = 0 notas,
        # só 6 na vida). Fallback: nota = views / mediana de views do canal — a MESMA régua relativa, marcada
        # como "fallback views" no decidido_gancho. Vídeo com "continuaram" continua usando a régua de cima.
        sem_ret = [(v, d) for v, d in lst if d.get("fonte") != "completo" and d.get("continuaram") is None
                   and d.get("views") is not None]
        if len(sem_ret) >= MIN_AMOSTRA:
            med = statistics.median(d["views"] for _, d in sem_ret)
            if med:  # mediana 0 = canal sem alcance medível, razão não diz nada
                for vid, d in sem_ret:
                    braco = (d.get("estrategia") or {}).get("gancho")
                    if d.get("decidido_gancho") or not braco:
                        continue
                    nota = round(d["views"] / med, 3)
                    canais.setdefault(slug, {}).setdefault("gancho", {}).setdefault(braco, []).append(nota)
                    d["decidido_gancho"] = f"fallback views {d['views']} x mediana {med} -> {nota}"
                    n += 1
        longos = [(v, d) for v, d in lst if d.get("fonte") == "completo" and d.get("ctr") is not None
                  and (d.get("impressoes") or 0) >= MIN_IMPRESSOES]
        if len(longos) >= MIN_AMOSTRA:
            med = statistics.median(d["ctr"] for _, d in longos) or 1
            for vid, d in longos:
                braco = (d.get("estrategia") or {}).get("titulo")
                if d.get("decidido_titulo") or not braco:
                    continue
                nota = round(d["ctr"] / med, 3)
                canais.setdefault(slug, {}).setdefault("titulo", {}).setdefault(braco, []).append(nota)
                d["decidido_titulo"] = f"ctr {d['ctr']} x mediana {med} -> {nota}"
                n += 1
    if n:
        _gravar(APREND, apr)
    _gravar(DADOS, dados)
    log(f"metricas da rede: {n} nota(s) nova(s) no aprendizado")
    return n


VEO_CACHE = Path(r"D:\veo\beta\logs\video_cache.json")


def alimentar_veo():
    """Fecha o laco do GERADOR do Veo (item AT-03): o numero real do video postado vai para a formula que o gerou
    (video_cache.json, item com o mesmo nome de arquivo; o limpo e o bruto do cron tem o mesmo nome). As analises do
    gerador (padroes de viralizacao, media por canal) ja leem metrics.views - so ninguem preenchia; ate aqui ele
    aprendia so com a nota do proprio critico. Devolve quantos itens atualizou."""
    dados, cache = _ler(DADOS, {}), _ler(VEO_CACHE, None)
    if not isinstance(cache, list):
        return 0
    por_nome = {Path(str(c.get("video_path") or "")).stem: c for c in cache if c.get("video_path")}
    n = 0
    for vid, d in dados.items():
        chave = str((d or {}).get("chave") or "")
        if not chave.startswith("veo:") or d.get("erro") or d.get("views") is None:
            continue
        c = por_nome.get(chave[4:])
        if not c or (c.get("metrics") or {}).get("lido_em") == d.get("lido_em"):
            continue
        c.setdefault("metrics", {}).update({k: d.get(k) for k in ("views", "continuaram", "intencionais", "dur_media")},
                                           video_id=vid, posted_url=f"https://youtu.be/{vid}", lido_em=d.get("lido_em"))
        c["metrics_updated_at"] = datetime.now().isoformat(timespec="seconds")
        n += 1
    if n:
        _gravar(VEO_CACHE, cache)
        log(f"metricas da rede: {n} formula(s) do Veo com numero real")
    return n


LOTE = ROOT / "_analise" / "metricas_lote.json"  # canal_id -> quando a lista dele foi lida
LOTE_RELER_H = 6
PUBLICO = ("público", "public")


def _studio_http(slug):
    """29/10 (Fable, D15): o lote do Studio por HTTP, sem Chrome (projeto-navegador-sem-navegador: StudioAnalytics +
    cookies de D:\\gemini-argo\\cookies_youtube). Só com cookie VIVO (teste quieto: GET do Studio tem CHANNEL_ID) —
    cookie morto = None e o lote segue pelo Chrome como sempre (que também renova o login). Devolve
    {video_id: {views, dur_media, pct_media, continuaram, impressoes, ctr, feed_impressoes}} ou None."""
    try:
        import requests
        arq = Path(r"D:\gemini-argo\cookies_youtube") / f"{slug}.json"
        if not arq.exists():
            return None
        s = requests.Session()
        s.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                   "Chrome/156.0.0.0 Safari/537.36")
        s.cookies.update(json.loads(arq.read_text("utf-8")))
        if '"CHANNEL_ID":"' not in s.get("https://studio.youtube.com/", timeout=30).text:
            return None
        raiz = r"D:\projeto-navegador-sem-navegador"
        if raiz not in sys.path:
            sys.path.insert(0, raiz)
        from services.youtube.studio_analytics import StudioAnalytics
        out = {}
        for v in StudioAnalytics(slug).videos(dias=28, limite=200):
            out[v["id"]] = {"views": v.get("views"), "dur_media": v.get("duracao_media_s"), "pct_media": v.get("pct_assistido"),
                            "continuaram": v.get("shorts_ficaram_pct"), "impressoes": v.get("impressoes"), "ctr": v.get("ctr"),
                            "feed_impressoes": v.get("shorts_impressoes"), "intencionais": None,
                            "views_periodo": v.get("views"), "inscritos": v.get("inscritos")}
        return out
    except Exception as ex:  # noqa: BLE001
        log(f"  lote {slug}: HTTP falhou ({type(ex).__name__}: {str(ex)[:100]}) — vai pelo Chrome")
        return None


def coletar_lote(max_canais, so=None):
    """M8 (22/10): views em LOTE na lista de Conteúdo (youtube_studio_extras.views_lista), 1 página por canal, pros
    Shorts de fora da rede (parceiro, hipercool...) que a leitura de 1 em 1 não alcança (3 por hora; 88 sem views em
    22/10). Só PREENCHE quem ainda não tem views (Público e com 48 h a 21 dias: mesma janela do coletar), marcado
    fonte_leitura="lista"; quem já tem views do Analytics fica igual e ganha views_lista (total de agora). Assim a 1ª
    leitura de 48-96 h do Telegram e as notas do gancho não mudam; o narrador (anime_voz_clonada) e o painel ganham dado."""
    import youtube_studio_extras as yx
    import youtube_web_poster as yw
    reg, dados, lote = _ler(PUBLICADOS, {}), _ler(DADOS, {}), _ler(LOTE, {})
    agora = datetime.now(timezone.utc)
    alvos = {}
    for v in do_ledger(reg).values():
        q = _dt(v.get("publish_at"))
        h = (agora - q).total_seconds() / 3600 if q else -1
        if IDADE_MIN_H <= h <= IDADE_MAX_D * 24 and (dados.get(v["video_id"]) or {}).get("views") is None \
                and not (dados.get(v["video_id"]) or {}).get("removido"):
            alvos.setdefault(v["canal_id"], {})[v["video_id"]] = (v, h)
    recente = {c for c, t in lote.items() if _dt(t) and (agora - _dt(t)).total_seconds() < LOTE_RELER_H * 3600}
    ordem = sorted((c for c in alvos if c not in recente), key=lambda c: (lote.get(c, ""), -len(alvos[c])))
    if so:  # só esses canal_id (teste / rodada na mão)
        ordem = [c for c in alvos if c in so]
    log(f"lote: {sum(len(x) for x in alvos.values())} video(s) sem views em {len(alvos)} canal(is); "
        f"lendo {min(max_canais, len(ordem))} ({len(recente & set(alvos))} lido(s) nas ultimas {LOTE_RELER_H} h)")
    preenchidos = 0
    for canal_id in ordem[:max_canais]:
        try:
            _c, slug, e = yw._canal_e_mapa(canal_id)
        except Exception as ex:  # noqa: BLE001
            log(f"  lote {canal_id}: sem perfil de navegador ({str(ex)[:80]}) - pulado")
            continue
        if not e.get("channel_id"):
            log(f"  lote {slug}: sem channel_id no mapa - pulado")
            continue
        t0 = time.time()
        http = _studio_http(slug)  # 29/10 (Fable, D15): sem Chrome quando o cookie HTTP está vivo
        if http is not None:
            t1 = t2 = time.time()
            lidos = {vid: {"views": x["views"], "visibilidade": "Público", "data": "", "aba": "http"}
                     for vid, x in http.items() if vid in alvos[canal_id]}
            ret = http
            log(f"  lote {slug}: por HTTP (sem Chrome) em {t1 - t0:.0f} s — {len(http)} vídeo(s) no Studio")
        else:
            try:
                with yx.sessao(e) as pg:
                    t1 = time.time()  # até aqui: fila da trava do navegador + abrir o Chrome da conta
                    lidos = yx.views_lista(pg, e["channel_id"], alvos=list(alvos[canal_id]))
                    t2 = time.time()
                    # 23/10 (pedido do placar de formatos/vozes): retenção do canal inteiro na mesma sessão, 1 página do
                    # modo avançado; falhar aqui não perde as views já lidas
                    try:
                        ret = yx.retencao_lista(pg, e["channel_id"])
                    except Exception as ex:  # noqa: BLE001
                        ret = {}
                        log(f"  lote {slug}: retencao falhou ({type(ex).__name__}: {str(ex)[:100]})")
            except Exception as ex:  # noqa: BLE001
                log(f"  lote {slug}: sessao falhou ({type(ex).__name__}: {str(ex)[:120]})")
                continue
        dados = _ler(DADOS, {})  # relê: o coletar() ou outra rodada pode ter gravado no meio
        quando = datetime.now().astimezone().isoformat(timespec="minutes")
        n_ok, fora = 0, []
        for vid, (it, h) in alvos[canal_id].items():
            x = lidos.get(vid)
            if not x:
                fora.append(vid)
                continue
            d = dados.setdefault(vid, {})
            d.update(views_lista=x["views"], views_lista_em=quando, visibilidade=x["visibilidade"])
            d.setdefault("so_primeira", True)  # de fora da rede: nunca entra na mediana dela (decidir)
            d.setdefault("canal_slug", it.get("canal_slug"))
            if x["views"] is None or x["visibilidade"].casefold() not in PUBLICO or d.get("views") is not None:
                continue  # privado/agendado/não listado: 0 view não é nota do vídeo
            d.update(views=x["views"], lido_em=quando, idade_h=round(h), canal_slug=it.get("canal_slug"),
                     fonte=it.get("fonte"), titulo=(it.get("titulo") or "")[:90], chave="<SEGREDO_REMOVIDO>" + vid,
                     so_primeira=True, fonte_leitura="lista")
            d.pop("erro", None)
            n_ok += 1
        # retenção: só vídeo nosso (do ledger deste canal ou já no arquivo). ret_lista guarda a leitura crua; os campos
        # continuaram/dur_media do metricas() por vídeo (período desde a publicação) não são sobrescritos, só preenchidos
        nossos = {v["video_id"]: v for v in do_ledger(reg).values() if v.get("canal_id") == canal_id}
        n_ret = 0
        for vid, x in ret.items():
            if vid not in nossos and vid not in dados:
                continue
            d = dados.setdefault(vid, {})
            if vid in nossos:
                d.setdefault("canal_slug", nossos[vid].get("canal_slug"))
                if not d.get("titulo") or str(d["titulo"]).endswith(".mp4"):
                    d["titulo"] = (nossos[vid].get("titulo") or "")[:90] or d.get("titulo")
                d.setdefault("so_primeira", True)  # entrou pela retenção: fora da mediana da rede (igual ao lote)
            d["ret_lista"] = dict(x, em=quando)
            # 29/10 (Fable, ER_02): a tabela agora traz também impressões de miniaturas, CTR e visualizações
            # intencionais — preenche os mesmos campos que o metricas() por vídeo usa (placar de título por CTR)
            for k in ("continuaram", "dur_media", "pct_media", "impressoes", "ctr", "intencionais", "feed_impressoes"):
                if d.get(k) is None and x.get(k) is not None:
                    d[k] = x[k]
            n_ret += 1
        _gravar(DADOS, dados)
        lote = _ler(LOTE, {})
        lote[canal_id] = quando
        _gravar(LOTE, lote)
        preenchidos += n_ok
        log(f"  lote {slug}: {len(lidos)} na lista, {n_ok} de {len(alvos[canal_id])} preenchido(s), "
            f"retencao de {n_ret} "
            f"(trava+Chrome {t1 - t0:.0f} s, lista {t2 - t1:.0f} s)"
            + (f"; {len(fora)} nao achado(s) nas paginas lidas: {', '.join(fora[:5])}" if fora else ""))
    return preenchidos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--por-canal", type=int, default=4)
    ap.add_argument("--so-decidir", action="store_true")
    ap.add_argument("--lote", type=int, default=4,
                    help="canais lidos em lote na lista de Conteudo (M8, 22/10); 0 desliga")
    a = ap.parse_args()
    if not a.so_decidir:
        coletar(a.max, a.por_canal)
        if a.lote:
            coletar_lote(a.lote)
    decidir()
    alimentar_veo()


if __name__ == "__main__":
    main()
