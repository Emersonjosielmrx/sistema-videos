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
    tmp = REG.with_suffix(".tmp")
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
        yt = [p for p in v["postagens"] if p["plataforma"] == "youtube" and p["conta"] in pag["postados_em"]]
        if not yt or v["caminho"].casefold() in ja:
            continue
        chave_nome = Path(v["caminho"]).parent.name.casefold() + "/" + Path(v["caminho"]).name.casefold()
        if chave_nome in nomes_ja:
            continue
        if Path(v["caminho"]).name.endswith("_ULTIMO.mp4"):  # historias: 2 versões da mesma história
            continue
        if pag.get("tags"):  # só o tema da Página (hashtag da legenda)
            import re
            tags = [t.casefold() for t in re.findall(r"#(\w+)", catalogo.legenda_reuso(v))]
            # 20/11: a 1ª hashtag é o tema (#anime ... #acao não é filme); só ela decide
            if not tags or tags[0] not in {t.casefold() for t in pag["tags"]}:
                continue
        out.append(dict(v, quando_yt=max(p["quando"] or "" for p in yt)))
    out.sort(key=lambda v: (v["no_pc"], v["quando_yt"]), reverse=True)
    return out


def hoje_na_pagina(reg, chave):
    h = datetime.now().strftime("%Y-%m-%d")
    return sum(1 for x in reg.get("postados", {}).get(chave, []) if x["quando"].startswith(h))


def postar_um(chave, pag, cfg, cat, reg, preview=False):
    from playwright.sync_api import sync_playwright
    import fb_contas, fb_reel_bs, fb_entrar_como
    cands = candidatos(chave, pag, cat, reg)
    print(f"[{pag['nome']}] {len(cands)} vídeo(s) disponíveis; hoje {hoje_na_pagina(reg, chave)}/{pag.get('por_dia', 3)}", flush=True)
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
        porta, proc = fb_contas.abrir(conta)
        try:
            with sync_playwright() as p:
                ctx = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}").contexts[0]
                pg = ctx.new_page(); pg.set_viewport_size({"width": 1366, "height": 900})
                ok_troca = fb_entrar_como.entrar_como(pg, pag["nome"]); pg.close()
                if not ok_troca:
                    return False, "não conseguiu entrar como a Página"
                ok, msg = fb_reel_bs.postar(ctx, pag["asset_id"], pag["nome"], str(mp4), legenda, tag=f"fb_{chave}")
        finally:
            fb_contas.fechar(proc)
            catalogo.liberar(mp4)
        print(f"   {'OK' if ok else 'ERRO'} {v['caminho'][-70:]} — {msg}", flush=True)
        if ok:
            reg.setdefault("postados", {}).setdefault(chave, []).append(
                {"caminho": v["caminho"], "quando": datetime.now().isoformat(timespec="seconds"), "legenda": legenda[:200],
                 "duracao": round(d, 1)})
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
    a = ap.parse_args()
    cfg = _ler(CFG, {})
    reg = _ler(REG, {})
    cat = catalogo.sincronizar(salvar=False)
    paginas = {k: v for k, v in cfg["paginas"].items() if (not a.pagina or k == a.pagina) and not v.get("pausada")}
    # página mais atrasada hoje primeiro
    ordem = sorted(paginas, key=lambda k: hoje_na_pagina(reg, k) / max(1, paginas[k].get("por_dia", 3)))
    for i, k in enumerate(ordem):
        pag = paginas[k]
        if a.preview:
            postar_um(k, pag, cfg, cat, reg, preview=True); continue
        if hoje_na_pagina(reg, k) >= pag.get("por_dia", 3):
            print(f"[{pag['nome']}] já postou {pag.get('por_dia', 3)} hoje"); continue
        r = postar_um(k, pag, cfg, cat, reg)
        if a.um and r and r[0]:
            break
        if i < len(ordem) - 1:
            time.sleep(a.intervalo)


if __name__ == "__main__":
    main()
