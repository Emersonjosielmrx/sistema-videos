"""Publicacao no YouTube dos Shorts prontos (paths.ready + paths.ready_cortes, em hipercool-materiais), via D:/postador-de-videos (youtube_poster + politica).

Todo upload passa pelo youtube_poster.py, entao vale a politica inteira do postador: parada geral, canal bloqueado
(token morto/suspenso), cota do dia, aprovacao humana e intervalo minimo entre videos do mesmo canal. Os canais da rede
ficam reservados ao projeto (config/canais_reservados.json do postador): os outros postadores nao postam neles.

Por video aprovado: horario (config publish.horarios + jitter) -> upload agendado (private + publishAt) -> thumbnail ->
move tudo para hipercool-materiais/_postados/react/<canal>/. Depois que o video fica publico, a proxima rodada posta o comentario do canal
(a API nao permite fixar: fixe no app se quiser).
"""
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from .common import log, load_json, save_json


def _postador(cfg):
    b = str(Path(cfg["publish"]["postador_bin"]))
    if b not in sys.path:
        sys.path.insert(0, b)
    import politica
    import youtube_poster
    return politica, youtube_poster


def _registro_path(cfg):
    return Path(cfg["publish"]["posted_dir"]) / "publicados.json"


def _carregar_registro(cfg):
    p = _registro_path(cfg)
    return load_json(p) if p.exists() else {}


def canais(cfg, politica):
    """slug -> (canal do config, credencial do youtube_canais.json ou None)."""
    creds = politica.carregar_creds()
    out = {}
    for ch in cfg["channels"]:
        yid = ch.get("youtube_id")
        out[ch["slug"]] = (ch, next((c for c in creds if yid and c.get("id") == yid), None))
    return out


def prontos(cfg):
    """Videos em shorts/<canal>/ e cortes/<canal>/ com postar.json pronto, em ordem (p1 antes de p2)."""
    itens = []
    pastas = [cfg["paths"]["ready"]] + ([cfg["paths"]["ready_cortes"]] if cfg["paths"].get("ready_cortes") else [])
    for pj in sorted(p for pasta in pastas for p in Path(pasta).glob("*/*.postar.json")):
        try:
            d = load_json(pj)
        except Exception as e:  # noqa: BLE001
            log(f"publicar: {pj.name} ilegivel ({e})")
            continue
        mp4 = pj.parent / d.get("arquivo", "")
        if d.get("pronto") is False or not mp4.is_file():
            continue
        itens.append({"json": pj, "mp4": mp4, "dados": d, "slug": d.get("canal_slug") or pj.parent.name})
    return itens


def _ocupados(politica, canal):
    """Horarios de publicacao ja usados pelo canal (ledger do postador, todos os scripts)."""
    out = []
    for r in politica._ler_ledger():
        if politica._do_canal(r, canal):
            out.append(politica._dt(r.get("publish_at")) or politica._dt(r["ts"]))
    return out


def proximo_horario(cfg, politica, ocupados, chave):
    """Proximo slot livre (config publish.horarios) respeitando max por dia e o intervalo minimo do canal."""
    pc = cfg["publish"]
    agora = politica.agora()
    intervalo = timedelta(hours=politica.politica().get("intervalo_min_horas_mesmo_canal") or 0)
    j = pc.get("jitter_min", 0)
    jitter = timedelta(minutes=(int(hashlib.md5(chave.encode()).hexdigest(), 16) % (2 * j + 1)) - j) if j else timedelta()
    for dias in range(30):
        dia = (agora + timedelta(days=dias)).date()
        if sum(1 for o in ocupados if o.astimezone().date() == dia) >= pc["max_por_canal_dia"]:
            continue
        for h in pc["horarios"]:
            hh, mm = (int(x) for x in h.split(":"))
            alvo = datetime(dia.year, dia.month, dia.day, hh, mm, tzinfo=agora.tzinfo) + jitter
            if alvo < agora + timedelta(minutes=pc.get("antecedencia_min", 30)):
                continue
            if any(abs(alvo - o) < intervalo for o in ocupados):
                continue
            return alvo
    return None


def _api(yp, canal, url, corpo=None, tipo="application/json"):
    tok = yp.refresh_access_token(canal)
    dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo).encode()
    req = urllib.request.Request(url, data=dados, method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": tipo})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode() or "{}")


def _erro_api(e):
    try:
        er = json.loads(e.read().decode("utf-8", "replace")).get("error", {})
        motivo = ",".join(x.get("reason", "") for x in er.get("errors", []))
        return f"{e.code} {motivo} {er.get('message', '')[:120]}".strip()
    except Exception:  # noqa: BLE001
        return f"{e.code}"


def _thumbnail(yp, canal, vid, thumb):
    try:
        _api(yp, canal, f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}&uploadType=media",
             thumb.read_bytes(), "image/jpeg")
        return "ok"
    except urllib.error.HTTPError as e:
        msg = _erro_api(e)
        if e.code == 403:
            msg += " (thumb personalizada exige canal verificado por telefone)"
        return "erro: " + msg
    except Exception as e:  # noqa: BLE001
        return f"erro: {e}"


def _fora_do_ar(vid):
    """True se o oEmbed publico diz 404 (video removido/apagado). Privado (401/403), no ar (200) ou sem rede: False."""
    try:
        urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json",
                               timeout=20)
        return False
    except urllib.error.HTTPError as e:
        return e.code == 404
    except Exception:  # noqa: BLE001
        return False


def _comentar(yp, canal, vid, texto):
    _api(yp, canal, "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
         {"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": texto}}}})


def _arquivar(cfg, it, extra):
    """Move mp4/postar.json/meta/thumb para _postados/react/<canal>/; o relatorio vai quando a ultima parte sair."""
    src = it["json"].parent
    dst = Path(cfg["publish"]["posted_dir"]) / src.name
    dst.mkdir(parents=True, exist_ok=True)
    stem = it["mp4"].stem
    d = dict(it["dados"], postado=extra)
    save_json(d, dst / it["json"].name)
    it["json"].unlink()
    for f in (it["mp4"], src / f"{stem}_meta.txt", src / (it["dados"].get("thumb") or f"{stem}_thumb.jpg"),
              *(src / n for n in it["dados"].get("thumbs_ab") or [])):
        if f.exists():
            shutil.move(str(f), str(dst / f.name))
    base = re.sub(r"_p\d+$", "", stem)
    rel = src / f"{base}_relatorio.md"
    if rel.exists() and not list(src.glob(f"{base}_p*.postar.json")):
        shutil.move(str(rel), str(dst / rel.name))


def comentarios_pendentes(cfg, politica, yp, reg):
    """Posta o comentario do canal nos videos que ja ficaram publicos."""
    agora = politica.agora()
    por_id = {c["id"]: c for c in politica.carregar_creds()}
    n = 0
    p_ret = Path(cfg["paths"]["work"]) / "rede_retirados.json" if cfg.get("paths", {}).get("work") else None
    retirados = load_json(p_ret) if p_ret and p_ret.exists() else {}
    for chave, r in reg.items():
        if r.get("comentario") != "pendente":
            continue
        if r.get("video_id") in retirados:  # tirado do ar de proposito (rede "tirar e repor"): sem comentario
            r["comentario"] = "retirado"
            continue
        quando = politica._dt(r.get("publish_at")) or politica._dt(r["postado_em"])
        if quando > agora - timedelta(minutes=10):
            continue
        # credencial principal do canal real (rede_canais.json): uma credencial-alias pode estar com a cota do projeto estourada
        rc = politica.rede_do_cred(r.get("canal_id")) if hasattr(politica, "rede_do_cred") else None
        canal = next((por_id[c] for c in (rc or {}).get("creds", []) if c in por_id), None) or por_id.get(r.get("canal_id"))
        if not canal:
            continue
        try:
            _comentar(yp, canal, r["video_id"], r["comentario_texto"])
            r["comentario"] = "ok"
            n += 1
            log(f"comentario postado: {r['canal']} {r['url']}")
        except urllib.error.HTTPError as e:
            msg = _erro_api(e)
            # video ainda processando/privado: tenta de novo na proxima rodada (ate 3 dias). Mas 404 de VIDEO que o
            # oEmbed confirma fora do ar (removido/apagado) desiste na hora (AB-12, 16/10: wKiGkUQ6bBc repetia o 404
            # de hora em hora - "removido por ser muito longo").
            if e.code == 403 and "insufficient" in msg.lower() and not _fora_do_ar(r["video_id"]):
                # 403 de PERMISSAO (a credencial da API nao pode comentar naquele canal - 16/10: 21x/dia nos 2 do Veo):
                # nao e horario, nao adianta repetir. Passa para o navegador: postador\bin\extras_rede.py comenta e
                # FIXA pelo Studio (ordem do dono 16/10: tudo pelo navegador).
                r["comentario"] = "navegador"
                log(f"comentario: {r['canal']} {r['url']} sem permissao pela API - vai pelo navegador (extras_rede)")
                continue
            if quando < agora - timedelta(days=3) or e.code not in (403, 404) or (e.code == 404 and _fora_do_ar(r["video_id"])):
                r["comentario"] = "erro: " + msg
            log(f"comentario falhou ({r['canal']} {r['url']}): {msg}")
        except Exception as e:  # noqa: BLE001
            log(f"comentario falhou ({r['canal']} {r['url']}): {e}")
    return n


def publicar(cfg, dry_run=False, limite=None, so_comentarios=False):
    politica, yp = _postador(cfg)
    pc = cfg["publish"]
    reg = _carregar_registro(cfg)
    total = 0
    if not so_comentarios:
        parada = politica.parada_ativa()
        if parada:
            log(f"publicar: PARADA GERAL do postador desde {parada.get('desde')}: {parada.get('motivo')} - nada sobe")
            return 0
        grupos = {}
        for it in prontos(cfg):
            grupos.setdefault(it["slug"], []).append(it)
        mapa = canais(cfg, politica)
        aprov = politica.ler_json(politica.APROV_FILE, {})
        for slug, itens in grupos.items():
            ch, canal = mapa.get(slug, (None, None))
            if not canal:
                log(f"{slug}: sem credencial ligada (config.json > channels > youtube_id) - {len(itens)} video(s) parados")
                continue
            nome = canal["nome"].strip()
            bloq = politica.motivo_bloqueio(canal)
            if bloq:
                log(f"{nome}: bloqueado no postador ({bloq}) - {len(itens)} video(s) esperando. Token morto: rode o relogin")
                continue
            aprovados = [i for i in itens if politica.status_aprovacao(i["mp4"], aprov) == "aprovado"
                         or not politica.politica().get("exigir_aprovacao_humana")]
            esperando = sum(1 for i in itens if politica.status_aprovacao(i["mp4"], aprov) is None)
            if esperando:
                log(f"{nome}: {esperando} video(s) esperando aprovacao (manhwareact.py aprovar)")
            ocupados = _ocupados(politica, canal)
            feitos = politica.uploads_hoje(canal)
            for it in aprovados:
                if feitos >= pc["max_por_canal_dia"]:
                    log(f"{nome}: ja subiram {feitos} hoje (max {pc['max_por_canal_dia']}) - o resto fica para amanha")
                    break
                if limite and total >= limite:
                    break
                alvo = proximo_horario(cfg, politica, ocupados, it["mp4"].name)
                if not alvo:
                    log(f"{nome}: sem horario livre nos proximos 30 dias")
                    break
                d = it["dados"]
                if dry_run:
                    log(f"[simulacao] {nome}: {it['mp4'].name} -> publica {alvo:%d/%m %H:%M} | {d['titulo'][:70]}")
                    ocupados.append(alvo); feitos += 1; total += 1
                    continue
                log(f"{nome}: enviando {it['mp4'].name} (publica {alvo:%d/%m %H:%M})")
                from .rede import anuncio_seguro
                status, info = politica.postar_youtube(canal["id"], it["mp4"], anuncio_seguro(d["titulo"]),
                                                       anuncio_seguro(d.get("descricao", "")),
                                                       [anuncio_seguro(t) for t in d.get("tags") or []], privacy="private",
                                                       publish_at=politica.rfc3339(alvo), projeto=pc["projeto"], tipo="short")
                if status in ("parado", "suspenso"):
                    log(f"{nome}: {status} - {info}. PAROU TUDO (veja D:/postador-de-videos/config/PARADO.json)")
                    if status == "suspenso":
                        from . import notificar
                        notificar.aviso(f"Canal SUSPENSO: {nome}", f"{info} - a postagem parou toda", nivel="erro")
                    save_json(reg, _registro_path(cfg))
                    return total
                if status in ("morto", "limite", "cota", "reservado"):
                    log(f"{nome}: {status} - {info}. Canal pulado nesta rodada")
                    break
                if status != "ok":
                    log(f"{nome}: {it['mp4'].name} nao subiu ({status}: {info})")
                    continue
                vid = info.rsplit("/", 1)[-1]
                rec = next((r for r in reversed(politica._ler_ledger()) if r.get("video_id") == vid), {})
                publica = rec.get("publish_at") or politica.rfc3339(alvo)
                ocupados.append(politica._dt(publica)); feitos += 1; total += 1
                thumb = it["json"].parent / (d.get("thumb") or f"{it['mp4'].stem}_thumb.jpg")
                st_thumb = _thumbnail(yp, canal, vid, thumb) if pc.get("thumbnail") and thumb.exists() else "sem"
                texto = (d.get("comentario_fixado") or "").strip()
                extra = {"video_id": vid, "url": info, "canal": nome, "canal_id": canal["id"], "publish_at": publica,
                         "postado_em": politica.agora().isoformat(timespec="seconds"), "thumb": st_thumb,
                         "comentario": "pendente" if pc.get("comentario") and texto else "sem", "comentario_texto": texto,
                         "titulo": d["titulo"], "canal_slug": slug}
                reg[it["mp4"].stem] = extra
                save_json(reg, _registro_path(cfg))
                _arquivar(cfg, it, extra)
                log(f"{nome}: AGENDADO {info} -> {publica} | thumb {st_thumb}")
    if not dry_run and pc.get("comentario"):
        comentarios_pendentes(cfg, politica, yp, reg)
    save_json(reg, _registro_path(cfg)) if reg else None
    log(f"publicar: {total} video(s) {'simulado(s)' if dry_run else 'agendado(s)'} nesta rodada")
    return total


def aprovar(cfg, tudo=False, abrir=True):
    """Revisao humana: abre cada Short pendente no player e grava a decisao na politica do postador."""
    politica, _ = _postador(cfg)
    aprov = politica.ler_json(politica.APROV_FILE, {})
    pend = [i for i in prontos(cfg) if politica.status_aprovacao(i["mp4"], aprov) is None]
    print(f"{len(pend)} video(s) esperando aprovacao.\n")
    if tudo:  # sem olhar: só sobe o que a análise de nudez passou (dono 20/10; advertência do hipercool 16/10)
        from . import revisao_nudez
        for it in pend:
            st, nota = revisao_nudez.portao(it["mp4"])
            if st:
                politica.marcar_aprovacao(it["mp4"], st, nota)
            print(f"  {st or 'fica pendente'}: {it['slug']}/{it['mp4'].name} ({nota})")
        return
    print("Para cada video: [a]provar  [r]ejeitar  [p]ular  [s]air\n")
    feitos = {"aprovado": 0, "rejeitado": 0}
    for n, it in enumerate(pend, 1):
        d = it["dados"]
        print(f"-- {n}/{len(pend)} -- {it['slug']} -- {it['mp4'].stat().st_size / 1e6:.0f} MB")
        print(f"   titulo:    {d.get('titulo', '')}")
        print(f"   descricao: {d.get('descricao', '')[:220].replace(chr(10), ' ')}")
        if abrir:
            try:
                os.startfile(str(it["mp4"]))
            except Exception as e:  # noqa: BLE001
                print(f"   (nao abriu o player: {e})")
        r = ""
        while r not in ("a", "r", "p", "s"):
            r = input("   > ").strip().lower()[:1]
        if r == "s":
            break
        if r == "p":
            continue
        status = "aprovado" if r == "a" else "rejeitado"
        nota = input("   motivo (opcional): ").strip() if status == "rejeitado" else ""
        politica.marcar_aprovacao(it["mp4"], status, nota)
        feitos[status] += 1
    print(f"\nAprovados: {feitos['aprovado']} | Rejeitados: {feitos['rejeitado']}")


def situacao(cfg):
    """Resumo por canal: credencial, aprovacoes, fila e postados."""
    politica, _ = _postador(cfg)
    aprov = politica.ler_json(politica.APROV_FILE, {})
    reg = _carregar_registro(cfg)
    itens = prontos(cfg)
    for slug, (ch, canal) in canais(cfg, politica).items():
        meus = [i for i in itens if i["slug"] == slug]
        st = [politica.status_aprovacao(i["mp4"], aprov) for i in meus]
        if not canal:
            cred = "SEM CREDENCIAL"
        else:
            bloq = politica.motivo_bloqueio(canal)
            cred = f"BLOQUEADO ({bloq})" if bloq else f"ok, {politica.uploads_hoje(canal)} upload(s) hoje"
        postados = [r for r in reg.values() if r.get("canal_slug") == slug]
        print(f"{ch['name']:13} token: {cred}")
        print(f"{'':13} fila: {len(meus)} | aprovados {st.count('aprovado')} | esperando {st.count(None)} | rejeitados {st.count('rejeitado')}"
              f" | postados {len(postados)} (comentarios pendentes {sum(1 for r in postados if r.get('comentario') == 'pendente')})")
        for r in sorted(postados, key=lambda r: r.get("publish_at") or "")[-3:]:
            print(f"{'':13}   {r.get('publish_at', '')[:16]} {r['url']} {r['titulo'][:50]}")
