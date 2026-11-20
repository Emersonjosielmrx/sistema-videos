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
            url = next((h for t, h in fb_contas.listar_paginas(ctx) if t.strip().casefold() == nome.casefold()), None)
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


def proxima(fila, est, conta_forcada=None, chave=None):
    """1ª pendente da conta que está liberada agora (respeita intervalo, máximo do dia e bloqueio)."""
    agora = datetime.now()
    hoje = agora.strftime("%Y-%m-%d")
    livres = []
    for conta, maxd in fila["max_dia_por_conta"].items():
        c = est.setdefault("contas", {}).setdefault(conta, {})
        if c.get("parada_ate", "") > agora.isoformat() or c.get("_ocupada"):
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
    # 1º termina a que ficou pela metade (já criada; não conta como criação nova), se a conta não está parada
    for item in fila["fila"]:
        st = est.get("paginas", {}).get(item["chave"], {})
        if st.get("etapa") and st["etapa"] != "pronta" and item["conta"] not in paradas:
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
        rc, out = rodar("postar_facebook_paginas.py", "--pagina", ch, "--um", timeout=2400)
        ok = " OK " in out
        log("   1º reel: " + next((l for l in out.splitlines() if " OK " in l or " ERRO " in l), out.strip()[-200:])[-200:])
        b = _bloqueio(out) if not ok else None
        if b:
            parar(est, conta, f"aviso no 1º reel ({b})"); return False
        if not ok:
            st["erro"] = "1º reel"; salvar()
            if "nenhum vídeo postável" in out:  # sem estoque: a Página fica pronta, a escada posta quando houver
                st["etapa"] = "pronta"; st["sem_estoque"] = True; salvar()
            return False
        st["etapa"] = "pronta"; st["pronta"] = datetime.now().isoformat(timespec="seconds"); st.pop("erro", None); salvar()
        log(f"   PRONTA: {nome}")
    return True


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
    a = ap.parse_args()
    fila, est = _ler(FILA, {}), _ler(EST, {})
    if a.ver:
        return ver(fila, est)
    # não roda junto com a rodada de postagem (os dois trocariam o perfil ativo no mesmo Chrome)
    ocup = subprocess.run(["powershell", "-NoProfile", "-Command",
                           "(Get-CimInstance Win32_Process -Filter \"name='python.exe' or name='pythonw.exe'\" | ? { $_.CommandLine -match "
                           "'postar_facebook_paginas|postar_ms_energy.*fb|fb_medir' -and $_.CommandLine -notmatch 'fb_criar_fila' } | "
                           "% { $_.CommandLine }) -join '||'"],
                          capture_output=True, text=True).stdout.strip()
    # conta ocupada = tem rodada de postagem dela agora (a outra conta pode criar: é outro Chrome e outra saída)
    ocupadas = {c for c in fila["max_dia_por_conta"] if c in ocup or ("postar_facebook_paginas" in ocup and "--conta" not in ocup)
                or (c == "msenergypara" and "postar_ms_energy" in ocup) or "fb_medir" in ocup}
    if ocupadas and not a.chave:
        for c in ocupadas:  # tira a conta ocupada da vez sem mexer no estado gravado
            est.setdefault("contas", {}).setdefault(c, {})["_ocupada"] = True
    item = proxima(fila, est, chave=a.chave)
    if item and est.get("contas", {}).get(item["conta"], {}).get("_ocupada"):
        log(f"conta {item['conta']} postando agora — fica pra próxima"); return
    if not item:
        log("nada a fazer agora (intervalo/limite do dia/conta parada/fila vazia)"); return
    # 1 Chrome da conta aberto o procedimento inteiro (abrir/fechar a cada etapa travava o perfil: ECONNREFUSED);
    # as etapas acham a porta aberta e não fecham. Fecha no fim.
    import fb_contas
    _, proc = fb_contas.abrir(item["conta"])
    try:
        fazer(item, fila, est)
    except Exception as e:  # noqa: BLE001
        log(f"   ERRO {item['chave']}: {str(e)[:300]}")
    finally:
        fb_contas.fechar(proc)


if __name__ == "__main__":
    main()
