"""conferir_logins.py — conferência PADRÃO depois de qualquer rodada de login, em qualquer máquina (x200ma, acer, pc2,
desktop). Dona 25/10: "tem que ser um script de conferência padrão depois de logins".

Ordem de cada máquina: 1) logar Google/YouTube  2) logar TikTok e Instagram  3) rodar ESTE script.
Prova por rede (a resposta da própria rede, não cookie nem URL):
  google    -> myaccount.google.com abre sem cair na tela de login
  youtube   -> studio.youtube.com abre um /channel/UC...
  tiktok    -> /passport/web/account/info/ devolve o @
  instagram -> web_form_data devolve o @
Só muda a marca em netbooks_logins.json com resposta certa (logado ou deslogado); sem resposta fica como está.
Deslogado no TikTok/Instagram volta pra fila de login. Print de cada conferência em logs/tiktok_tela/.
Resultado: logs/conferencia_<maquina>.json + linha no maquina_remota.log.

    python bin\\netbooks\\conferir_logins.py x200ma                 # todas as redes marcadas nessa máquina
    python bin\\netbooks\\conferir_logins.py acer instagram         # só uma rede (google|youtube|tiktok|instagram)
    python bin\\netbooks\\conferir_logins.py x200ma acer instagram  # várias máquinas em paralelo
"""
import json
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import maquina_remota as mr  # noqa: E402
import tiktok_notebooks as tn  # noqa: E402

REDES = ("google", "youtube", "tiktok", "instagram")


def _google(ctx, pg):
    pg.goto("https://myaccount.google.com/", wait_until="domcontentloaded", timeout=120000)
    pg.wait_for_timeout(6000)
    if "accounts.google.com" in pg.url:
        return ""
    return "logado" if "myaccount.google.com" in pg.url else None


def _youtube(ctx, pg):
    pg.goto("https://studio.youtube.com/", wait_until="domcontentloaded", timeout=120000)
    for _ in range(6):
        pg.wait_for_timeout(5000)
        m = re.search(r"/channel/(UC[\w-]{20,})", pg.url)
        if m:
            return m.group(1)
        if "accounts.google.com" in pg.url:
            return ""
    return None


def _tiktok(ctx, pg, perfil, nome):
    return tn._confirmar(ctx, pg, perfil, nome)


def _instagram(ctx, pg):
    import instagram_local as il
    pg.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=120000)
    for _ in range(4):
        pg.wait_for_timeout(6000)
        u = il._usuario_logado(pg)
        if u:
            return "@" + u
    if pg.locator("input[name=username], input[name=email]").count():
        return ""
    # 25/10 Acer: "Confirme que você é humano para usar seu perfil" — sessão bloqueada até a dona resolver na tela
    if "você é humano" in il._texto(pg).lower() or "you're human" in il._texto(pg).lower():
        mr.log(f"conferir instagram: verificação humana na tela (a dona resolve) — {pg.url[:80]}")
        return ""
    return None


def _marcar(perfil, nome, rede, logado):
    if rede == "tiktok" and not logado:
        tn._desligar(perfil, nome)
        return
    lg = mr._logins()
    lg.setdefault(perfil, {}).setdefault(nome, {})[rede] = bool(logado)
    mr._politica().gravar_json(mr.LOGINS, lg)


def _um(perfil, nome, redes):
    from playwright.sync_api import sync_playwright
    r, res = mr.Remoto(nome), {}
    try:
        porta = r.abrir(perfil, sem_espera=True)
        with sync_playwright() as p:
            try:
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=300000)
            except Exception:  # noqa: BLE001 — Acer lento: mais uma vez
                time.sleep(20)
                br = p.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}", timeout=300000)
            ctx = br.contexts[0]
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            for rede in redes:
                try:
                    res[rede] = _tiktok(ctx, pg, perfil, nome) if rede == "tiktok" else \
                        {"google": _google, "youtube": _youtube, "instagram": _instagram}[rede](ctx, pg)
                except Exception as e:  # noqa: BLE001
                    res[rede] = None
                    mr.log(f"conferir {rede} {perfil} no {nome}: erro {type(e).__name__}: {str(e)[:80]}")
                if rede != "tiktok":  # o _confirmar do TikTok já tira o print dele
                    tn._passo(pg, perfil, nome, f"conferir_{rede}")
    finally:
        r.fechar()
    return res


def conferir(nome, so=()):
    """Confere cada rede marcada como logada nessa máquina. Devolve {perfil: {rede: resultado}}."""
    saida, arq = {}, mr.ROOT / "logs" / f"conferencia_{nome}.json"
    for perfil, maqs in sorted(mr._logins().items()):
        v = (maqs or {}).get(nome)
        if not isinstance(v, dict):
            continue
        redes = [x for x in REDES if v.get(x) and (not so or x in so)]
        if not redes:
            continue
        for _ in range(60):  # espera a vez (Veo, login, telão) até ~30 min
            # 04/11: a conferência (15 min por perfil, horas seguidas) tomava x200ma/acer entre uma tentativa e outra do
            # Veo das SOLARES (prioridade 1 da dona) — o reel da Globo ficou sem máquina das 02:09 às 05:45. Solar
            # gerando = espera (rotina cede pra cliente).
            if tn.Remoto_livre(nome) and not _solar_gerando():
                break
            time.sleep(30)
        else:
            mr.log(f"conferir logins: {nome} ocupado há 30 min, parei")
            break
        vez = f"conferir logins {perfil}"
        mr.ocupar(nome, vez, 15)
        try:
            res = _um(perfil, nome, redes)
        except Exception as e:  # noqa: BLE001
            res = {x: None for x in redes}
            mr.log(f"conferir logins {perfil} no {nome}: erro {type(e).__name__}: {str(e)[:80]}")
        finally:
            mr.liberar(nome, quem=vez)
        for rede, ok in res.items():
            if ok is not None:
                _marcar(perfil, nome, rede, bool(ok))
            mr.log(f"conferir {rede} {perfil} no {nome}: "
                   f"{'sem resposta (fica como está)' if ok is None else ok or 'NÃO está logado (volta pra fila)'}")
        saida[perfil] = {"em": datetime.now().isoformat(timespec="minutes"), **res}
        arq.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    return saida


def resumo(nome, saida):
    linhas = [f"== {nome}"]
    for rede in REDES:
        vals = [(p, r[rede]) for p, r in saida.items() if rede in r]
        if not vals:
            continue
        ok = [p for p, x in vals if x]
        fora = [p for p, x in vals if x == ""]
        nada = [p for p, x in vals if x is None]
        linhas.append(f"{rede}: {len(ok)} logadas de {len(vals)}"
                      + (f" | DESLOGADAS: {', '.join(fora)}" if fora else "")
                      + (f" | sem resposta: {', '.join(nada)}" if nada else ""))
    return "\n".join(linhas)


def _solar_gerando():
    """Algum reel das solares (MS/Advance/Globo) sendo gerado agora no PC1? (eles usam o Veo dos notebooks)"""
    try:
        import psutil
    except ImportError:
        return False
    for p in psutil.process_iter(["cmdline"]):
        try:
            c = " ".join(p.info["cmdline"] or [])
        except (psutil.Error, TypeError):
            continue
        if "ms-energy" in c and any(s in c for s in ("reel_advance", "reel_globo", "gerar_short_veo", "estoque_reels")):
            return True
    return False


def main(a):
    maqs = [n for n in mr.MAQUINAS if n in a] or ["x200ma", "acer"]
    so = tuple(x for x in REDES if x in a)
    resultados = {}
    ts = [threading.Thread(target=lambda n=n: resultados.__setitem__(n, conferir(n, so))) for n in maqs]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    for n in maqs:
        print(resumo(n, resultados.get(n) or {}))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main(sys.argv[1:])
