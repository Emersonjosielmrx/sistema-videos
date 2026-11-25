"""Reels nas Páginas do Facebook (dona 19-20/11/2026: "comece as postagens", trabalhar a noite toda).

Cada Página de config/facebook_paginas.json reposta os vídeos que JÁ saíram no YouTube dos canais em 'postados_em'
(catálogo: bin/catalogo.py), ainda não postados nesta Página, mais recentes primeiro. Posta pelo Meta Business Suite
(fb_reel_bs.postar: só a Página marcada; Instagram/grupos desmarcados) no Chrome da conta, SEMPRE pela saída fixa
dela (fb_contas.abrir confere o proxy). Antes de postar entra como a Página (fb_entrar_como) — o composer exige.

Limites: 'por_dia' por Página (padrão 3), intervalo entre posts, duração <= 90 s (Reel do FB aceita até 90 s
para entrar em Reels e na monetização), nunca o mesmo vídeo em 2 Páginas. Registro: logs/facebook_paginas.json.
MS Energy NÃO passa aqui (produto de cliente: postar_ms_energy.py + trava_empresa).

    python postar_facebook_paginas.py --preview            # mostra o que sairia em cada Página
    python postar_facebook_paginas.py --um                 # 1 Reel na Página mais atrasada e sai (cron)
    python postar_facebook_paginas.py --pagina assistia --um
"""
import argparse, json, os, subprocess, sys, time
from datetime import datetime
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
import catalogo  # noqa: E402

CFG = BIN.parent / "config" / "facebook_paginas.json"
REG = BIN.parent / "logs" / "facebook_paginas.json"
FFPROBE = r"D:\hipercool-materiais\bin\ffprobe.exe"
DUR_MAX = 90


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return padrao


def _gravar(reg):
    """Grava mesclando com o que está no disco (20/11: as 2 contas postam em paralelo, cada uma num processo)."""
    disco = _ler(REG, {})
    for sec in ("postados",):
        for ch, lst in (disco.get(sec) or {}).items():
            meu = reg.setdefault(sec, {}).setdefault(ch, [])
            vistos = {(x["caminho"], x["quando"]) for x in meu}
            meu.extend(x for x in lst if (x["caminho"], x["quando"]) not in vistos)
            meu.sort(key=lambda x: x["quando"])
    for sec in ("erros",):
        for ch, d in (disco.get(sec) or {}).items():
            reg.setdefault(sec, {}).setdefault(ch, {}).update({k: v for k, v in d.items() if k not in reg[sec][ch]})
    for k, v in (disco.get("pulados") or {}).items():
        reg.setdefault("pulados", {}).setdefault(k, v)
    tmp = REG.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, REG)


def duracao(mp4):
    try:
        r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                           capture_output=True, text=True, timeout=60)
        return float(r.stdout.strip())
    except Exception:
        return None


def candidatos(chave, pag, cat, reg):
    ja = {x["caminho"].casefold() for ps in reg.get("postados", {}).values() for x in ps}
    ja |= {x.casefold() for x in reg.get("pulados", {})}
    nomes_ja = {Path(x).parent.name.casefold() + "/" + Path(x).name.casefold()
                for ps in reg.get("postados", {}).values() for x in [y["caminho"] for y in ps]}
    out = []
    for v in cat["videos"]:
        if v["tipo"] != "final" or not (v["no_pc"] or v["drive"]):
            continue
        yt = [p for p in v["postagens"] if p["plataforma"] == "youtube" and p["conta"] in pag.get("postados_em", [])]
        # 20/11: Página sem canal próprio (TikTok de reserva Veo) = Veo do tema que já saiu no YouTube, SÓ a versão limpa
        veo = None
        if not yt and pag.get("temas_veo") and v["projeto"] == "veo" and any(v["nome"].startswith(t) for t in pag["temas_veo"]):
            yt = [p for p in v["postagens"] if p["plataforma"] == "youtube"]
            veo = catalogo.versao_limpa(v) if yt else None
            if not veo:
                continue
        if not yt or v["caminho"].casefold() in ja:
            continue
        chave_nome = Path(v["caminho"]).parent.name.casefold() + "/" + Path(v["caminho"]).name.casefold()
        if chave_nome in nomes_ja:
            continue
        if Path(v["caminho"]).name.endswith("_ULTIMO.mp4"):  # historias: 2 versões da mesma história
            continue
        if pag.get("tags") and not veo:  # só o tema da Página (hashtag da legenda)
            import re
            tags = [t.casefold() for t in re.findall(r"#(\w+)", catalogo.legenda_reuso(v))]
            # 20/11: a 1ª hashtag é o tema (#anime ... #acao não é filme); só ela decide
            if not tags or tags[0] not in {t.casefold() for t in pag["tags"]}:
                continue
        out.append(dict(v, quando_yt=max(p["quando"] or "" for p in yt), **({"limpo": str(veo)} if veo else {})))
    # 23/11: vídeo pequeno primeiro (todo upload que falhou no dia tinha > 38 MB; todo que passou, <= 38 MB). Os grandes
    # continuam na fila, só vão para o fim. FB_GRANDE_MB muda o corte.
    corte = float(os.environ.get("FB_GRANDE_MB", "38")) * 1e6
    out.sort(key=lambda v: (v["no_pc"], v["quando_yt"]), reverse=True)
    # 24/11: no PC primeiro (não baixa do Drive lento), depois pequeno primeiro; o sort de 23/11 passava por cima do no_pc
    out.sort(key=lambda v: (not v["no_pc"], (v.get("bytes") or 0) > corte))
    return out


def hoje_na_pagina(reg, chave):
    h = datetime.now().strftime("%Y-%m-%d")
    return sum(1 for x in reg.get("postados", {}).get(chave, []) if x["quando"].startswith(h))


def postar_um(chave, pag, cfg, cat, reg, preview=False):
    from playwright.sync_api import sync_playwright
    import fb_contas, fb_reel_bs, fb_entrar_como
    cands = candidatos(chave, pag, cat, reg)
    import fb_escada
    print(f"[{pag['nome']}] {len(cands)} vídeo(s) disponíveis; hoje {hoje_na_pagina(reg, chave)}/{fb_escada.teto(chave, pag)}", flush=True)
    if preview:
        for v in cands[:5]:
            print("   ", v["caminho"][-90:], "|", catalogo.legenda_reuso(v)[:90].replace("\n", " "))
        return None
    for v in cands[:15]:
        legenda = catalogo.legenda_reuso(v)
        if not legenda:
            reg.setdefault("pulados", {})[v["caminho"]] = "sem legenda"; _gravar(reg); continue
        try:
            mp4 = catalogo.baixar(v)
        except Exception as e:  # noqa: BLE001
            print("   não baixou:", str(e)[:150]); continue
        d = duracao(mp4)
        if d is None or d > DUR_MAX:
            reg.setdefault("pulados", {})[v["caminho"]] = f"duração {d}"; _gravar(reg)
            catalogo.liberar(mp4); continue
        conta = pag["conta"]
        # 25/11 (dona: "postar pela API"): com token da Página o Reel sai pela Graph API (sem Chrome; ~2 min/post; 1º teste
        # Invento React + Assist-IA ok). Sem token / erro de token ou permissão = cai no Chrome como antes. FB_SEM_API=1 desliga.
        via, vid = "chrome", None
        ok = None
        if os.environ.get("FB_SEM_API") != "1":
            try:
                import fb_reel_api
                if fb_reel_api.token_pagina(conta, pag["asset_id"]):
                    ok, msg, vid = fb_reel_api.postar_api(conta, pag["asset_id"], str(mp4), legenda)
                    via = "api"
                    if not ok and any(x in msg for x in ("190/", "200/", "10/", "sem token", "start:", "OAuth")):
                        print(f"   API recusou ({msg[:80]}); tento pelo Chrome", flush=True)
                        ok, via = None, "chrome"
            except Exception as e:  # noqa: BLE001
                print(f"   API falhou ({str(e).splitlines()[0][:80] if str(e) else type(e).__name__}); tento pelo Chrome", flush=True)
                ok, via = None, "chrome"
        if ok is None and os.environ.get("FB_SO_API") == "1":
            catalogo.liberar(mp4)
            return False, "API indisponível e o Chrome está com a criação de Página — fica para a próxima rodada"
        if ok is not None:
            catalogo.liberar(mp4)
        else:
          porta, proc = fb_contas.abrir(conta)
          try:
            with sync_playwright() as p:
                ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
                # 20/11: troca pelo cookie i_user (instantâneo); o menu da foto fica só de reserva
                ok_troca = fb_entrar_como.entrar_como_cookie(ctx, pag.get("id"), pag["nome"])
                if not ok_troca:
                    pg = ctx.new_page(); pg.set_viewport_size({"width": 1366, "height": 900})
                    try:  # 23/11: facebook.com não abrindo em 90 s derrubava a RODADA inteira (mundosolar1995 18:2x)
                        ok_troca = fb_entrar_como.entrar_como(pg, pag["nome"])
                    except Exception as ex:  # noqa: BLE001
                        print(f"   troca de perfil falhou ({str(ex).splitlines()[0][:80]})", flush=True)
                        ok_troca = False
                    finally:
                        try:
                            pg.close()
                        except Exception:  # noqa: BLE001
                            pass
                if not ok_troca:
                    return False, "não conseguiu entrar como a Página"
                ok, msg = fb_reel_bs.postar(ctx, pag["asset_id"], pag["nome"], str(mp4), legenda, tag=f"fb_{chave}")
          finally:
            fb_contas.fechar(proc)
            catalogo.liberar(mp4)
        print(f"   {'OK' if ok else 'ERRO'} {v['caminho'][-70:]} — {msg} [{via}]", flush=True)
        if not ok:  # 20/11 escada: guarda o erro; bloqueio/restrição do Facebook = desce e segura 24 h
            reg.setdefault("erros", {}).setdefault(chave, {})[datetime.now().isoformat(timespec="seconds")] = msg[:300]
            _gravar(reg)
            import fb_escada
            if fb_escada.e_bloqueio(msg):
                fb_escada.descer(chave, msg)
        if ok:
            reg.setdefault("postados", {}).setdefault(chave, []).append(
                {"caminho": v["caminho"], "quando": datetime.now().isoformat(timespec="seconds"), "legenda": legenda[:200],
                 "duracao": round(d, 1), "via": via, **({"video_id": vid} if vid else {})})
            _gravar(reg)
            try:  # rede nova nas etapas (Drive por etapa)
                import etapas
                etapas.registrar(v["caminho"], "facebook", conta=pag["nome"])
            except Exception:
                pass
        return ok, msg
    return False, "nenhum vídeo postável"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--um", action="store_true")
    ap.add_argument("--pagina")
    ap.add_argument("--intervalo", type=int, default=300)
    ap.add_argument("--conta", help="só as Páginas desta conta (as 2 contas rodam em paralelo, cada uma na sua saída)")
    ap.add_argument("--horario", action="store_true",
                    help="rodada de hora em hora: posta só nas Páginas atrasadas pelo relógio (08-23 h) + horário nobre")
    a = ap.parse_args()
    cfg = _ler(CFG, {})
    # 21/11: trava por conta — 2 postagens na MESMA conta brigam pelo Chrome (uma fecha enquanto a outra posta ->
    # "Target page has been closed"). Se já tem outra rodando nesta(s) conta(s), sai.
    # 21/11 13h: a 1ª versão procurava processos e via o PRÓPRIO lançador do venv (pai) como "outra postagem" -> TODAS as
    # rodadas das 08:20 às 13:20 saíram sem postar. Agora é arquivo de trava por conta (pid + hora); trava de processo
    # morto ou com > 40 min é liberada sozinha.
    alvo_contas = sorted({a.conta} if a.conta else {v["conta"] for k, v in cfg["paginas"].items()
                                                    if (not a.pagina or k == a.pagina) and not v.get("pausada")})
    travas = []
    herdada = os.environ.get("FB_TRAVA_HERDADA")  # 1º Reel chamado pela criação: a trava é dela
    for c in alvo_contas:
        tv = REG.parent / f"fb_postando_{c}.lock"
        if c == herdada:
            continue
        if tv.exists():
            try:
                pid_t, quando_t = tv.read_text(encoding="utf-8").split("|")
                vivo = str(pid_t) in subprocess.run(["tasklist", "/FI", f"PID eq {pid_t}", "/NH"], capture_output=True,
                                                    text=True, errors="replace").stdout
                velha = (datetime.now() - datetime.fromisoformat(quando_t)).total_seconds() > 2400
            except Exception:
                vivo, velha = False, True
            if vivo and not velha:
                # 25/11: a trava é da CRIAÇÃO de Página (usa o Chrome da conta 20-40 min) -> posta só pela API (não abre
                # o Chrome). Antes a rodada pulava a conta e a postagem não andava (25/11 11:20). Outra POSTAGEM = sai.
                dono = subprocess.run(["powershell", "-NoProfile", "-Command",
                                       f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid_t}').CommandLine"],
                                      capture_output=True, text=True, errors="replace").stdout
                if "fb_criar_fila" in dono:
                    print(f"conta {c} criando Página (pid {pid_t}) — posto SÓ pela API, sem Chrome", flush=True)
                    os.environ["FB_SO_API"] = "1"
                    continue
                print(f"já tem postagem rodando na conta {c} (pid {pid_t}) — saio", flush=True)
                for t in travas:
                    t.unlink(missing_ok=True)
                return
        tv.write_text(f"{os.getpid()}|{datetime.now().isoformat(timespec='seconds')}", encoding="utf-8")
        travas.append(tv)
    import atexit
    atexit.register(lambda: [t.unlink(missing_ok=True) for t in travas])
    reg = _ler(REG, {})
    paginas = {k: v for k, v in cfg["paginas"].items() if (not a.pagina or k == a.pagina) and not v.get("pausada")
               and (not a.conta or v["conta"] == a.conta)}
    # página mais atrasada hoje primeiro; o teto do dia vem da escada (fb_escada.py)
    import fb_escada
    ordem = sorted(paginas, key=lambda k: hoje_na_pagina(reg, k) / max(1, fb_escada.teto(k, paginas[k])))
    agora = datetime.now()
    if a.horario and not any(hoje_na_pagina(reg, k) < fb_escada.teto(k, paginas[k])
                             and deve_postar_agora(hoje_na_pagina(reg, k), fb_escada.teto(k, paginas[k]), agora) for k in ordem):
        print(f"{agora:%H:%M} nenhuma Página com post devido nesta hora", flush=True)
        return
    cat = carregar_catalogo()
    for i, k in enumerate(ordem):
        pag = paginas[k]
        if a.preview:
            postar_um(k, pag, cfg, cat, reg, preview=True); continue
        reg = _ler(REG, {})  # outro processo (a outra conta / criar_fila) pode ter gravado
        lim, feitos = fb_escada.teto(k, pag), hoje_na_pagina(reg, k)
        if feitos >= lim:
            if not a.horario:
                print(f"[{pag['nome']}] já postou {lim} hoje" + (" (segurada pela escada)" if lim == 0 else ""))
            continue
        if a.horario and not deve_postar_agora(feitos, lim, agora):
            continue
        viral = fb_escada.segurar_viral(k)
        if viral and not a.pagina:
            print(f"[{pag['nome']}] segura: {viral}"); continue
        # 24/11 (noite, robustez.1): exceção dentro de postar_um (cofre PermissionError, Chrome sem porta, erro que escapa
        # do composer) derrubava a RODADA inteira e as Páginas seguintes da conta ficavam sem post. Agora registra e segue.
        # SystemExit (saída/proxy errado em fb_contas._conferir_saida) continua parando tudo — de propósito.
        try:
            r = postar_um(k, pag, cfg, cat, reg)
        except Exception as e:  # noqa: BLE001
            msg = f"{type(e).__name__}: {str(e).splitlines()[0][:200] if str(e) else ''}"
            print(f"   ERRO [{pag['nome']}] — {msg} (sigo para a próxima Página)", flush=True)
            try:
                reg = _ler(REG, {})
                reg.setdefault("erros", {}).setdefault(k, {})[datetime.now().isoformat(timespec="seconds")] = msg[:300]
                _gravar(reg)
            except Exception:  # noqa: BLE001
                pass
            r = (False, msg)
        if a.um and r and r[0]:
            break
        if i < len(ordem) - 1 and not a.horario:
            time.sleep(a.intervalo)


def carregar_catalogo(max_h=2):
    """20/11 12:20: sincronizar() lê o Drive (rclone) e travou a rodada 10+ min com o Drive lento. O catálogo salvo
    (catalogo_videos.json, regravado pelo TikTok/Instagram/backup) serve se tem menos de max_h; a repetição no FB é
    controlada pelo registro logs/facebook_paginas.json, não pelo catálogo."""
    try:
        if (time.time() - catalogo.CATALOGO.stat().st_mtime) < max_h * 3600:
            return json.loads(catalogo.CATALOGO.read_text(encoding="utf-8"))
    except Exception:
        pass
    return catalogo.sincronizar(salvar=False)


NOBRE = (18, 21)  # 25/11 análise de 85 Reels: 18-21 h rende 427 views/Reel, 21-24 h só 190 (pior faixa); 24/11 era 19-22, antes 21-22
INICIO, FIM = 8, 23


def deve_postar_agora(feitos, lim, agora):
    """Espalha os 'lim' Reels do dia de 08 h a 23 h e guarda 1 para o horário nobre (21-22 h):
    antes das 21 h a Página posta até lim-1 no ritmo do relógio; às 21-22 h sai o do nobre; depois, o que faltar."""
    h = agora.hour + agora.minute / 60
    if h < INICIO or h >= FIM + 1:
        return False
    if NOBRE[0] <= agora.hour <= NOBRE[1]:
        return True  # nobre: 1 por rodada (a rodada das 21 e a das 22 completam o dia)
    if agora.hour > NOBRE[1]:
        return True  # 23 h: completa o que faltou
    dia_util = max(1, lim - 1)  # antes do nobre só lim-1
    esperado = int(dia_util * (h - INICIO) / (NOBRE[0] - INICIO)) + 1
    return feitos < min(dia_util, esperado)


if __name__ == "__main__":
    main()
