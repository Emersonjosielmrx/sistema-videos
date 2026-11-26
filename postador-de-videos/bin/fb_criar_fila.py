"""Cria a próxima Página da fila (config/fb_fila_paginas.json) com o PROCEDIMENTO COMPLETO (dona 20/11/2026: "vai
fazendo uma a cada X horas como fazemos no Instagram; o script já tem que fazer o procedimento completo: capa, perfil,
bio, descrição, primeiro post"):

  1. arte (foto 1024 + capa 1640x624) por tema  -> fb_arte_pagina.py
  2. cria a Página no perfil pessoal da conta (nome, categoria, bio) -> fb_criar_pagina.py
  3. acha o id do perfil da Página e o asset_id do Business Suite (delegate_page_id)
  4. entra como a Página e põe foto e capa -> fb_foto_perfil.py + fb_foto_capa.py (confere pelo texto de saída)
  5. grava a Página em config/facebook_paginas.json (entra na postagem, escada e medidor)
  6. 1º Reel -> postar_facebook_paginas.py --pagina <chave> --um

Ritmo/segurança: revezam as 2 contas (emersonjosiel02 = perfil novo, Webshare rnprmtfo-58; msenergypara = perfil de
10+ anos, casa); cada conta no máximo 'max_dia_por_conta' por dia e 'intervalo_h' entre criações; aviso do Facebook de
limite/restrição/checkpoint = PARA a conta por 48 h. Estado em logs/fb_fila_estado.json. Etapa que falhou fica
registrada e a próxima rodada continua dela (não cria a Página de novo).

    python fb_criar_fila.py            # tarefa FacebookCriarPaginas (a cada 3 h)
    python fb_criar_fila.py --ver      # mostra a fila
    python fb_criar_fila.py --chave cenareact   # força uma
"""
import argparse, collections, json, os, re, subprocess, sys, time
from datetime import datetime, timedelta
from pathlib import Path

BIN = Path(__file__).resolve().parent
sys.path.insert(0, str(BIN))
FILA = BIN.parent / "config" / "fb_fila_paginas.json"
CFG = BIN.parent / "config" / "facebook_paginas.json"
EST = BIN.parent / "logs" / "fb_fila_estado.json"
LOG = BIN.parent / "logs" / "fb_criar_fila.log"
ART = BIN.parent / "assets" / "facebook"
PY = sys.executable
BLOQ = ("rápido demais", "rapido demais", "too fast", "temporariamente bloque", "restri", "checkpoint", "confirme sua identidade",
        "limite", "suspens")


def _ler(p, padrao):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return padrao


def _gravar(p, d):
    if Path(p) == EST:  # marca de "ocupada" é só da rodada
        d = json.loads(json.dumps(d))
        for c in d.get("contas", {}).values():
            c.pop("_ocupada", None)
        # 26/11: o criador relia o estado no começo e regravava tudo no fim -> apagava o repouso de 48 h gravado por fora
        # (emersonjosiel02 voltou a 25/11 10:45 e criou Página às 02:45 em repouso). Nunca DIMINUI parada_ate do disco.
        try:
            disco = json.loads(Path(p).read_text(encoding="utf-8")).get("contas", {})
            for nome, c in d.get("contas", {}).items():
                pd = (disco.get(nome) or {}).get("parada_ate")
                if pd and (not c.get("parada_ate") or c["parada_ate"] < pd):
                    c["parada_ate"] = pd
                    c["motivo"] = (disco.get(nome) or {}).get("motivo", c.get("motivo"))
        except (OSError, ValueError):
            pass
    tmp = Path(p).with_suffix(".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")
    print(msg, flush=True)


def rodar(scr, *args, timeout=1500):
    r = subprocess.run([PY, "-u", str(BIN / scr), *map(str, args)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(BIN), timeout=timeout, env=dict(os.environ, PYTHONUTF8="1"))
    out = (r.stdout or "") + (r.stderr or "")
    return r.returncode, out


def _bloqueio(texto):
    t = (texto or "").casefold()
    return next((b for b in BLOQ if b in t), None)


def achar_pagina(conta, nome):
    """Depois de criar: url do perfil da Página + asset_id (delegate_page_id). Usa a lista de Páginas da conta."""
    from playwright.sync_api import sync_playwright
    import fb_contas
    porta, proc = fb_contas.abrir(conta)
    try:
        with sync_playwright() as p:
            ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
            url = None
            for tent in range(4):  # conta nova demora a listar a Página recém-criada
                url = next((h for t, h in fb_contas.listar_paginas(ctx) if t.strip().casefold() == nome.casefold()), None)
                if url:
                    break
                # 2ª via: a tela "Páginas que você gerencia" / allactivity; e a aba de criação ainda aberta
                pv = ctx.new_page()
                try:
                    pv.goto("https://www.facebook.com/pages/?category=your_pages", wait_until="domcontentloaded", timeout=60000)
                    time.sleep(8)
                    for a in pv.query_selector_all("a[href*='/profile.php?id='], a[href*='facebook.com/']"):
                        txt = (a.inner_text() or "").strip().split("\n")[0]
                        if txt.casefold() == nome.casefold():
                            url = (a.get_attribute("href") or "").split("?__")[0].split("&")[0]
                            break
                finally:
                    pv.close()
                if url:
                    break
                time.sleep(20)
            if not url:
                return None, None, None
            pg = ctx.new_page()
            pg.goto(url, wait_until="domcontentloaded", timeout=120000); time.sleep(10)
            h = pg.content()
            pid = re.search(r"profile\.php\?id=(\d+)", url)
            pid = pid.group(1) if pid else (re.search(r'"userID"\s*:\s*"(\d{10,20})"', h) or [None, None])[1]
            ids = collections.Counter(re.findall(r'"delegate_page_id"\s*:\s*"?(\d{6,20})', h))
            pg.close()
            return url, pid, (ids.most_common(1)[0][0] if ids else None)
    finally:
        fb_contas.fechar(proc)


def contas_livres(fila, est):
    """Contas que podem criar AGORA (sem intervalo/limite/bloqueio/saturação)."""
    agora = datetime.now()
    hoje = agora.strftime("%Y-%m-%d")
    out = []
    for conta, maxd in fila["max_dia_por_conta"].items():
        c = est.get("contas", {}).get(conta, {})
        if c.get("parada_ate", "") > agora.isoformat() or c.get("saturado"):
            continue
        feitas = sum(1 for x in est.get("paginas", {}).values() if x.get("conta") == conta and x.get("criada", "")[:10] == hoje)
        if feitas >= maxd:
            continue
        ult = c.get("ultima")
        inter = (fila.get("intervalo_h_por_conta") or {}).get(conta, fila["intervalo_h"])
        if ult and datetime.fromisoformat(ult) > agora - timedelta(hours=inter):
            continue
        out.append(conta)
    # conta com página pela metade pode continuar mesmo fora do intervalo
    for conta in fila["max_dia_por_conta"]:
        if conta in out:
            continue
        if any(v.get("conta") == conta and v.get("etapa") not in (None, "pronta")
               for v in est.get("paginas", {}).values()):
            if not est.get("contas", {}).get(conta, {}).get("parada_ate", "") > agora.isoformat():
                out.append(conta)
    return out


def proxima(fila, est, conta_forcada=None, chave=None):
    """1ª pendente da conta que está liberada agora (respeita intervalo, máximo do dia e bloqueio).
    conta_forcada = só olha essa conta."""
    agora = datetime.now()
    hoje = agora.strftime("%Y-%m-%d")
    livres = []
    for conta, maxd in fila["max_dia_por_conta"].items():
        if conta_forcada and conta != conta_forcada:
            continue
        c = est.setdefault("contas", {}).setdefault(conta, {})
        if c.get("parada_ate", "") > agora.isoformat() or c.get("_ocupada"):
            continue
        if c.get("saturado"):  # fb_saturacao.py: Reels novos rendendo < 40% da 1ª semana -> não vale mais Página aqui
            continue
        feitas_hoje = sum(1 for x in est.get("paginas", {}).values() if x.get("conta") == conta and x.get("criada", "")[:10] == hoje)
        if feitas_hoje >= maxd:
            continue
        ult = c.get("ultima")
        inter = (fila.get("intervalo_h_por_conta") or {}).get(conta, fila["intervalo_h"])
        if ult and datetime.fromisoformat(ult) > agora - timedelta(hours=inter):
            continue
        livres.append((ult or "", conta))
    livres.sort()  # a conta que criou há mais tempo vai primeiro (revezam)
    paradas = {c for c, v in est.get("contas", {}).items() if v.get("parada_ate", "") > agora.isoformat()}
    if chave:
        return next((i for i in fila["fila"] if i["chave"] == chave), None)
    livres_c = {c for _, c in livres} | ({conta_forcada} if conta_forcada else set())
    # 1º termina a que ficou pela metade (já criada; não conta como criação nova), se a conta não está parada
    for item in fila["fila"]:
        st = est.get("paginas", {}).get(item["chave"], {})
        if st.get("etapa") and st["etapa"] != "pronta" and item["conta"] not in paradas \
                and (not conta_forcada or item["conta"] == conta_forcada):
            return item
    for _, conta in livres:
        for item in fila["fila"]:
            if item["conta"] == conta and not est.get("paginas", {}).get(item["chave"], {}).get("etapa"):
                return item
    return None


def fazer(item, fila, est):
    ch, conta, nome = item["chave"], item["conta"], item["nome"]
    st = est.setdefault("paginas", {}).setdefault(ch, {"conta": conta, "nome": nome})
    salvar = lambda: _gravar(EST, est)  # noqa: E731
    perfil = fila["perfil_pessoal"][conta]
    foto, capa = ART / f"{ch}_foto.png", ART / f"{ch}_capa.png"
    log(f"== {nome} ({ch}) na conta {conta} — etapa atual: {st.get('etapa') or 'nova'}")

    if not (foto.exists() and capa.exists()):
        palavras = nome.split()
        rc, out = rodar("fb_arte_pagina.py", ch, nome, item["bio"].split(".")[0][:60], "Reels novos todo dia", item["arte"])
        if rc:
            log(f"   arte falhou: {out[-300:]}"); return False
    if not st.get("criada"):
        # já existe na conta? (rodada anterior criou e caiu antes de gravar)
        url, pid, asset = achar_pagina(conta, nome)
        if not url:
            rc, out = rodar("fb_criar_pagina.py", conta, perfil, nome, item["categoria"], item["bio"], ch)
            b = _bloqueio(out)
            if b:
                parar(est, conta, f"aviso ao criar ({b}): {out[-200:]}"); return False
            url, pid, asset = achar_pagina(conta, nome)
            if not url:
                log(f"   não achei a Página depois de criar: {out[-400:]}"); st["erro"] = "criação"; salvar(); return False
        st.update(criada=datetime.now().isoformat(timespec="seconds"), url=url, id=pid, asset_id=asset, etapa="criada")
        est["contas"][conta]["ultima"] = st["criada"]
        salvar()
        log(f"   criada: {url} id={pid} asset={asset}")
    if not st.get("asset_id"):
        url, pid, asset = achar_pagina(conta, nome)
        st.update(asset_id=asset, id=st.get("id") or pid); salvar()
        if not asset:
            log("   sem asset_id ainda (tenta na próxima rodada)"); return False
    if st.get("etapa") == "criada":
        rc, out = rodar("fb_entrar_como.py", conta, nome)
        rc, out = rodar("fb_foto_perfil.py", conta, st["url"], foto, ch)
        if "foto salva" not in out:
            log(f"   foto falhou: {out[-250:]}"); return False
        st["etapa"] = "foto"; salvar()
    if st.get("etapa") == "foto":
        rc, out = rodar("fb_foto_capa.py", conta, st["url"], foto, capa, ch)
        if "capa: salva" not in out:
            log(f"   capa falhou: {out[-250:]}"); return False
        st["etapa"] = "capa"; salvar()
    if st.get("etapa") == "capa":
        cfg = _ler(CFG, {})
        pag = {"conta": conta, "id": st["id"], "asset_id": st["asset_id"], "nome": nome,
               "_criada": f"{st['criada'][:16]} fb_criar_fila (TikTok {item['tiktok']})",
               "postados_em": item.get("postados_em", []), "tags": item.get("tags", []), "por_dia": 3}
        if item.get("temas_veo"):
            pag["temas_veo"] = item["temas_veo"]
        cfg["paginas"][ch] = pag
        _gravar(CFG, cfg)
        st["etapa"] = "config"; salvar()
    if st.get("etapa") == "config":
        # 23/11: a Página já existe com foto/capa/config; se a postagem normal já pôs reel nela, ou o 1º reel falhou 2x,
        # ela fica PRONTA (a rodada normal posta). Antes ficava em "config" para sempre e travava a fila da conta inteira
        # (Cartucho React 22/11 23:45 -> 23/11: 26 Páginas da emersonjosiel02 paradas atrás dela).
        reg = _ler(BIN.parent / "logs" / "facebook_paginas.json", {})
        if (reg.get("postados") or {}).get(ch) or st.get("falhas_1reel", 0) >= 2:
            st["etapa"] = "pronta"; st["pronta"] = datetime.now().isoformat(timespec="seconds"); st.pop("erro", None)
            st["obs"] = "pronta sem o 1º reel da criação (a rodada normal posta)"; salvar()
            log(f"   PRONTA (reel fica para a rodada normal): {nome}")
            return True
        rc, out = rodar("postar_facebook_paginas.py", "--pagina", ch, "--um", timeout=2400)
        ok = " OK " in out
        log("   1º reel: " + next((l for l in out.splitlines() if " OK " in l or " ERRO " in l), out.strip()[-200:])[-200:])
        b = _bloqueio(out) if not ok else None
        if b:
            parar(est, conta, f"aviso no 1º reel ({b})"); return False
        if not ok:
            st["erro"] = "1º reel"; st["falhas_1reel"] = st.get("falhas_1reel", 0) + 1; salvar()
            if "nenhum vídeo postável" in out:  # sem estoque: a Página fica pronta, a escada posta quando houver
                st["etapa"] = "pronta"; st["sem_estoque"] = True; salvar()
            return False
        st["etapa"] = "pronta"; st["pronta"] = datetime.now().isoformat(timespec="seconds"); st.pop("erro", None); salvar()
        log(f"   PRONTA: {nome}")
        _token_nova(conta)
    return True


def _token_nova(conta):
    """25/11: Página nova já ganha token da API (o token de usuário salvo cobre 'Páginas atuais e futuras')."""
    try:
        rc, out = rodar("fb_token_assistido.py", "trocar", conta, timeout=300)
        log("   token API: " + next((l for l in out.splitlines() if "OK:" in l or "FALTAM" in l), out.strip()[-120:])[:160])
    except Exception as e:  # noqa: BLE001
        log(f"   token API não atualizou: {e}")


def parar(est, conta, motivo):
    est.setdefault("contas", {}).setdefault(conta, {})["parada_ate"] = (datetime.now() + timedelta(hours=48)).isoformat(timespec="seconds")
    est["contas"][conta]["motivo"] = motivo
    _gravar(EST, est)
    log(f"   PAROU a conta {conta} por 48 h: {motivo}")
    try:
        sys.path.insert(0, r"D:\video-fila")
        import avisos
        avisos.enviar(f"Facebook: criação de Páginas parada 48 h na conta {conta} — {motivo[:150]}", "facebook_paginas",
                      importante=True)
    except Exception:
        pass


def ver(fila, est):
    for item in fila["fila"]:
        st = est.get("paginas", {}).get(item["chave"], {})
        print(f"{item['nome']:30} {item['conta']:16} {st.get('etapa') or 'pendente':9} {st.get('erro') or ''}")
    print({c: v for c, v in est.get("contas", {}).items()})


def main():
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", action="store_true")
    ap.add_argument("--chave")
    ap.add_argument("--conta", help="só cria nesta conta")
    ap.add_argument("--todas", action="store_true", help="dispara 1 processo por conta LIVRE, em paralelo (cada uma no seu IP)")
    a = ap.parse_args()
    fila, est = _ler(FILA, {}), _ler(EST, {})
    if a.ver:
        return ver(fila, est)
    if a.todas:
        livres = contas_livres(fila, est)
        if not livres:
            log("--todas: nenhuma conta livre agora"); return
        log(f"--todas: disparando {len(livres)} conta(s) em paralelo: {livres}")
        procs = []
        for c in livres:
            p = subprocess.Popen([PY, "-u", str(BIN / "fb_criar_fila.py"), "--conta", c], cwd=str(BIN),
                                 creationflags=0x08000000, env=dict(os.environ, PYTHONUTF8="1"),
                                 stdout=open(BIN.parent / "logs" / f"fb_criar_{c}.log", "a", encoding="utf-8"),
                                 stderr=subprocess.STDOUT)
            procs.append(p); time.sleep(3)
        for p in procs:
            p.wait()
        return
    # não roda junto com a rodada de postagem (os dois trocariam o perfil ativo no mesmo Chrome)
    ocup = subprocess.run(["powershell", "-NoProfile", "-Command",
                           "(Get-CimInstance Win32_Process -Filter \"name='python.exe' or name='pythonw.exe'\" | ? { $_.CommandLine -match "
                           "'postar_facebook_paginas|postar_ms_energy.*fb|fb_medir' -and $_.CommandLine -notmatch 'fb_criar_fila' } | "
                           "% { $_.CommandLine }) -join '||'"],
                          capture_output=True, text=True).stdout.strip()
    # conta ocupada = tem rodada de postagem dela agora (a outra conta pode criar: é outro Chrome e outra saída)
    # 23/11: olha CADA processo (antes 1 linha juntava todos: um "--conta" em qualquer processo liberava/travava errado,
    # e qualquer fb_medir travava as 2 contas -> a criação quase nunca tinha vez). Só trava tudo um processo sem conta.
    ocupadas = set()
    for linha in (x for x in ocup.split("||") if x.strip()):
        donos = {c for c in fila["max_dia_por_conta"] if c in linha}
        if "postar_ms_energy" in linha:
            donos.add("msenergypara")
        if not donos and ("postar_facebook_paginas" in linha or "fb_medir" in linha) and "--pagina" not in linha:
            donos = set(fila["max_dia_por_conta"])
        ocupadas |= donos
    if ocupadas and not a.chave:
        for c in ocupadas:  # tira a conta ocupada da vez sem mexer no estado gravado
            est.setdefault("contas", {}).setdefault(c, {})["_ocupada"] = True
    item = proxima(fila, est, conta_forcada=a.conta, chave=a.chave)
    if item and est.get("contas", {}).get(item["conta"], {}).get("_ocupada"):
        log(f"conta {item['conta']} postando agora — fica pra próxima"); return
    if not item:
        log("nada a fazer agora (intervalo/limite do dia/conta parada/fila vazia)"); return
    # 1 Chrome da conta aberto o procedimento inteiro (abrir/fechar a cada etapa travava o perfil: ECONNREFUSED);
    # as etapas acham a porta aberta e não fecham. Fecha no fim.
    # 21/11: mesma trava por conta da postagem (logs/fb_postando_<conta>.lock) — criação e rodada de postagem na MESMA
    # conta brigavam pelo Chrome (uma fechava o da outra). O 1º Reel da criação roda com FB_TRAVA_HERDADA e passa.
    trava = BIN.parent / "logs" / f"fb_postando_{item['conta']}.lock"
    if trava.exists():
        try:
            pid_t, quando_t = trava.read_text(encoding="utf-8").split("|")
            vivo = str(pid_t) in subprocess.run(["tasklist", "/FI", f"PID eq {pid_t}", "/NH"], capture_output=True,
                                                text=True, errors="replace").stdout
            if vivo and (datetime.now() - datetime.fromisoformat(quando_t)).total_seconds() < 2400:
                log(f"conta {item['conta']} postando agora (pid {pid_t}) — criação fica pra próxima"); return
        except Exception:
            pass
    trava.write_text(f"{os.getpid()}|{datetime.now().isoformat(timespec='seconds')}", encoding="utf-8")
    os.environ["FB_TRAVA_HERDADA"] = item["conta"]
    import fb_contas
    _, proc = fb_contas.abrir(item["conta"])
    try:
        fazer(item, fila, est)
    except Exception as e:  # noqa: BLE001
        log(f"   ERRO {item['chave']}: {str(e)[:300]}")
    finally:
        fb_contas.fechar(proc)
        trava.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
